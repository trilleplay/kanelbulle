from discord.ext import commands

def is_admin():
    def predicate(ctx):
        return ctx.author.id in [128181551472050176, 132819036282159104]
    return commands.check(predicate)