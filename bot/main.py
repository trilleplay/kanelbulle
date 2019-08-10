from discord.ext import commands
import pymongo, discord
from config import token, admin_actions_log, emojis, sentry_dsn
import logging
import sentry_sdk
from utils.get_prefix import get_prefix
from utils.timestamp import timestamp
from utils.prometheus_tools import startup_prometheus, ready_events, reconnects, all_users, message_events, all_guilds
from discord.ext import commands

logging.basicConfig(level=logging.INFO)

# track errors in sentry
if sentry_dsn != '':
	sentry_sdk.init(sentry_dsn)

startup_prometheus()
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
async def on_guild_join(guild):
	all_guilds.inc()

@bot.listen()
async def on_guild_remove(guild):
	all_guilds.dec()

@bot.listen()
async def on_member_join(member):
	all_users.set(len(set(bot.get_all_members())))

@bot.listen()
async def on_member_remove(member):
	all_users.set(len(set(bot.get_all_members())))

@bot.listen()
async def on_message(message):
	message_events.inc()

@bot.listen()
async def on_reconnect():
	reconnects.inc()

@bot.listen()
async def on_ready():
	ready_events.inc()
	all_users.set(len(set(bot.get_all_members())))
	all_guilds.set(len(bot.guilds))
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
