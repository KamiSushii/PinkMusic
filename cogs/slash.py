import discord
from discord.ext import commands


class Example(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()  # Create a slash command for the supplied guilds.
    async def jing(self, ctx: discord.ApplicationContext):
        await ctx.respond("Hi, this is a slash command from a cog!")

    @commands.slash_command()  # Not passing in guild_ids creates a global slash command.
    async def pan(self, ctx: discord.ApplicationContext):
        await ctx.respond("Hi, this is a global slash command from a cog!")


def setup(bot):
    bot.add_cog(Example(bot))