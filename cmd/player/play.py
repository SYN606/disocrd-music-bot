from __future__ import annotations

from typing import cast

import discord
import wavelink
from discord.ext import commands

from config.emojis import EMOJIS
from config.settings import DEFAULT_VOLUME
from ui.views.player_views import PlayerControls
from utils.respond import Respond


class Player(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # GET / CREATE PLAYER
    async def get_player(self,
                         ctx: commands.Context) -> wavelink.Player | None:

        response = Respond(ctx=ctx)

        member = cast(discord.Member, ctx.author)

        # USER NOT IN VC
        if not member.voice:

            await response.warning("Voice Channel Required",
                                   "You must join a voice channel first.")

            return None

        channel = member.voice.channel

        if channel is None:

            await response.warning("Voice Channel Required",
                                   "You must join a voice channel first.")

            return None

        player = cast(wavelink.Player | None, ctx.voice_client)

        # CONNECT
        if player is None:

            player = await channel.connect(cls=wavelink.Player, self_deaf=True)

            await player.set_volume(DEFAULT_VOLUME)

        return player

    # FORMAT TIME
    def format_time(self, milliseconds: int) -> str:
        seconds = milliseconds // 1000
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:

            return (f"{hours}:"
                    f"{minutes:02}:"
                    f"{seconds:02}")
        return (f"{minutes}:"
                f"{seconds:02}")

    # PROGRESS BAR
    def progress_bar(self, position: int, length: int, size: int = 16) -> str:
        if length <= 0:
            return "─" * size
        filled = int((position / length) * size)
        filled = min(filled, size - 1)
        bar = ""
        for index in range(size):

            if index == filled:
                bar += "🔘"
            else:
                bar += "─"
        return bar

    # NOW PLAYING EMBED
    def build_now_playing(self, player: wavelink.Player,
                          track: wavelink.Playable):

        position = getattr(player, "position", 0)
        progress = self.progress_bar(position, track.length)
        requester = (
            f"<@{track.extras.requester}>" if hasattr(track, "extras")
            and getattr(track.extras, "requester", None) else "Unknown")

        queue_count = player.queue.count
        embed = discord.Embed(color=0x5865F2)
        embed.description = (f"{EMOJIS['music_player']} "
                             f"**DV-Music Player**\n\n"
                             f"# {track.title}\n"
                             f"> {EMOJIS['waveform']} {track.author}\n\n"
                             f"{EMOJIS['play']} "
                             f"`{self.format_time(position)}` "
                             f"{progress} "
                             f"`{self.format_time(track.length)}`\n\n"
                             f"{EMOJIS['queue']} "
                             f"`{queue_count}` queued "
                             f"• "
                             f"{EMOJIS['volume']} "
                             f"`{player.volume}%`\n\n"
                             f"{EMOJIS['developer']} "
                             f"Requested by {requester}")

        if track.artwork:
            embed.set_thumbnail(url=track.artwork)
        embed.set_footer(text="Use the buttons below to control playback")

        return embed

    # PLAY
    @commands.hybrid_command(name="play",
                             aliases=["p"],
                             description="Play a song or playlist.")
    async def play(self, ctx: commands.Context, *, query: str):
        response = Respond(ctx=ctx)
        player = await self.get_player(ctx)
        if not player:
            return
        loading = await response.raw(f"{EMOJIS['rounded_loading']} "
                                     f"Searching for tracks...")

        # SMART SEARCH
        if ("youtube.com" in query or "youtu.be" in query):
            search_query = query

        elif "spotify.com" in query:
            search_query = query

        else:

            search_query = (f"ytsearch:{query}")
        tracks = await wavelink.Playable.search(search_query)

        # NO RESULTS
        if not tracks:
            return await response.error("No Results", "No tracks were found.")

        # PLAYLIST
        if isinstance(tracks, wavelink.Playlist):
            added = 0

            for track in tracks.tracks:
                track.extras = {"requester": ctx.author.id}
                player.queue.put(track)
                added += 1
            embed = discord.Embed(color=0x5865F2)
            embed.description = (
                f"# {EMOJIS['music_player']} Playlist Added\n\n"
                f"## {tracks.name}\n\n"
                f"{EMOJIS['queue']} "
                f"Added `{added}` tracks\n\n"
                f"{EMOJIS['developer']} "
                f"Requested by {ctx.author.mention}")

            if tracks.artwork:
                embed.set_thumbnail(url=tracks.artwork)

            if isinstance(loading, discord.Message):
                await loading.edit(content=None, embed=embed)

            else:
                await response.send(embed=embed)

            # START PLAYBACK
            if not player.playing:
                next_track = await player.queue.get_wait()
                await player.play(next_track)

            return

        # SINGLE TRACK
        track = tracks[0]
        # REQUESTER
        track.extras = {"requester": ctx.author.id}
        if player.playing:

            player.queue.put(track)
            embed = discord.Embed(color=0x5865F2)
            embed.description = (f"# {EMOJIS['queue']} Added To Queue\n\n"
                                 f"## {track.title}\n"
                                 f"> {EMOJIS['waveform']} {track.author}\n\n"
                                 f"{EMOJIS['play']} "
                                 f"`{self.format_time(track.length)}`\n\n"
                                 f"{EMOJIS['developer']} "
                                 f"Requested by {ctx.author.mention}")

            if track.artwork:
                embed.set_thumbnail(url=track.artwork)

            if isinstance(loading, discord.Message):
                await loading.edit(content=None, embed=embed)

            else:
                await response.send(embed=embed)
            return

        # PLAY
        await player.play(track)
        embed = self.build_now_playing(player, track)
        if isinstance(loading, discord.Message):
            await loading.edit(content=None,
                               embed=embed,
                               view=PlayerControls())

        else:
            await response.send(embed=embed, view=PlayerControls())

    # PAUSE
    @commands.hybrid_command(name="pause", description="Pause playback.")
    async def pause(self, ctx: commands.Context):
        response = Respond(ctx=ctx)
        player = cast(wavelink.Player | None, ctx.voice_client)
        if not player or not player.playing:
            return await response.warning("Nothing Playing",
                                          "There is no active track.")

        if player.paused:
            return await response.warning("Already Paused",
                                          "Playback is already paused.")

        await player.pause(True)
        await response.success("Playback Paused",
                               "Music playback has been paused.")

    # RESUME
    @commands.hybrid_command(name="resume", description="Resume playback.")
    async def resume(self, ctx: commands.Context):
        response = Respond(ctx=ctx)
        player = cast(wavelink.Player | None, ctx.voice_client)

        if not player:
            return await response.warning("Nothing Playing",
                                          "No active player found.")

        if not player.paused:
            return await response.warning("Not Paused",
                                          "Playback is not paused.")

        await player.pause(False)
        await response.success("Playback Resumed",
                               "Music playback has resumed.")

    # SKIP
    @commands.hybrid_command(name="skip",
                             aliases=["next"],
                             description="Skip current track.")
    async def skip(self, ctx: commands.Context):
        response = Respond(ctx=ctx)
        player = cast(wavelink.Player | None, ctx.voice_client)

        if not player or not player.playing:
            return await response.warning("Nothing Playing",
                                          "There is no track to skip.")

        current = player.current
        if current is None:
            return await response.warning("Nothing Playing",
                                          "No active track found.")

        await player.skip()
        await response.success("Track Skipped", f"Skipped **{current.title}**")

    # STOP
    @commands.hybrid_command(name="stop", description="Stop playback.")
    async def stop(self, ctx: commands.Context):
        response = Respond(ctx=ctx)
        player = cast(wavelink.Player | None, ctx.voice_client)
        if not player:
            return await response.warning("Nothing Playing",
                                          "No active player found.")

        player.queue.clear()
        await player.disconnect()
        await response.success("Playback Stopped",
                               "Disconnected from voice channel.")

    # TRACK END
    @commands.Cog.listener()
    async def on_wavelink_track_end(self,
                                    payload: wavelink.TrackEndEventPayload):
        player = payload.player
        if not player:
            return

        if not player.queue.is_empty:
            next_track = await player.queue.get_wait()
            await player.play(next_track)

    # AUTO DISCONNECT
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member,
                                    before: discord.VoiceState,
                                    after: discord.VoiceState):

        if member.bot:
            return

        if not before.channel:
            return

        voice_client = before.channel.guild.voice_client
        player = cast(wavelink.Player | None, voice_client)
        if not player:
            return

        humans = [m for m in before.channel.members if not m.bot]
        if not humans:
            player.queue.clear()
            await player.disconnect()


async def setup(bot):
    await bot.add_cog(Player(bot))
