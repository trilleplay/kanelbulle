from discord.ext import commands
import textwrap, traceback, contextlib, io
from utils import experiments, current_experiments, decorators
from utils.timestamp import timestamp

class AdminCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='leave')
    @commands.is_owner()
    async def server_leave(self, ctx, guild: int):
        leaveguild = self.bot.get_guild(guild)
        await leaveguild.leave()
        await ctx.send("Kanelbulle has now left that server.")
        timestamp_now = await timestamp()
        await self.bot.log_channel.send(f"{timestamp_now} Bot was removed from server {guild} by {str(ctx.author)}({ctx.author.id}) {emojis['LEAVE']}")

    @commands.group(name="experiments")
    @decorators.is_admin()
    async def experiments_cmd(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid sub command passed.")

    @experiments_cmd.command()
    async def has(self, ctx, experiment_id: int):
        await ctx.send(f"Experiment on: {experiments.has(ctx.guild.id, 1 << experiment_id)}")
        timestamp_now = timestamp()
        await self.bot.log_channel.send(f"{timestamp_now} {str(ctx.author)}({ctx.author.id}) checked if experiment: {experiment_id} was enabled for ``{ctx.guild.id}`` {emojis['EXPERIMENT']}")

    @experiments_cmd.command(name="set")
    async def _set(self, ctx, experiment_id: int, on: bool):
        experiments.set_experiment(ctx.guild.id, 1 << experiment_id, on)
        await ctx.send(f"Experiment on: {experiments.has(ctx.guild.id, 1 << experiment_id)}")
        timestamp_now = timestamp()
        await self.bot.log_channel.send(f"{timestamp_now} {str(ctx.author)}({ctx.author.id}) changed the state of experiment: {experiment_id} for: ``{ctx.guild.id}`` {emojis['EXPERIMENT']}")

    # Eval Command - https://github.com/Rapptz/RoboDanny by Rapptz see credit.md for License
    @commands.command(hidden=True, name='eval')
    @commands.is_owner()
    async def eval(self, ctx:commands.Context, *, code: str):
        timestamp_now = timestamp()
        await self.bot.log_channel.send(f"{timestamp_now} {str(ctx.author)}({ctx.author.id}) evaluated this code: ``{code}`` {emojis['EVAL']}")
        output = None
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message
        }

        env.update(globals())

        if code.startswith('```'):
            code = "\n".join(code.split("\n")[1:-1])

        out = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(code, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            output = f'{e.__class__.__name__}: {e}'
        else:
            func = env['func']
            try:
                with contextlib.redirect_stdout(out):
                    ret = await func()
            except Exception as e:
                value = out.getvalue()
                output = f'{value}{traceback.format_exc()}'
            else:
                value = out.getvalue()
                if ret is None:
                    if value:
                        output = value
                else:
                    output = f'{value}{ret}'
        if output is not None:
            await ctx.send(output)
        else:
            await ctx.send("I did a thing!")

def setup(bot):
    bot.add_cog(AdminCog(bot))
