from discord.ext import commands
import discord, config
from utils import snowflake
from utils import clean
from utils import experiments, current_experiments

class Basic(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(aliases=["check"])
	@experiments.has_experiment(current_experiments.MODERATION)
	async def infractions(self, ctx, user: discord.Member):
		database = self.bot.client["kanelbulle"]
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
			inf = f"| {infraction['type']} | {infraction['infraction_id']} | {infraction['moderator_id']} | {infraction['reason']}"
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

	@commands.command(aliases=["strike"])
	@experiments.has_experiment(current_experiments.MODERATION)
	async def warn(self, ctx, user: discord.Member, *, reason: str = "No reason specified."):
		database = self.bot.client["kanelbulle"]
		infractions = database["infractions"]
		servers = database["servers"]
		query = servers.find({"id": ctx.guild.id}, {"_id": 0}).limit(1)
		if query.count() == 0:
			await ctx.send("Oh no! This server has not been set up yet, but don't fret, run `<.setup` and we'll get this server all ready in no time!")
			return
		for server in query:
			# permissions check
			if len(reason) > config.max_reason_length:
				await ctx.send(f"Sorry! The maximum reason length is {config.max_reason_length}. Please shorten your reason by {len(reason) - config.max_reason_length} characters.")
				return
			reason = await clean.clean_escape(reason)
			infractions.insert_one(
				{
					"guild_id": ctx.guild.id,
					"moderator_id": ctx.author.id,
					"user_id": user.id,
					"infraction_id": snowflake.nextId(),
					"reason": reason,
					"type": "warning"
				}
			)
			user_name = await clean.clean_escape(str(user))
			await ctx.send(f"Successfully warned **{user_name}** (**{user.id}**)!")
			guild = self.bot.get_guild(server["id"])
			log_channel = guild.get_channel(server["log_channels"]["moderator_actions"])
			if log_channel is not None:
				author_name = await clean.clean_escape(str(ctx.author))
				await log_channel.send(
					content=f":warning: Moderator {author_name} (**{ctx.author.id}**) has warned user {user_name} (**{user.id}**)",
					embed=discord.Embed().from_dict(
						{
							"title": "> Reason",
							"description": reason,
							"color": 16768000
						}
					)
				)

def setup(bot):
	bot.add_cog(Basic(bot))