from discord.ext import commands
import discord, pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
database = client["kanelbulle"]
servers = database["servers"]

class MessageLogs(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_message_delete(self, message):
		for server in servers.find({"id": message.guild.id}, {"_id": 0}).limit(1):
			log_channel = message.guild.get_channel(server["log_channels"]["messages"])
			if log_channel is not None:
				await log_channel.send(
					content=f":x: **{message.author.name}**#{message.author.discriminator} ({message.author.id})'s message has been deleted in <#{message.id}>",
					embed=discord.Embed().from_dict(
						{
							"description": message.content,
							"color": 16745090
						}
					)
				)


def setup(bot):
    bot.add_cog(MessageLogs(bot))