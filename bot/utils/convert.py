from discord.ext import commands

class ApexPlatformConverter(commands.Converter):
    async def convert(self, ctx, argument):
        ValidPlatforms = {
            "XBOX": {"value": "xbl", "name": "Xbox"},
            "PS4": {"value": "psn", "name": "PSN"},
            "PC": {"value": "origin", "name": "PC"}
        }
        try:
            return(ValidPlatforms[f"{argument.upper()}"])
        except KeyError:
            return("invalid")
