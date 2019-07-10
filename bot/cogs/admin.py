from discord.ext import commands

class AdminCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='leave')
    @commands.is_owner()
    async def server_leave(self, ctx, guild: int):
        leaveguild = self.bot.get_guild(guild)
        await leaveguild.leave()
        await ctx.send("Kanelbulle has now left that server.")

def setup(bot):
    bot.add_cog(AdminCog(bot))
