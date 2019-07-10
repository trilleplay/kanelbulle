from discord.ext import commands
from utils.gamestats import apex_fetch, fortnite_fetch
from utils.exceptions import Forbidden, Unknown, NotFound, Unavailable, RateLimit, InvalidPlatform
from utils.convert import ApexPlatformConverter, FortnitePlatformConverter
from utils.clean import clean_escape
from config import invite
import discord, math
import aiohttp

class GameStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.aiohttpclient = aiohttp.ClientSession()

    @commands.command()
    async def apex(self, ctx, platform: ApexPlatformConverter, *, username: str):
        if platform == "invalid":
            raise commands.BadArgument(message="Platform specified is invalid.")
        async with ctx.typing():
            try:
                data = await apex_fetch(self.aiohttpclient, platform["value"], username)
            except Forbidden:
                await ctx.send(f"Uh oh, something seems to be inproperly configured. Please contact the bot maintainer about this over at discord.gg/{invite}\nIf you're the bot maintainer please make sure your API keys are valid.")
                return
            except NotFound:
                await ctx.send("A player with that username could not be found, **Note:** make sure your username is 100% correct, and its also important that the platform paramater is correct aswell. Otherwise we cant find it :C")
                return
            except Unavailable:
                await ctx.send("It seems that Tracker Networks API is having problems at the moment :(\nPlease try again in a few moments.")
                return
            except RateLimit:
                await ctx.send("Uh oh, a lot of users are using our service and while we love this **HYPE**, we are limited on how fast we can check your and everyones stats.\nPlease retry again in a few moments once this has calmed down.")
                return
            except Unknown:
                await ctx.send("Oh no :(, it seems like the API we use to get your game stats is having some issues at the moment, hopefully this will be resolved soon.")
                return
            except InvalidPlatform:
                await ctx.send("Shit, something just happend that there are checks in place for how did this happen, please open an issue here: <https://github.com/trilleplay/paperplane/issues>.")
                return
            escaped_player_handle = await clean_escape(data['data']['metadata']['platformUserHandle'])
            embed = discord.Embed(title=f"{self.bot.user.name} showing lifetime stats for Apex Legends player: {escaped_player_handle}, on platform: {platform['name']}")
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url_as(static_format='png', size=1024))
            embed.set_thumbnail(url=data['data']['metadata']['avatarUrl'])
            for stat in data['data']['stats']:
                embed.add_field(name=stat["metadata"]["name"], value=stat["displayValue"], inline=True)
            await ctx.send(embed=embed)


    @commands.command()
    async def fortnite(self, ctx, platform: FortnitePlatformConverter, *, username: str):
        if platform == "invalid":
            raise commands.BadArgument(message="Platform specified is invalid.")
        async with ctx.typing():
            try:
                data = await fortnite_fetch(self.aiohttpclient, platform, username)
            except Forbidden:
                await ctx.send(f"Uh oh, something seems to be inproperly configured. Please contact the bot maintainer about this over at discord.gg/{invite}\nIf you're the bot maintainer please make sure your API keys are valid.")
                return
            except NotFound:
                await ctx.send("A player with that username could not be found, **Note:** we are asking you for your epic username, and its also important that the platform paramater is correct aswell.")
                return
            except Unavailable:
                await ctx.send("It seems that Tracker Networks API is having problems at the moment :(\nPlease try again in a few moments.")
                return
            except RateLimit:
                await ctx.send("Uh oh, a lot of users are using our service and while we love this **HYPE**, we are limited on how fast we can check your and everyones stats.\nPlease retry again in a few moments once this has calmed down.")
                return
            except Unknown:
                await ctx.send("Oh no :(, it seems like the API we use to get your game stats is having some issues at the moment, hopefully this will be resolved soon.")
                return
            except InvalidPlatform:
                await ctx.send("Shit, something just happend that there are checks in place for how did this happen, please open an issue here: <https://github.com/trilleplay/paperplane/issues>.")
                return
            escaped_player_handle = await clean_escape(data['epicUserHandle'])
            embed = discord.Embed(title=f"{self.bot.user.name} showing lifetime stats for Fortnite player: {escaped_player_handle}, on platform: {data['platformNameLong']}")
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url_as(static_format='png', size=1024))
            embed.set_footer(text="Portions of the materials used are trademarks and/or copyrighted works of Epic Games, Inc. All rights reserved by Epic. This material is not official and is not endorsed by Epic.")
            for stat in data["lifeTimeStats"]:
                embed.add_field(name=stat["key"], value=stat["value"], inline=True)
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(GameStats(bot))
