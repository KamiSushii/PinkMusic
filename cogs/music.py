import wavelink, discord, asyncio, datetime, re
from .error import *
from wavelink.ext import spotify
from discord.ext import commands, pages
from config import *

temp = None

class loopMode():
    NONE = ''
    ONE  = '| 🔂 '
    ALL  = '| 🔁 '

class shuffleMode():
    NO  = ''
    YES = '| 🔀 '

class Control(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    async def _check(self, interaction):
        if interaction.guild.voice_client is None:
            await interaction.response.send_message('❌ I am not playing any songs for you.',ephemeral=True, delete_after=10)
            return False

        elif interaction.user.voice is None:
            await interaction.response.send_message(f'❌ {interaction.user.mention}, You have to be connected to a voice channel.',ephemeral=True, delete_after=10)
            return False

        elif interaction.user.voice.channel.id != interaction.guild.voice_client.channel.id:
            await interaction.response.send_message('❌ You are in the wrong channel.',ephemeral=True, delete_after=10)
            return False

        else:
            return True

    @discord.ui.button(label='', style=discord.ButtonStyle.primary,emoji="<:pause:1014645688417660999>")
    async def pause(self, button: discord.ui.Button, interaction: discord.Interaction):
        try :
            self.timeout=None
            if not await self._check(interaction):
                return

            if not interaction.guild.voice_client.is_paused():
                await interaction.guild.voice_client.pause()
                return await interaction.response.send_message('✔️ Successfully paused.',ephemeral=True, delete_after=10)
            else:
                await interaction.guild.voice_client.resume()
                await interaction.response.send_message('✔️ Successfully resumed.',ephemeral=True, delete_after=10)

        except:
            self.timeout=None
            pass
    
    @discord.ui.button(label='', style=discord.ButtonStyle.primary,emoji="<:skip:1014645693102694470>")
    async def skip(self, button: discord.ui.Button, interaction: discord.Interaction):
        try :
            if not await self._check(interaction):
                return

            await interaction.guild.voice_client.stop()
            await interaction.response.send_message('✔️ Successfully skipped.', delete_after=3)

            global temp
            await asyncio.sleep(3)
            await Music.control_command(temp)
        except:
            self.timeout=None
            pass
        
    @discord.ui.button(label='', style=discord.ButtonStyle.red,emoji="<:stop:1014645696718184478>")
    async def stop(self, button: discord.ui.Button, interaction: discord.Interaction):
        try :
            if not await self._check(interaction):
                return


            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message('✔️ Successfully disconnected.',ephemeral=True, delete_after=10)

        except:
            self.timeout=None
            pass
    
    @discord.ui.button(label='', style=discord.ButtonStyle.primary,emoji="<:loop:1014645681329295411>")
    async def loop(self, button: discord.ui.Button, interaction: discord.Interaction):
        try :
            self.timeout=None

            if not await self._check(interaction):
                return

            if Music.loop == loopMode.NONE:
                Music.loop = loopMode.ALL
                await interaction.response.send_message('🔁 Queue loop enabled!',ephemeral=True, delete_after=10)
            elif Music.loop == loopMode.ALL:
                Music.loop = loopMode.ONE
                await interaction.response.send_message('🔂 Current track loop enabled!',ephemeral=True, delete_after=10)
            else:
                Music.loop = loopMode.NONE
                await interaction.response.send_message('❌ Loop disabled!',ephemeral=True, delete_after=10)

            await Music.control_command(self.ctx)
        except:
            self.timeout=None
            pass

    @discord.ui.button(label='', style=discord.ButtonStyle.primary,emoji="<:shuffle:1014645684764422224>")
    async def shuffle(self, button: discord.ui.Button, interaction: discord.Interaction):
        try :
            self.timeout=None
            global queues
            global all_queues_info

            if not await self._check(interaction):
                return

            if Music.shuffle == loopMode.NONE:
                Music.shuffle = loopMode.ALL
                await interaction.response.send_message('🔁 Shuffle enabled!',ephemeral=True, delete_after=10)
            else:
                Music.shuffle = loopMode.NONE
                await interaction.response.send_message('❌ Shuffle disabled!',ephemeral=True, delete_after=10)

            if interaction.guild.id not in all_queues_info or len(all_queues_info[interaction.guild.id]) == 0:
                return await interaction.response.send_message('❌ Your queue is empty!',ephemeral=True, delete_after=10)
        except:
            self.timeout=None
            pass

class Music(commands.Cog, wavelink.Player):
    def __init__(self, bot):
        self.bot = bot

        self.player = None
        self.ctrl = None
        self.current_track = None

        self.loop = loopMode.NONE
        self.shuffle = shuffleMode.NO
        self.temp = None

        bot.loop.create_task(self.start_nodes())

    def __thumbnail(self, identifier):
        return f"https://img.youtube.com/vi/{identifier}/0.jpg"

    def progress(self, position, duration):
        progress = position / duration * 100
        if progress < 10:   return '●---------'
        elif progress < 20: return '-●--------'
        elif progress < 30: return '--●-------'
        elif progress < 40: return '---●------'
        elif progress < 50: return '----●-----'
        elif progress < 60: return '-----●----'
        elif progress < 70: return '------●---'
        elif progress < 80: return '-------●--'
        elif progress < 90: return '--------●-'
        elif progress < 100: return '--------●'


    def convert(self, sec):
        if sec < 60:
            return f"0:{str(datetime.timedelta(seconds = int(sec))).lstrip('0:')}"
        else:
            return str(datetime.timedelta(seconds = int(sec))).lstrip('0:')

    async def teardown(self):
        try:
            await self.player.destroy()
        except KeyError:
            pass

    async def connect(self, ctx):
        if not ctx.voice_client:
            self.player: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            self.player: wavelink.Player = ctx.voice_client

        if not self.player.is_connected:
            await self.player.connect(ctx)
    
    async def start_nodes(self):
        await self.bot.wait_until_ready()
        for node in nodes.values():
            await wavelink.NodePool.create_node(bot=self.bot, **node)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f'[NODE] {node.identifier} connected.')

    @commands.Cog.listener("on_wavelink_track_exception")
    @commands.Cog.listener("on_wavelink_track_stuck")
    @commands.Cog.listener("on_wavelink_track_end")
    async def on_player_stop(self, *args, **kwargs):
        await self.start_playback()


# Adding music to queue
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
        if not self.player.queue.is_empty:
            self.current_track = self.player.queue.get()
            await self.player.play(self.current_track)


# Bot Commands
    @commands.command(name='shutdown', aliases=['kill'])
    async def shutdown_command(self, ctx):
        await self.player.disconnect()

    @commands.command(name='control', aliases=['ctrl', 'np'])
    async def control_command(self, ctx):
        view = Control()
        current = self.current_track
        embed = discord.Embed(
            description=f"**Now playing:**\n"
                        f"[{current.title}]({current.uri})\n"
                        f"`{self.convert(self.player.position)} |{self.progress(self.player.position, current.duration)}| {self.convert(current.duration)}`",
            colour=template["__colour"]
        )
        embed.set_thumbnail(url=self.__thumbnail(current.identifier))
        embed.set_footer(text=f"{self.loop}{self.shuffle}", icon_url=ctx.author.display_avatar)

        global temp
        temp = ctx
        if self.ctrl is not None:
            await self.ctrl.delete()
        self.ctrl = await ctx.send(embed=embed, view=view)

    @commands.command(name='play', aliases=['p'])
    async def play_command(self, ctx, *, query: str):
        await self.connect(ctx)
        query = query.strip("<>")
        if re.match(YOUTUBEPL_REGEX, query):
            await self.add_youtubepl(ctx, query)
        
        elif re.match(YOUTUBE_REGEX, query):
            await self.add_youtube(ctx, query)

        else:
            await self.choose_track(ctx, query)

        if not self.player.is_playing() and not self.player.queue.is_empty:
            await self.start_playback()

    @commands.command(name='skip', aliases=['next'])
    async def skip_command(self, ctx):
        await self.player.stop()
        await ctx.send("Song skipped")

    @play_command.error
    async def play_command_error(self, ctx, exc):
        await ctx.send("error")

    @commands.command(name='queue', aliases=['q'])
    async def queue_command(self, ctx):
        queue_page = []
        song_list = ''
        current = self.current_track
        upcoming = self.player.queue._queue

        i= 0
        for track in upcoming:
            song_list = song_list + f"{i + 1}. [{track.title}]({track.uri}) | `{self.convert(track.length)}`\n\n"
            i = i + 1
            if i % 10 == 0:
                embed = discord.Embed(
                    description=(f"**Now playing:**"
                                f"\n[{current.title}]({current.uri}) | `{self.convert(current.length)}`\n\n"
                                f"**Up next:**\n{song_list}"),
                    colour=template["__colour"])
                embed.set_thumbnail(url=self.__thumbnail(current.identifier))
                embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)
                queue_page.append(embed)
                song_list = ''

        if i % 10 != 0 or i == 0:
            embed = discord.Embed(
                description=(f"**Now playing:**"
                            f"\n[{current.title}]({current.uri}) | `{self.convert(current.length)}`\n\n"
                            f"**Up next:**\n{song_list}"),
                colour=template["__colour"])
            embed.set_thumbnail(url=self.__thumbnail(current.identifier))
            embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)
            queue_page.append(embed)

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

    @commands.command(name='history', aliases=['ht'])
    async def history_command(self, ctx):
        history_page = []
        song_list = ''
        history = self.player.queue.history

        i= 0
        for track in history:
            song_list = song_list + f"{i + 1}. [{track.title}]({track.uri}) | `{self.convert(track.length)}`\n\n"
            i = i + 1
            if i % 10 == 0:
                embed = discord.Embed(
                    description=f"**History:**\n{song_list}",
                    colour=template["__colour"])
                embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)
                history_page.append(embed)
                song_list = ''

        if i % 10 != 0 or i == 0:
            embed = discord.Embed(
                    description=f"**History:**\n{song_list}",
                    colour=template["__colour"])
            embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)
            history_page.append(embed)

        page_buttons = [
            pages.PaginatorButton("prev", emoji="◀️", style=discord.ButtonStyle.primary),
            pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True),
            pages.PaginatorButton("next", emoji="▶️", style=discord.ButtonStyle.primary),
        ]
        paginator = pages.Paginator(
            pages=history_page,
            show_disabled=True,
            show_indicator=True,
            use_default_buttons=False,
            custom_buttons=page_buttons,
        )
        await paginator.send(ctx)


def setup(bot):
    bot.add_cog(Music(bot))