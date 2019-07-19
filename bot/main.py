from discord.ext import commands
import pymongo, discord
from config import token, admin_actions_log, emojis, sentry_dsn
import logging
import sentry_sdk
from utils.get_prefix import get_prefix
from utils.timestamp import timestamp
from discord.ext import commands

logging.basicConfig(level=logging.INFO)

# track errors in sentry
if sentry_dsn != '':
	sentry_sdk.init(sentry_dsn)

bot = commands.AutoShardedBot(command_prefix=get_prefix)
bot.client = pymongo.MongoClient("mongodb://localhost:27017/")

cogs = ["basic", "setup", "moderation", "message_logs", "gamestats", "levels", "admin"]

for cog in cogs:
	bot.load_extension(f"cogs.{cog}")
	print(f"Loaded cog {cog}.")

# bot.load_extension("jishaku")
# print("Loaded cog jishaku")

STARTUP_COMPLETE = False

@bot.listen()
async def on_ready():
	global STARTUP_COMPLETE
	if not STARTUP_COMPLETE:
		STARTUP_COMPLETE = True
		bot.log_channel = bot.get_channel(admin_actions_log)
		print("Bot is READY.")
		timestamp_now = timestamp()
		await bot.log_channel.send(f"{timestamp_now} Bot is ready! {emojis['READY']}")

@bot.listen()
async def on_command_error(ctx: commands.Context, error):
	ignored = [commands.BotMissingPermissions, commands.CheckFailure, commands.CommandOnCooldown, commands.MissingRequiredArgument, commands.BadArgument]
	for i in ignored:
		if isinstance(error, i):
			return
	sentry_sdk.capture_exception(error)
		
					   
try:
	bot.run(token)
except KeyboardInterrupt:
	print("Shutting down..")
