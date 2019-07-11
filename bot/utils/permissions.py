import pymongo, discord, config
from discord.ext import commands

client = pymongo.MongoClient("mongodb://localhost:27017/")
database = client[config.database_name]
servers = database["servers"]

ADMIN = 1 << 0
MODERATOR = 1 << 1

def get_permission(name: str):
    if name.lower() == "admin":
        return ADMIN
    elif name.lower() == "moderator":
        return MODERATOR
    else:
        return None

def get_permission_str(permission: int):
    if permission == ADMIN:
        return "admin"
    elif permission == MODERATOR:
        return "moderator"
    else:
        return "None"

def has_permission_role(guild_id: int, role: int, permission: int):
    for server in servers.find({"id": guild_id}, {"role_permissions": 1}).limit(1):
        for role_permission in server["role_permissions"]:
            if role_permission["role_id"] == role:
                return (role_permission["perms"] & permission) == permission or (role_permission["perms"] & ADMIN) == ADMIN
    return None

def has_permission_member(guild_id: int, member: discord.Member, permission: int):
    for server in servers.find({"id": guild_id}, {"role_permissions": 1}).limit(1):
        for role_permission in server["role_permissions"]:
            for role in member.roles:
                if role_permission["role_id"] == role.id:
                    return (role_permission["perms"] & permission) == permission or (role_permission["perms"] & ADMIN) == ADMIN
        return False
    return None

def set_permission(guild_id: int, role: int, permission: int, on: bool):
    for server in servers.find({"id": guild_id}, {"role_permissions": 1}).limit(1):
        role_permissions = []
        role_permissions_ids = []
        for role_permission in server["role_permissions"]:
            if role_permission["role_id"] == role and on:
                return
            role_permissions.append(role_permission)
            role_permissions_ids.append(role_permission["role_id"])
        if on:
            role_permissions.append({"role_id": role, "perms": permission})
        if not on and role in role_permissions_ids:
            role_permissions.remove({"role_id": role, "perms": permission})
        servers.update_one(
            {
                "id": guild_id
            },
            {
                "$set": {
                    "role_permissions": role_permissions
                }
            }
        )

def has_permission(permission):
    def predicate(ctx):
        if ctx.guild is None:
            return False
        if ctx.author.id == ctx.guild.owner_id:
            return True
        if ctx.author.id in config.admins:
            return True
        return has_permission_member(ctx.guild.id, ctx.author, permission)
    return commands.check(predicate)