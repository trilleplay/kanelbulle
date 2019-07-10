import pymongo
from discord.ext import commands

client = pymongo.MongoClient("mongodb://localhost:27017/")
database = client["kanelbulle"]
servers = database["servers"]

def has(guild_id: int, experiment: int):
    for server in servers.find({"id": guild_id}, {"experiments": 1}).limit(1):
        return (server["experiments"] & experiment) == experiment
    return None

# ignore this one for a bit
def has_multiple(guild_id: int, experiments: list):
    for server in servers.find({"id": guild_id}, {"experiments": 1}).limit(1):
        server_experiments = 0
        for experiment in experiments:
            server_experiments+=experiment
        return server["experiments"] == server_experiments
    return None

def set_experiment(guild_id: int, experiment: int, on: bool):
    for server in servers.find({"id": guild_id}, {"experiments": 1}).limit(1):
        if on and not has(guild_id, experiment):
            servers.update_one({"id": guild_id}, {"$set": {"experiments": server["experiments"] + experiment}})
        if not on and has(guild_id, experiment):
            servers.update_one({"id": guild_id}, {"$set": {"experiments": server["experiments"] - experiment}})
    return None

def has_experiment(experiment):
    def predicate(ctx):
        return has(ctx.guild.id, experiment)
    return commands.check(predicate)