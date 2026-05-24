from __future__ import annotations
from discord.ext import commands
from manager.handlers.player_manager import PlayerManager
from ui.views.queue_paginator import QueuePaginator
from utils.respond import Respond


class Queue(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="queue",
                             aliases=["q"],
                             description="View the current music queue.")
    async def queue(self, ctx: commands.Context):

        response = Respond(ctx=ctx)
        player = await PlayerManager.validate_player(ctx)
        if not player:
            return
        if player.queue.is_empty:
            current = player.current
            
            if current:
                embed = PlayerManager.build_now_playing(player, current)
                embed.description = ((embed.description or "") +
                                     "\n\n⚠️ No upcoming tracks in queue.")
                return await response.send(embed=embed)
            return await response.warning("Empty Queue",
                                          "There are no queued tracks.")

        # PAGINATOR
        view = QueuePaginator(player=player, author_id=ctx.author.id)
        embed = view.build_embed()
        await response.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Queue(bot))
