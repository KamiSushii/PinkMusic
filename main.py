import discord
from discord.ext import commands
from config import *

intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True

class pinkMusic(commands.Bot):
    def __init__(self):
        self._cogs = ['slash', 'battleship', 'music']
        super().__init__(command_prefix=self.prefix, case_insensitive=True, intents=intents, debug_guilds=debug_guilds)
        
    def setup(self):
        print("[*]Running setup...")

        self.remove_command('help')
        print("   - Default help command deleted.")

        for cog in self._cogs:
                self.load_extension(f"cogs.{cog}")
                print(f"   - Loaded {cog} cog.")

        print("[v]Setup complete.")

    def run(self):
        self.setup()
        
        print("[*]Running bot...")
        super().run(TOKEN, reconnect=True)

    async def on_connect(self):
        print(f"[v]Connected to Discord (latency: {self.latency*1000:,.0f} ms).")

    async def on_error(self, err, *args, **kwargs):
        raise 

    async def on_command_error(self, ctx, exc):
        raise getattr(exc, "original", exc)

    async def on_ready(self):
        self.client_id = (await self.application_info()).id

        activity_name='Please support my work! https://trakteer.id/kamisushi'
        activity_type=discord.ActivityType.custom

        await self.change_presence(activity=discord.Activity(type=activity_type,name=activity_name))
        print(f"\n{self.user.name} is online.")

    async def prefix(self, bot, msg):
        return commands.when_mentioned_or("`")(bot, msg)

bot = pinkMusic()
bot.run()