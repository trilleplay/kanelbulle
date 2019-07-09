from discord.ext import commands
import pymongo, config, discord

client = pymongo.MongoClient("mongodb://localhost:27017/")
database = client["kanelbulle"]
servers = database["servers"]

def get_prefix(bot, message):
	query = servers.find({"id": message.guild.id}, {"_id": 0}).limit(1)
	if not message.guild or query.count() == 0:
		return '>.'
	prefix = ""
	for server in query:
		prefix = server["prefix"]
	return commands.when_mentioned_or(prefix)(bot, message)

bot = commands.AutoShardedBot(command_prefix=get_prefix)

cogs = ["basic", "setup", "moderation"]

for cog in cogs:
	bot.load_extension(f"cogs.{cog}")
	print(f"Loaded cog {cog}.")

@bot.listen()
async def on_ready():
	print("Bot is READY.")


try:
	bot.run(config.token)
except KeyboardInterrupt:
	print("Shutting down..")
