from discord.ext import commands
import discord, pymongo, time, config
from utils import experiments, current_experiments, text_handler, clean, decorators

class Levels(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	def set_unlockable_role_at(self, guild: int, xp: int, role: discord.Role):
		database = self.bot.client["kanelbulle"]
		servers = database["servers"]
		doc = servers.find({"id": guild}).limit(1)
		if doc is not None:
			unlockable_roles = []
			for x in doc:
				try:
					unlockable_roles = x["xp_unlockable_roles"]
				except KeyError:
					pass
			updating = False
			for unlockable_role in unlockable_roles:
				if role.id == unlockable_role["role"]:
					print("updating, not inserting")
					updating = True
					unlockable_role["role"] = role.id
			if not updating:
				unlockable_roles.append({"xp": xp, "role": role.id})
			print("adding unlockable role")
			servers.update_one({"id": guild}, {"$set": {"xp_unlockable_roles": unlockable_roles}})

	def get_unlockable_roles(self, guild: int):
		database = self.bot.client["kanelbulle"]
		servers = database["servers"]
		doc = servers.find({"id": guild}, {"_id": 0})
		if doc is not None:
			unlockable_roles = []
			for x in doc:
				try:
					unlockable_roles = x["xp_unlockable_roles"]
				except KeyError:
					return None
			return unlockable_roles
		else:
			return None

	@commands.command()
	@decorators.is_admin()
	async def guild(self, ctx):
		database = self.bot.client["kanelbulle"]
		servers = database["servers"]
		for server in servers.find({"id": ctx.guild.id}, {"_id": 0}):
			await ctx.send(server)

	@commands.command()
	@commands.guild_only()
	@experiments.has_experiment(current_experiments.LEVELS)
	async def rank(self, ctx):
		database = self.bot.client["kanelbulle"]
		levels = database["levels"]
		servers = database["servers"]
		level_query = levels.find(
			{
				"user_id": ctx.author.id,
				"guild_id": ctx.guild.id
			}, {"_id": 0}
		).limit(1)
		server_query = servers.find(
			{
				"id": ctx.guild.id
			}, {"_id": 0}
		)
		if server_query.count() == 0:
			return
		for server in server_query:
			for level_doc in level_query:
				await ctx.author.send(text_handler.translate(server["language"], "leveling_rank_cmd", xp=level_doc["level"], guild_name=ctx.guild.name))
				return
		await ctx.author.send(text_handler.translate(server["language"], "leveling_rank_cmd", xp=0, guild_name=ctx.guild.name))
	
	@commands.group()
	@experiments.has_experiment(current_experiments.LEVELS)
	async def roles(self, ctx):
		if ctx.invoked_subcommand is None:
			await text_handler.send(ctx, "invalid_sub_command")
	
	@roles.command()
	async def list(self, ctx):
		await ctx.send(f"{self.get_unlockable_roles(ctx.guild.id)}")

	@roles.command()
	async def add(self, ctx, xp: int, role: discord.Role):
		if self.get_unlockable_roles(ctx.guild.id) is not None and role.id in self.get_unlockable_roles(ctx.guild.id):
			await text_handler.send(ctx, "leveling_role_already_assigned")
			return
		self.set_unlockable_role_at(ctx.guild.id, xp, role)
		role_name = await clean.clean_escape(role.name)
		await text_handler.send(ctx, "leveling_role_assign_success", role=role_name, xp=xp)

	@commands.Cog.listener()
	async def on_message(self, message):
		if message.guild is None or message.author.bot:
			return
		if experiments.has(message.guild.id, current_experiments.LEVELS):
			database = self.bot.client["kanelbulle"]
			levels = database["levels"]
			level_query = levels.find(
				{
					"user_id": message.author.id,
					"guild_id": message.guild.id
				}, {"_id": 0}
			).limit(1)
			cooldowns = database["cooldowns"]
			cooldown_query = cooldowns.find(
				{
					"user_id": message.author.id,
					"guild_id": message.guild.id,
					"type": "xp"
				}, {"_id": 0}
			).limit(1)

			if cooldown_query.count() > 0:
				for cooldown in cooldown_query:
					if (time.time() - cooldown["last_xp_gain"]) > 30:
						if level_query.count() == 0:
							levels.insert_one(
								{
									"user_id": message.author.id,
									"guild_id": message.guild.id,
									"level": config.xp_gain
								}
							)
						else:
							for level_doc in level_query:
								levels.update_one(
									{
										"user_id": message.author.id,
										"guild_id": message.guild.id
									},
									{
										"$set": {
											"level": level_doc["level"]+config.xp_gain
										}
									}
								)
								role_ids = []
								for role in message.author.roles:
									role_ids.append(role.id)
								unlockable_roles = self.get_unlockable_roles(message.guild.id)
								if unlockable_roles is not None:
									for unlockable_role in unlockable_roles:
										if unlockable_role["role"] not in role_ids:
											if unlockable_role["xp"] <= level_doc["level"]+config.xp_gain:
												await message.author.add_roles(message.guild.get_role(unlockable_role["role"]), reason="User reached level {}".format(unlockable_role["xp"]))
						cooldowns.update_one(
						{
							"user_id": message.author.id,
							"guild_id": message.guild.id,
							"type": "xp"
						},
						{
							"$set": {
								"last_xp_gain": time.time()
							}
						}
					)

			if cooldown_query.count() == 0:
				cooldowns.insert_one(
					{
						"user_id": message.author.id,
						"guild_id": message.guild.id,
						"last_xp_gain": time.time(),
						"type": "xp"
					}
				)



def setup(bot):
    bot.add_cog(Levels(bot))
