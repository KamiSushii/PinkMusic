from pathlib import Path
from config import *
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True

class pinkMusic(commands.Bot):
    def __init__(self):
        self._cogs = ["music", "slash"]
        super().__init__(command_prefix=self.prefix, case_insensitive=True, intents=intents)
        
    def setup(self):
        print("[*]Running setup...")

        self.remove_command('help')
        print("   - Default help command deleted.")

        for cog in self._cogs:
                self.load_extension(f"cogs.{cog}")
                print(f"   - Loaded {cog}.py.")

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

        game_name='with ur mom | 🎵.help'
        activity_type=discord.ActivityType.playing

        await self.change_presence(activity=discord.Activity(type=activity_type,name=game_name))
        print(f"\n{self.user.name} is online.")

    async def prefix(self, bot, msg):
        return commands.when_mentioned_or("`")(bot, msg)

    # async def process_commands(self, msg):
    #     ctx = await self.get_context(msg, cls=commands.Context)

    #     if ctx.command is not None:
    #         await self.invoke(ctx)

    # async def on_message(self, msg):
    #     if not msg.author.bot:
    #         await self.process_commands(msg)

bot = pinkMusic()
bot.run()