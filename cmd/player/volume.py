from __future__ import annotations

import discord
import wavelink
from discord.ext import commands

from config.emojis import EMOJIS
from manager.handlers.player_manager import PlayerManager
from ui.views.volume_views import VolumeControls
from utils.respond import Respond


class Volume(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # VOLUME
    @commands.hybrid_command(name="volume",
                             aliases=["vol"],
                             description="Control music volume.")
    async def volume(self, ctx: commands.Context, volume: int | None = None):

        response = Respond(ctx=ctx)

        # VALIDATE PLAYER
        player = await PlayerManager.validate_player(ctx)

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
                                 f"Use the buttons below to\n"
                                 f"adjust playback volume")

            embed.set_footer(text="Volume changes by 2%")

            return await response.send(embed=embed, view=VolumeControls())

        # LIMIT RANGE
        volume = max(0, min(volume, 100))

        # SET VOLUME
        await player.set_volume(volume)

        # EMBED
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
