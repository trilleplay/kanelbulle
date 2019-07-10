from discord.ext import commands
from discord.utils import escape_mentions
from discord.utils import escape_markdown
import pymongo, discord, asyncio, re

client = pymongo.MongoClient("mongodb://localhost:27017/")
database = client["kanelbulle"]
servers = database["servers"]

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def settings(self, ctx):
        query = servers.find({"id": ctx.guild.id}, {"_id": 0}).limit(1)
        #will only run once anyway
        for server in query:
            embed = discord.Embed().from_dict(
                {
                    "title": "> Settings",
                    "color": 15575881,
                    "fields": [
                        {
                            "name": "Log Channels",
                            "value": f"**Moderator actions:** <#{server['log_channels']['moderator_actions']}>\n**Messages:** <#{server['log_channels']['messages']}>"
                        }
                    ]
                }
            )
            await ctx.send(embed=embed)
            return
        await ctx.send("Oh no! This server has not been set up yet, but don't fret, run `<.setup` and we'll get this server all ready in no time!")

    @commands.command()
    async def prefix(self, ctx, prefix: str):
        servers.update_one({"id": ctx.guild.id}, {"$set": {"prefix": prefix}})
        await ctx.send(f"Prefix set to {escape_markdown(escape_mentions(prefix))}.")

    @commands.command()
    async def setup(self, ctx):
        query = servers.find({"id": ctx.guild.id}, {"_id": 0}).limit(1)
        def reaction_check(reaction, user):
            return user.id == ctx.author.id and (str(reaction.emoji) == "❌" or str(reaction.emoji) == "✅")
        def message_check(message):
            return message.author.id == ctx.author.id and message.channel.id == ctx.channel.id
        if query.count() != 0:
            m = await ctx.send("Hmm. It looks like this server is already set up.. Would you like to start over?")
            await m.add_reaction("✅")
            await m.add_reaction("❌")
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=20.0, check=reaction_check)
                if str(reaction.emoji) == "❌":
                    await ctx.send("Okay. I have canceled the setup for you.")
                    await m.delete()
                    return
                elif str(reaction.emoji) == "✅":
                    await m.delete()
                    servers.delete_one({"id": ctx.guild.id})
            except asyncio.TimeoutError:
                await ctx.send("You didn't click any of the reactions in time, so to be safe I canceled it.")
                return
            servers.delete_one({"id": ctx.guild.id})
        m = await ctx.send("Welcome to the Kanelbulle setup! I will ask you a couple of questions, and set up the server for you! It's that easy. Are you ready?")
        await m.add_reaction("✅")
        await m.add_reaction("❌")
        reaction, user = await self.bot.wait_for("reaction_add", check=reaction_check)
        if str(reaction.emoji) == "❌":
            await ctx.send("That's fine, I'll be here when you're ready!")
            await m.delete()
            return
        elif str(reaction.emoji) == "✅":
            await m.delete()
        m1 = await ctx.send(
            "Glad to hear! :) " 
            +"Now let's get started, shall we? Should you accidentally click the wrong reaction, or answer wrongly, no need to start over you can all change this later on."
            +"\nWould you like to enable the moderation part of the bot for your server?"
        )
        await m1.add_reaction("✅")
        await m1.add_reaction("❌")
        reaction1, user = await self.bot.wait_for("reaction_add", check=reaction_check)
        res = None
        moderation_enabled = str(reaction1.emoji) == "✅"
        if moderation_enabled:
            res = await ctx.send("I will enable that for you.")
            await m1.delete()
        else:
            res = await ctx.send("Okay, I will **not** enable the moderation part.")
            await m1.delete()
        moderation_channel = None
        if moderation_enabled:
            m2 = await ctx.send("Would you like me to log moderator actions to a channel?")
            await m2.add_reaction("✅")
            await m2.add_reaction("❌")
            reaction2, user = await self.bot.wait_for("reaction_add", check=reaction_check)
            await res.delete()
            if str(reaction2.emoji) == "✅":
                await m2.delete()
                _m = await ctx.send("Okay. Where would you like me to log it to?")
                m3 = await self.bot.wait_for("message", check=message_check)
                mod_actions_log_input = None
                try:
                    mod_actions_log_input = ctx.guild.get_channel(int(m3.content))
                    await _m.delete()
                    await m3.delete()
                except ValueError:
                    try:
                        mod_actions_log_input = ctx.guild.get_channel(int(m3.content.split("<#")[1].split(">")[0]))
                        await _m.delete()
                        await m3.delete()
                    except ValueError:
                        await ctx.send("Oh no! That doesn't seem like a valid channel..")
                        return
                if mod_actions_log_input is None:
                    await ctx.send("Hmmm. I can't seem to find that channel.. Are you sure I have access to it?")
                    return
                moderation_channel = mod_actions_log_input.id
                await ctx.send(f"Okay! I will log moderator actions to <#{mod_actions_log_input.id}>.")
        messages_channel = None
        m2 = await ctx.send("Would you like me to log deleted messages to a channel?")
        await m2.add_reaction("✅")
        await m2.add_reaction("❌")
        reaction2, user = await self.bot.wait_for("reaction_add", check=reaction_check)
        if not moderation_enabled:
            await res.delete()
        if str(reaction2.emoji) == "✅":
            await m2.delete()
            _m = await ctx.send("Okay. Where would you like me to log it to?")
            m3 = await self.bot.wait_for("message", check=message_check)
            messages_log_input = None
            try:
                messages_log_input = ctx.guild.get_channel(int(m3.content))
                await _m.delete()
            except ValueError:
                try:
                    messages_log_input = ctx.guild.get_channel(int(m3.content.split("<#")[1].split(">")[0]))
                    await _m.delete()
                    await m3.delete()
                except ValueError:
                    await ctx.send("Oh no! That doesn't seem like a valid channel..")
                    await _m.delete()
                    return
            if messages_log_input is None:
                await ctx.send("Hmmm. I can't seem to find that channel.. Are you sure I have access to it?")
                await _m.delete()
                return
            messages_channel = messages_log_input.id
            await ctx.send(f"Okay! I will log deleted messages to <#{messages_log_input.id}>.")
        m3 = await ctx.send("Would you like to have a custom prefix?")
        await m3.add_reaction("✅")
        await m3.add_reaction("❌")
        reaction3, user = await self.bot.wait_for("reaction_add", check=reaction_check)
        prefix = ">."
        await m3.delete()
        if str(reaction3.emoji) == "✅":
            await ctx.send("Okay. Which one would you like?")
            m4 = await self.bot.wait_for("message", check=message_check)
            prefix = m4.content
        servers.insert_one(
            {
                "id": ctx.guild.id,
                "prefix": prefix,
                "log_channels": {
                    "moderator_actions": moderation_channel,
                    "messages": messages_channel
                }
            }
        )
        await ctx.send("And that's it! You're good to go! :)")
        

def setup(bot):
    bot.add_cog(Setup(bot))