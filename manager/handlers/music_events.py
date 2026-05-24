from __future__ import annotations
from typing import cast
import discord
import wavelink
from discord.ext import commands
from manager.handlers.queue_manager import QueueManager


class MusicEvents(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # TRACK END
    @commands.Cog.listener()
    async def on_wavelink_track_end(self,
                                    payload: wavelink.TrackEndEventPayload):

        player = payload.player
        if not player:
            return

        next_track = await QueueManager.get_next(player)
        if next_track:
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
        if humans:
            return

        player.queue.clear()
        await player.disconnect()


async def setup(bot):
    await bot.add_cog(MusicEvents(bot))
