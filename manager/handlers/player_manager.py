from __future__ import annotations
from typing import cast
import discord
import wavelink
from config.emojis import EMOJIS
from config.settings import DEFAULT_VOLUME
from utils.respond import Respond


class PlayerManager:
    # GET / CREATE PLAYER
    @staticmethod
    async def get_player(ctx) -> wavelink.Player | None:
        response = Respond(ctx=ctx)
        member = cast(discord.Member, ctx.author)
        # USER NOT IN VC
        if not member.voice:
            await response.warning("Voice Channel Required",
                                   "You must join a voice channel first.")
            return None
        channel = member.voice.channel
        if channel is None:
            return None
        player = cast(wavelink.Player | None, ctx.voice_client)

        # CONNECT BOT
        if player is None:
            player = await channel.connect(cls=wavelink.Player, self_deaf=True)
            await player.set_volume(DEFAULT_VOLUME)
        return player

    # VALIDATE ACTIVE PLAYER
    @staticmethod
    async def validate_player(ctx) -> wavelink.Player | None:
        response = Respond(ctx=ctx)
        player = cast(wavelink.Player | None, ctx.voice_client)
        if not player:
            await response.warning("Nothing Playing",
                                   "No active player found.")
            return None

        member = cast(discord.Member, ctx.author)

        # USER NOT IN VC
        if not member.voice:
            await response.warning("Voice Channel Required",
                                   "You must join a voice channel first.")
            return None

        # PLAYER NO CHANNEL
        if not player.channel:
            await response.warning("Voice Channel Missing",
                                   "Bot is not connected to a voice channel.")
            return None

        # DIFFERENT VC
        if member.voice.channel.id != player.channel.id:  # type: ignore
            await response.warning(
                "Wrong Voice Channel",
                "You must be in the same voice channel as the bot.")

            return None
        return player

    # FORMAT TIME
    @staticmethod
    def format_time(milliseconds: int) -> str:
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
    @staticmethod
    def progress_bar(position: int, length: int, size: int = 14) -> str:
        if length <= 0:
            return "─" * size
        filled = int((position / length) * size)
        filled = min(filled, size - 1)
        bar = ""
        for index in range(size):
            if index == filled:
                bar += "◉"
            else:
                bar += "─"
        return bar

    # BUILD PLAYER EMBED
    @staticmethod
    def build_now_playing(player: wavelink.Player,
                          track: wavelink.Playable) -> discord.Embed:
        position = getattr(player, "position", 0)
        progress = PlayerManager.progress_bar(position, track.length)
        requester = (
            f"<@{track.extras.requester}>" if hasattr(track, "extras")
            and getattr(track.extras, "requester", None) else "Unknown")
        queue_count = player.queue.count
        embed = discord.Embed(color=0x5865F2)
        embed.description = (f"{EMOJIS['music_player']} "
                             f"**Now Playing**\n\n"
                             f"## {track.title}\n"
                             f"{EMOJIS['waveform']} "
                             f"`{track.author}`\n\n"
                             f"`{PlayerManager.format_time(position)}` "
                             f"{progress} "
                             f"`{PlayerManager.format_time(track.length)}`\n\n"
                             f"{EMOJIS['queue']} "
                             f"`{queue_count}` queued "
                             f"• "
                             f"{EMOJIS['volume']} "
                             f"`{player.volume}%`\n\n"
                             f"{EMOJIS['developer']} "
                             f"{requester}")

        # THUMBNAIL
        artwork = getattr(track, "artwork", None)
        if artwork:
            embed.set_thumbnail(url=artwork)
        embed.set_footer(text="DV-Music Player")
        return embed

    # BUILD QUEUE EMBED
    @staticmethod
    def build_queue_embed(player: wavelink.Player) -> discord.Embed:
        embed = discord.Embed(color=0x5865F2)
        if player.queue.is_empty:
            embed.description = (f"{EMOJIS['warning']} "
                                 f"Queue is empty.")
            return embed
        entries = []
        for index, track in enumerate(player.queue, start=1):
            entries.append(f"`{index}.` "
                           f"{track.title}")
            if index >= 10:
                break
        embed.description = (f"{EMOJIS['queue']} "
                             f"**Current Queue**\n\n"
                             f"{chr(10).join(entries)}")

        embed.set_footer(text=f"{player.queue.count} tracks queued")
        return embed
