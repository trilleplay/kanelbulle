from discord.ext import commands
import config

def is_admin():
    def predicate(ctx):
        return ctx.author.id in config.admins
    return commands.check(predicate)