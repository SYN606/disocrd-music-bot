from __future__ import annotations
from discord.ext import commands
from config.emojis import EMOJIS
from manager.handlers.player_manager import PlayerManager
from ui.views.player_views import PlayerControls
from utils.respond import Respond


class NowPlaying(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="nowplaying",
                             aliases=["np", "current"],
                             description="Show the current playing track.")
    async def nowplaying(self, ctx: commands.Context):
        response = Respond(ctx=ctx)
        player = await PlayerManager.validate_player(ctx)

        if not player:
            return

        # CURRENT TRACK
        track = player.current
        if not track:
            return await response.warning("Nothing Playing",
                                          "There is no active track.")

        embed = PlayerManager.build_now_playing(player, track)
        view = PlayerControls()
        await response.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(NowPlaying(bot))
