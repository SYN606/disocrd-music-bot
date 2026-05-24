from __future__ import annotations
import discord
import wavelink
from discord.ext import commands
from config.emojis import EMOJIS
from manager.handlers.player_manager import PlayerManager
from manager.handlers.queue_manager import QueueManager
from ui.views.player_views import PlayerControls
from ui.views.queue_views import QueueControls
from utils.respond import Respond


class Player(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # PLAY
    @commands.hybrid_command(name="play",
                             aliases=["p"],
                             description="Play a song or playlist.")
    async def play(self, ctx: commands.Context, *, query: str):
        response = Respond(ctx=ctx)

        player = await PlayerManager.get_player(ctx)
        if not player:
            return

        loading = await response.raw(f"{EMOJIS['rounded_loading']} "
                                     f"Searching for tracks...")

        query = " ".join(query.strip().split())

        garbage = ("(lyrics)", "[lyrics]", "lyrics", "official video",
                   "official audio", "audio", "video")
        cleaned = query.lower()
        for item in garbage:
            cleaned = cleaned.replace(item, "")
        query = cleaned.strip()
        try:
            if query.startswith(("http://", "https://")):
                result = await wavelink.Playable.search(query)
            else:
                result = await wavelink.Playable.search(f"ytmsearch:{query}")

                if not result:
                    result = await wavelink.Playable.search(f"ytsearch:{query}"
                                                            )

        except Exception:
            return await response.error("Search Failed",
                                        "Failed to fetch search results.")

        if not result:
            return await response.warning("No Results",
                                          "No matching tracks were found.")
        if isinstance(result, wavelink.Playlist):
            added = 0
            for track in result.tracks:
                track.extras = {"requester": ctx.author.id}
                await QueueManager.add_track(player, track)
                added += 1

            embed = discord.Embed(color=0x5865F2)
            embed.description = (f"{EMOJIS['playlist']} "
                                 f"**Playlist Added**\n\n"
                                 f"## {result.name}\n\n"
                                 f"{EMOJIS['queue']} "
                                 f"`{added}` tracks queued\n\n"
                                 f"{EMOJIS['developer']} "
                                 f"{ctx.author.mention}")
            artwork = getattr(result, "artwork", None)

            if artwork:
                embed.set_thumbnail(url=artwork)

            if loading:
                await loading.edit(content=None, embed=embed)  # type: ignore

            else:
                await response.send(embed=embed)

            if not player.playing:
                next_track = await QueueManager.get_next(player)
                if next_track:
                    await player.play(next_track)

            return
        track = (result[0] if isinstance(result, list) else result)

        if not track:
            return await response.warning("No Results",
                                          "No playable track found.")

        track.extras = {"requester": ctx.author.id}
        if player.playing:
            await QueueManager.add_track(player, track)
            embed = discord.Embed(color=0x5865F2)
            embed.description = (
                f"{EMOJIS['queue']} "
                f"**Added To Queue**\n\n"
                f"## {track.title}\n"
                f"{EMOJIS['waveform']} "
                f"`{track.author}`\n\n"
                f"{EMOJIS['play']} "
                f"`{PlayerManager.format_time(track.length)}`\n\n"
                f"{EMOJIS['developer']} "
                f"{ctx.author.mention}")
            artwork = getattr(track, "artwork", None)
            if artwork:
                embed.set_thumbnail(url=artwork)
            view = QueueControls(player=player,
                                 track=track,
                                 requester_id=ctx.author.id)
            if loading:
                await loading.edit(content=None, embed=embed, view=view) # type: ignore

            else:
                await response.send(embed=embed, view=view)
            return
        await player.play(track)
        embed = PlayerManager.build_now_playing(player, track)
        view = PlayerControls()
        if loading:
            await loading.edit(content=None, embed=embed, view=view) # type: ignore
        else:
            await response.send(embed=embed, view=view)

    # PAUSE
    @commands.hybrid_command(name="pause", description="Pause playback.")
    async def pause(self, ctx: commands.Context):

        response = Respond(ctx=ctx)

        player = await PlayerManager.validate_player(ctx)

        if not player:
            return

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

        player = await PlayerManager.validate_player(ctx)

        if not player:
            return

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

        player = await PlayerManager.validate_player(ctx)

        if not player:
            return

        current = player.current

        if not current:

            return await response.warning("Nothing Playing",
                                          "No active track found.")

        await player.skip()

        await response.success("Track Skipped", f"Skipped **{current.title}**")

    # STOP
    @commands.hybrid_command(name="stop", description="Stop playback.")
    async def stop(self, ctx: commands.Context):

        response = Respond(ctx=ctx)

        player = await PlayerManager.validate_player(ctx)

        if not player:
            return

        QueueManager.clear(player)

        await player.disconnect()

        await response.success("Playback Stopped",
                               "Disconnected from voice channel.")


async def setup(bot):

    await bot.add_cog(Player(bot))
