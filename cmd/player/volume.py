from __future__ import annotations
from typing import cast
import discord
import wavelink
from discord.ext import commands
from config.emojis import EMOJIS
from ui.views.volume_views import VolumeControls
from utils.respond import Respond


class Volume(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # GET PLAYER
    def get_player(self, ctx: commands.Context) -> wavelink.Player | None:
        return cast(wavelink.Player | None, ctx.voice_client)

    # VALIDATE PLAYER
    async def validate_player(self,
                              ctx: commands.Context) -> wavelink.Player | None:

        response = Respond(ctx=ctx)
        player = self.get_player(ctx)

        # NO PLAYER
        if not player:
            await response.warning("Nothing Playing",
                                   "No active player found.")
            return None

        # BOT NOT PLAYING
        if not player.playing:
            await response.warning("Nothing Playing",
                                   "The bot is not currently playing music.")

            return None
        member = cast(discord.Member, ctx.author)

        # USER NOT IN VC
        if not member.voice:
            await response.warning("Voice Channel Required",
                                   "You must join the voice channel first.")
            return None

        # BOT NOT IN VC
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

    # VOLUME
    @commands.hybrid_command(name="volume",
                             aliases=["vol"],
                             description="Control music volume.")
    async def volume(self, ctx: commands.Context, volume: int | None = None):
        response = Respond(ctx=ctx)
        player = await self.validate_player(ctx)
        if not player:
            return

        # OPEN UI
        if volume is None:
            embed = discord.Embed(color=0x5865F2)
            embed.description = (f"{EMOJIS['volume']} "
                                 f"**Volume Controller**\n\n"
                                 f"{EMOJIS['waveform']} "
                                 f"Current Volume\n"
                                 f"## `{player.volume}%`\n\n"
                                 f"{EMOJIS['music_player']} "
                                 f"Use the buttons below\n"
                                 f"to control playback volume")

            embed.set_footer(text="Volume changes by 2%")
            return await response.send(embed=embed, view=VolumeControls())

        # LIMITS
        volume = max(0, min(volume, 100))
        await player.set_volume(volume)
        embed = discord.Embed(color=0x5865F2)
        embed.description = (f"{EMOJIS['volume']} "
                             f"**Volume Updated**\n\n"
                             f"{EMOJIS['waveform']} "
                             f"Current Volume\n"
                             f"## `{volume}%`")
        embed.set_footer(text=(f"{EMOJIS['music_player']} "
                               f"DV-Music Audio System"))
        await response.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Volume(bot))
