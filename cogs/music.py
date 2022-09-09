import wavelink, discord, asyncio, datetime, re
from . import queue
from .error import *
from wavelink.ext import spotify
from discord.ext import commands
from config import *

class Music(commands.Cog, wavelink.Player):
    def __init__(self, bot):
        self.bot = bot
        self.player = None
        # self.__queue = wavelink.Queue()
        bot.loop.create_task(self.start_nodes())

    def convert(self, sec):
        return str(datetime.timedelta(seconds = sec))

    async def connect(self, ctx, channel=None):
        if self.is_connected:
            raise AlreadyConnectedToChannel

        if (channel := getattr(ctx.author.voice, "channel", channel)) is None:
            raise NoVoiceChannel

        await super().connect(channel.id)
        return channel
    
    async def start_nodes(self):
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(bot=self.bot,
                                            host='lava.link',
                                            port=80,
                                            password='youshallnotpass',
                                            identifier='pinkMusic',
                                            region='asia',)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f'Node: <{node.identifier}> is ready!')

    @commands.Cog.listener()
    async def on_track_end():
        pass

    async def add_youtubepl(self, ctx, query):
        tracks = await wavelink.YouTubePlaylist.search(query=query)

        for t in tracks.tracks:
            self.player.queue.put(t)

    async def add_youtube(self, ctx, query):
        track = await wavelink.YouTubeTrack.search(query=query, return_first=True)
        self.player.queue.put(track)

    async def choose_track(self, ctx, query):
        tracks = await wavelink.YouTubeTrack.search(query=query)

        for t in tracks:
            print(t.id)

        def _check(r, u):
            return (
                r.emoji in OPTIONS.keys()
                and u == ctx.author
                and r.message.id == msg.id
            )

        embed = discord.Embed(
            title="",
            description=(
                "\n".join(
                    f"`{i+1}.` [{t.title}]({t.uri}) | `{self.convert(t.length)}`"
                    for i, t in enumerate(tracks[:5])
                )
            ),
            colour=ctx.author.colour,
        )
        embed.set_author(name="Choose a song")
        embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)
        
        msg = await ctx.send(embed=embed)
        for emoji in list(OPTIONS.keys())[:min(len(tracks), len(OPTIONS))]:
            await msg.add_reaction(emoji)
        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=_check)
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.message.delete()
        else:
            await msg.delete()
            self.player.queue.put(tracks[OPTIONS[reaction.emoji]])

    @commands.command()
    async def play(self, ctx, *, query: str):        
        if not ctx.voice_client:
            self.player: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            self.player: wavelink.Player = ctx.voice_client

        if not self.player.is_connected:
            await self.player.connect(ctx)

        query = query.strip("<>")
        if re.match(YOUTUBEPL_REGEX, query):
            await self.add_youtubepl(ctx, query)
        
        elif re.match(YOUTUBE_REGEX, query):
            await self.add_youtube(ctx, query)

        else:
            await self.choose_track(ctx, query)

        for q in self.player.queue:
            print(q.title)

        await self.player.play(self.player.queue.get())

def setup(bot):
    bot.add_cog(Music(bot))