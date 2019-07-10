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

class FortnitePlatformConverter(commands.Converter):
    async def convert(self, ctx, argument):
        if argument.lower() == "pc":
            request_platform = "pc"
        elif argument.lower() == "ps4":
            request_platform = "psn"
        elif argument.lower() == "xbox":
            request_platform = "xbl"
        else:
            request_platform = "invalid"
        return(request_platform)
