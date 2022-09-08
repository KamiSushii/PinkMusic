from discord.ext import commands

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="test")
    async def test(self, ctx):
        await ctx.send("tested")

def setup(bot):
    bot.add_cog(Music(bot))