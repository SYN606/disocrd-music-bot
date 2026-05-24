from __future__ import annotations
import discord
from discord.ext import commands
from config.emojis import EMOJIS
from manager.handlers.player_manager import PlayerManager
from ui.views.player_views import PlayerControls
from utils.respond import Respond


class NowPlaying(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # CLEANUP
    async def cleanup(self, ctx: commands.Context):
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.hybrid_command(name="nowplaying",
                             aliases=["np", "current"],
                             description="Show the current playing track.")
    async def nowplaying(self, ctx: commands.Context):
        await self.cleanup(ctx)
        response = Respond(ctx=ctx)
        player = await PlayerManager.validate_player(ctx)

        if not player:
            return
        track = player.current

        if not track:
            embed = discord.Embed(color=0x5865F2)
            embed.description = (f"{EMOJIS['warning']} "
                                 f"No active track is currently playing.")
            return await response.send(embed=embed)

        embed = PlayerManager.build_now_playing(player, track)

        queue_count = player.queue.count
        requester = "Unknown"

        try:
            requester_id = (track.extras.get("requester")
                            if isinstance(track.extras, dict) else getattr(
                                track.extras, "requester", None))

            if requester_id:
                requester = (f"<@{requester_id}>")
        except Exception:
            pass

        embed.description = ((embed.description or "") + "\n\n" +
                             (f"{EMOJIS['queue']} "
                              f"`{queue_count}` queued "
                              f"• "
                              f"{EMOJIS['volume']} "
                              f"`{player.volume}%`\n\n"
                              f"{EMOJIS['developer']} "
                              f"{requester}"))
                              
        view = PlayerControls(player=player, requester_id=ctx.author.id)
        message = await response.send(embed=embed, view=view)
        if isinstance(message, discord.Message):
            view.message = message

    # ERROR HANDLER
    @nowplaying.error
    async def nowplaying_error(self, ctx: commands.Context,
                               error: commands.CommandError):

        response = Respond(ctx=ctx)
        embed = discord.Embed(color=0x5865F2)
        embed.description = (f"{EMOJIS['warning']} "
                             f"Failed to fetch player information.\n\n"
                             f"`{str(error)[:120]}`")

        await response.send(embed=embed)


async def setup(bot):
    await bot.add_cog(NowPlaying(bot))
