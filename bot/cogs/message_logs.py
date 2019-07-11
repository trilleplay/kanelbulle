from discord.ext import commands
import discord, pymongo, config

class MessageLogs(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_message(self, message):
		if message.guild is None:
			return
		database = self.bot.client[config.database_name]
		messages = database["messages"]
		servers = database["servers"]
		# Only store messages if logging is enabled.
		for server in servers.find({"id": message.guild.id}, {"_id": 0}).limit(1):
			if server["log_channels"]["messages"] is None:
				return
		messages.insert_one(
            {
                "guild_id": message.guild.id,
				"channel_id": message.channel.id,
                "message_id": message.id,
				"content": message.content,
				"author": message.author.id
            }
        )

	@commands.Cog.listener()
	async def on_raw_message_delete(self, payload):
		database = self.bot.client[config.database_name]
		servers = database["servers"]
		messages = database["messages"]
		for server in servers.find({"id": payload.guild_id}, {"_id": 0}).limit(1):
			guild = self.bot.get_guild(payload.guild_id)
			log_channel = guild.get_channel(server["log_channels"]["messages"])
			if log_channel is not None:
				for message in messages.find({"message_id": payload.message_id}, {"_id": 0}).limit(1):
					author = self.bot.get_user(message["author"])
					if not author.bot and message["channel_id"] != log_channel.id:
						await log_channel.send(
							content=f":x: **{author.name}**#{author.discriminator} ({message['author']})'s message has been deleted in <#{payload.channel_id}>",
							embed=discord.Embed().from_dict(
								{
									"description": message["content"],
									"color": 16745090
								}
							)
						)


def setup(bot):
    bot.add_cog(MessageLogs(bot))
