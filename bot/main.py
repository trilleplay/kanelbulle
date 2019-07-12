from discord.ext import commands
import pymongo, discord
from config import token, admin_actions_log, emojis
from utils.get_prefix import get_prefix
from utils.timestamp import timestamp

bot = commands.AutoShardedBot(command_prefix=get_prefix)
bot.client = pymongo.MongoClient("mongodb://localhost:27017/")

cogs = ["basic", "setup", "moderation", "message_logs", "gamestats", "levels", "admin"]

for cog in cogs:
	bot.load_extension(f"cogs.{cog}")
	print(f"Loaded cog {cog}.")

# bot.load_extension("jishaku")
# print("Loaded cog jishaku")

first_run = 0

@bot.listen()
async def on_ready():
	global first_run
	if first_run == 0:
		first_run = 1
		bot.log_channel = bot.get_channel(admin_actions_log)
	print("Bot is READY.")
	timestamp_now = await timestamp()
	await bot.log_channel.send(f"{timestamp_now} Bot is ready! {emojis['READY']}")

try:
	bot.run(token)
except KeyboardInterrupt:
	print("Shutting down..")
