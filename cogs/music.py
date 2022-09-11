import wavelink, discord, asyncio, datetime, re
from .error import *
from wavelink.ext import spotify
from discord.ext import commands, pages
from config import *

#Config
template = {
    '__colour':discord.Colour.nitro_pink(),
}

class Music(commands.Cog, wavelink.Player):
    def __init__(self, bot):
        self.bot = bot
        self.player = None
        self.current_track = None
        bot.loop.create_task(self.start_nodes())

    def __thumbnail(self, identifier):
        return f"https://img.youtube.com/vi/{identifier}/0.jpg"

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
        nodes = {
            # "node1": {
            #     "bot": self.bot,
            #     "host": "node1.gglvxd.tk",
            #     "port": 443,
            #     "password": "free",
            #     "identifier": "pinkMusic1",
            #     "region": "asia",
            #     "https": True,
            # },
            "node2": {
                "bot": self.bot,
                "host": "lava.link",
                "port": 80,
                "password": "youshallnotpass",
                "identifier": "pinkMusic2",
                "region": "europe",
            },
        }

        for node in nodes.values():
            await wavelink.NodePool.create_node(**node)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f'[NODE] {node.identifier} connected.')

    @commands.Cog.listener("on_wavelink_track_exception")
    @commands.Cog.listener("on_wavelink_track_stuck")
    @commands.Cog.listener("on_wavelink_track_end")
    async def on_player_stop(self, *args, **kwargs):
        await self.start_playback()

    async def add_youtubepl(self, ctx, query):
        tracks = await wavelink.YouTubePlaylist.search(query=query)

        for t in tracks.tracks:
            self.player.queue.put(t)
        
        embed = discord.Embed(
            title=f"{tracks}",
            description=f"{len(tracks.tracks)} songs added to queue.",
            url=query,
            colour=template["__colour"],
        )
        embed.set_thumbnail(url=self.__thumbnail(tracks.tracks[0].identifier))
        embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)
        await ctx.send(embed=embed)
        await ctx.message.delete()

    async def add_youtube(self, ctx, query):
        track = await wavelink.YouTubeTrack.search(query=query, return_first=True)
        self.player.queue.put(track)

        embed = discord.Embed(
            title=f"{track.title}",
            description=f"added to queue.",
            url=track.uri,
            colour=template["__colour"],
        )
        embed.set_thumbnail(url=self.__thumbnail(track.identifier))
        embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)
        await ctx.send(embed=embed)
        await ctx.message.delete()

    async def choose_track(self, ctx, query):
        tracks = await wavelink.YouTubeTrack.search(query=query)

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
            colour=template["__colour"],
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
            track = tracks[OPTIONS[reaction.emoji]]
            self.player.queue.put(track)

        embed = discord.Embed(
            title=f"{track.title}",
            description=f"added to queue.",
            url=track.uri,
            colour=template["__colour"],
        )
        embed.set_thumbnail(url=self.__thumbnail(track.identifier))
        embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)
        await ctx.send(embed=embed)
        await ctx.message.delete()

    async def start_playback(self):
        self.current_track = self.player.queue.get()
        await self.player.play(self.current_track)

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

        if not self.player.is_playing() and not self.player.queue.is_empty:
            await self.start_playback()

    @commands.command(name='queue', aliases=['q'])
    async def queue_command(self, ctx):
        queue_page = []
        current = self.current_track
        song_list = ''
        upcoming = self.player.queue._queue

        i, p = 0, 0
        for track in upcoming:
            song_list = song_list + f"{i + 1}. [{track.title}]({track.uri}) | `{self.convert(track.length)}`\n\n"
            i = i + 1
            if i % 10 == 0:
                p = p + 1
                embed = discord.Embed(description=(f"**Now playing:**\n[{current.title}]({current.uri}) | `{self.convert(current.length)}`\n\n"
                                                   f"**Up next:**\n{song_list}"),
                                      colour=template["__colour"])
                embed.set_thumbnail(url=self.__thumbnail(current.identifier))
                embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)
                queue_page.append(embed)
                song_list = ''

        page_buttons = [
            pages.PaginatorButton("prev", emoji="◀️", style=discord.ButtonStyle.primary),
            pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True),
            pages.PaginatorButton("next", emoji="▶️", style=discord.ButtonStyle.primary),
        ]
        paginator = pages.Paginator(
            pages=queue_page,
            show_disabled=True,
            show_indicator=True,
            use_default_buttons=False,
            custom_buttons=page_buttons,
        )
        await paginator.send(ctx)

    @queue_command.error
    async def queue_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("The queue is currently empty.")

def setup(bot):
    bot.add_cog(Music(bot))