from discord.ext import commands
import discord, math

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        embed = discord.Embed().from_dict({
            "title": ":ping_pong: Pong!",
            "description": f"{str(round(self.bot.latency * 1000, 1))} ms",
            "color": 15575881
        })
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Basic(bot))