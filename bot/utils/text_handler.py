import discord, config, pymongo, json, os
from cachetools import cached, TTLCache

client = pymongo.MongoClient("mongodb://localhost:27017/")
database = client[config.database_name]
servers = database["servers"]

string_cache = TTLCache(maxsize=100, ttl=300)

@cached(string_cache)
def translate(lang: str, string: str, **kwargs):
    for filename in os.listdir("lang"):
        if lang.lower() == filename.split(".json")[0].lower():
            with open(f"lang/{filename}") as dataf:
                returntranslatedstring = json.load(dataf)
            return returntranslatedstring[string].format(**kwargs)

async def send_lang(ctx, string: str, language: str, **kwargs):
    msg = await ctx.send(translate(language, string, **kwargs))
    return msg

async def send(ctx, string: str, **kwargs):
    query = servers.find({"id": ctx.guild.id}, {"_id": 0}).limit(1)
    for server in query:
        msg = await ctx.send(translate(server["language"], string, **kwargs))
        return msg
    