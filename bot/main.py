from discord.ext import commands
import pymongo, config, discord
from utils.get_prefix import get_prefix

bot = commands.AutoShardedBot(command_prefix=get_prefix)
bot.client = pymongo.MongoClient("mongodb://localhost:27017/")

cogs = ["basic", "setup", "moderation", "message_logs"]

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