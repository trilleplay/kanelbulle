from discord.ext.commands import when_mentioned_or
import config

async def get_prefix(bot, message):
    database = bot.client[config.database_name]
    servers = database["servers"]
    query = servers.find({"id": message.guild.id}, {"_id": 0}).limit(1)
    if not message.guild or query.count() == 0:
	       return '<.'
    prefix = ""
    for server in query:
        prefix = server["prefix"]
    return when_mentioned_or(prefix)(bot, message)
