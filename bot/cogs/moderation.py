from discord.ext import commands
import discord, config, asyncio
from utils import snowflake
from utils import clean
from utils import experiments, current_experiments, decorators, text_handler, permissions
from datetime import datetime
from utils.timestamp import timestamp

class Moderation(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	@experiments.has_experiment(current_experiments.MODERATION)
	@permissions.has_permission(permissions.MODERATOR)
	async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason specified."):
		if member.id == ctx.author.id:
			await text_handler.send(ctx, "moderation_ban_failure_self_ban")
			return
		if member.id == self.bot.user.id:
			# self_kick(ctx)
			await ctx.guild.leave()
			return
		await self.add_infraction(ctx, "ban", member, reason)

	@commands.command()
	@experiments.has_experiment(current_experiments.MODERATION)
	@permissions.has_permission(permissions.MODERATOR)
	async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason specified."):
		if member.id == ctx.author.id:
			await text_handler.send(ctx, "moderation_kick_failure_self_kick")
			return
		if member.id == self.bot.user.id:
			# self_kick(ctx)
			await ctx.guild.leave()
			return
		await self.add_infraction(ctx, "kick", member, reason)


	async def self_kick(self, ctx):
		database = self.bot.client[config.database_name]
		servers = database["servers"]
		server_query = servers.find(
			{
				"id": ctx.guild.id
			}, {"_id": 0}
		).limit(1)
		for server in server_query:
			def message_check(message):
				return message.author.id == ctx.author.id and message.channel.id == ctx.channel.id and message.content.lower() in [text_handler.translate(server["language"], "yes"), text_handler.translate(server["language"], "no"), text_handler.translate(server["language"], "moderation_ban_or_kick_bot_stay")]
			await text_handler.send(ctx, "moderation_ban_or_kick_bot")
			try:
				m3 = await self.bot.wait_for("message", check=message_check, timeout=20.0)
			except asyncio.TimeoutError:
				await text_handler.send(ctx, "moderation_ban_or_kick_bot_timeout")
			if text_handler.translate(server["language"], "yes") in m3.content.lower():
				await text_handler.send(ctx, "moderation_ban_or_kick_bot_yes")
			elif m3.content.lower() == text_handler.translate(server["language"], "moderation_ban_or_kick_bot_stay"):
				await text_handler.send(ctx, "moderation_ban_or_kick_bot_selected_stay")
				return
			else:
				await text_handler.send(ctx, "moderation_ban_or_kick_bot_no")

	@commands.command()
	@experiments.has_experiment(current_experiments.MODERATION)
	@permissions.has_permission(permissions.MODERATOR)
	async def pardon(self, ctx, inf_id: int, *, reason: str):
		database = self.bot.client[config.database_name]
		infractions = database["infractions"]
		servers = database["servers"]
		query = servers.find({"id": ctx.guild.id}, {"_id": 0}).limit(1)
		if query.count() == 0:
			await ctx.send("Oh no! This server has not been set up yet, but don't fret, run `<.setup` and we'll get this server all ready in no time!")
			return
		infractions_query = infractions.find(
			{
				"guild_id": ctx.guild.id,
				"infraction_id": inf_id
			}, { "_id": 0 }
		)
		if infractions_query.count() == 0:
			await text_handler.send(ctx, "pardon_infraction_not_found")
			return
		infraction = None
		for inf in infractions_query:
			infraction = inf
		infractions.delete_one(
			{
				"guild_id": ctx.guild.id,
				"infraction_id": inf_id
			}
		)
		for server in query:
			log_channel = ctx.guild.get_channel(server["log_channels"]["moderator_actions"])
			author_name = await clean.clean_escape(str(ctx.author))
			user = ctx.guild.get_member(infraction["user_id"])
			mod = ctx.guild.get_member(infraction["moderator_id"])
			user_name = await clean.clean_escape(str(user) if user is not None else str(self.bot.get_user(infraction["user_id"])))
			mod_name = await clean.clean_escape(str(mod) if mod is not None else str(self.bot.get_user(infraction["moderator_id"])))
			if log_channel is not None:
				await log_channel.send(
					content=text_handler.translate(
						server["language"],
						"mod_log_pardon",
						time=datetime.now().strftime('%H:%M:%S'),
						author_name=author_name,
						author_id=ctx.author.id,
						inf_id=inf_id
					),
					embed=discord.Embed().from_dict(
						{
							"color": self.get_embed_color_per_action("pardon"),
							"fields": [
								{
									"name": text_handler.translate(
										server["language"],
										"mod_log_pardon_inf_info"
									),
									"value": text_handler.translate(
										server["language"],
										"mod_log_pardon_inf_info_format",
										user=user_name,
										moderator=mod_name,
										type=infraction["type"],
										inf_reason=infraction["reason"]
									)
								},
								{
									"name": text_handler.translate(
										server["language"],
										"mod_log_reason"
									),
									"value": reason
								}
							]
						}
					)
				)


	@commands.command(aliases=["check"])
	@experiments.has_experiment(current_experiments.MODERATION)
	@permissions.has_permission(permissions.MODERATOR)
	async def infractions(self, ctx, user: discord.Member):
		database = self.bot.client[config.database_name]
		infractions = database["infractions"]
		servers = database["servers"]
		server_query = servers.find(
			{
				"id": ctx.guild.id
			}, {"_id": 0}
		).limit(1)
		infractions_query = infractions.find(
			{
				"guild_id": ctx.guild.id,
				"user_id": user.id
			}, { "_id": 0 }
		)
		if server_query.count() == 0:
			await ctx.send("Oh no! This server has not been set up yet, but don't fret, run `<.setup` and we'll get this server all ready in no time!")
			return
		if infractions_query.count() == 0:
			await ctx.send("No infractions were found for that member.")
			return
		infractions_query = list(infractions_query)
		infractions_str = ""
		longest_reason = 0
		for infraction in infractions_query:
			if len(infraction['reason']) > longest_reason:
				longest_reason = len(infraction['reason'])
		for infraction in infractions_query:
			inf = f"| {infraction['type']} | {infraction['infraction_id']}"
			for x in range(len("------------------ ") - len(str(infraction["infraction_id"]))):
				inf+=" "
			inf+= f"| {infraction['moderator_id']} | {infraction['reason']}"
			for x in range(longest_reason - len(infraction["reason"])):
				inf+=" "
			inf += " |\n"
			infractions_str += inf
		header = "| Type    | Infraction ID      | Moderator ID       | Reason"
		header_2="| ------- | ------------------ | ------------------ | "
		for x in range(longest_reason):
			header_2 += "-"
		for x in range(longest_reason-len("Reason")):
			header += " "
		header += " |\n"
		header_2 += " |\n"
		await ctx.send(f"```{header}{header_2}{infractions_str}```")

	@commands.command()
	@decorators.is_admin()
	async def infdrop(self, ctx):
		timestamp_now = await timestamp()
		await self.bot.log_channel.send(f"{timestamp_now} Admin: {str(ctx.author)}({ctx.author.id}) dropped all infractions for guild: {ctx.guild.id} {emojis['INFRACTION_DROP']}")
		database = self.bot.client[config.database_name]
		infractions = database["infractions"]
		for infraction in infractions.find({"server_id": ctx.guild.id}, {"_id": 0}).limit(1):
			infractions.delete_one(infraction)
		for infraction in infractions.find({"guild_id": ctx.guild.id}, {"_id": 0}):
			infractions.delete_one(infraction)
		await ctx.send("Dropped db")

	@commands.command(aliases=["strike"])
	@experiments.has_experiment(current_experiments.MODERATION)
	@permissions.has_permission(permissions.MODERATOR)
	async def warn(self, ctx, user: discord.Member, *, reason: str = "No reason specified."):
		await self.add_infraction(ctx, "warning", user, reason)

	async def add_infraction(self, ctx, inf_type: str, user: discord.Member, reason: str):
		database = self.bot.client[config.database_name]
		infractions = database["infractions"]
		servers = database["servers"]
		query = servers.find({"id": ctx.guild.id}, {"_id": 0}).limit(1)
		infractions_server_query = infractions.find(
			{
				#delibirate, do not "fix"
				"server_id": ctx.guild.id
			}, {"_id": 0}
		)
		if query.count() == 0:
			await ctx.send("Oh no! This server has not been set up yet, but don't fret, run `<.setup` and we'll get this server all ready in no time!")
			return
		for server in query:
			# permissions check
			if len(reason) > config.max_reason_length:
				await text_handler.send(ctx, "moderation_failure_reason_too_long", max_reason_length=config.max_reason_length, amount=(len(reason) - config.max_reason_length))
				return
			reason = await clean.clean_escape(reason)
			id = 0
			if infractions_server_query.count() != 0:
				for infraction_server in infractions_server_query:
					id = infraction_server["last_id"]+1
					infractions.update_one(
						{
							"server_id": ctx.guild.id
						},
						{
							"$set": {
								"last_id": infraction_server["last_id"]+1
							}
						}
					)
			else:
				infractions.insert_one(
					{
						"server_id": ctx.guild.id,
						"last_id": 0
					}
				)
			infractions.insert_one(
				{
					"guild_id": ctx.guild.id,
					"moderator_id": ctx.author.id,
					"user_id": user.id,
					"infraction_id": id,
					"reason": reason,
					"type": inf_type
				}
			)
			user_name = await clean.clean_escape(str(user))
			author_name = await clean.clean_escape(str(ctx.author))
			if inf_type == "ban":
				try:
					await ctx.guild.ban(user, reason=text_handler.translate(server["language"], "audit_log_ban", moderator=author_name, reason=reason))
				except discord.Forbidden:
					return await text_handler.send(ctx, "moderation_ban_failure_missing_permissions")
			elif inf_type == "kick":
				try:
					await ctx.guild.kick(user, reason=text_handler.translate(server["language"], "audit_log_kick", moderator=author_name, reason=reason))
				except discord.Forbidden:
					return await text_handler.send(ctx, "moderation_kick_failure_missing_permissions")
			await text_handler.send(ctx, f"moderation_{inf_type}_success", user_name=user_name, user_id=user.id)
			guild = self.bot.get_guild(server["id"])
			log_channel = guild.get_channel(server["log_channels"]["moderator_actions"])
			if log_channel is not None:
				await log_channel.send(
					content=text_handler.translate(
						server["language"],
						f"mod_log_{inf_type}",
						time=datetime.now().strftime('%H:%M:%S'),
						infraction_id=id,
						author_name=author_name,
						author_id=ctx.author.id,
						user_name=user_name,
						user_id=user.id
					),
					embed=discord.Embed().from_dict(
						{
							"title": text_handler.translate(
								server["language"],
								"mod_log_reason"
							),
							"description": reason,
							"color": self.get_embed_color_per_action(inf_type)
						}
					)
				)

	def get_embed_color_per_action(self, action: str):
		if action == "warning":
			return 16768000
		elif action == "ban" or action == "kick":
			return 16724530
		elif action == "pardon":
			return 4605695
		else:
			return 10197915

def setup(bot):
	bot.add_cog(Moderation(bot))
