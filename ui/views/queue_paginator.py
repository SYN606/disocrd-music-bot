from __future__ import annotations
import discord
import wavelink
from config.emojis import EMOJIS
from manager.handlers.player_manager import PlayerManager


class QueuePaginator(discord.ui.View):

    def __init__(self, player: wavelink.Player, author_id: int):

        super().__init__(timeout=120)

        self.player = player
        self.author_id = author_id
        self.page = 0
        self.per_page = 10

    # VALIDATE USER
    async def interaction_check(self, interaction: discord.Interaction):

        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "You cannot control this queue.", ephemeral=True)
            return False
        return True

    # BUILD EMBED
    def build_embed(self):

        queue = list(self.player.queue)
        start = self.page * self.per_page
        end = start + self.per_page
        tracks = queue[start:end]
        embed = discord.Embed(color=0x5865F2)
        description = (f"{EMOJIS['queue']} "
                       f"**Music Queue**\n\n")
        current = self.player.current

        if current:
            description += (f"{EMOJIS['play']} "
                            f"**Now Playing**\n"
                            f"> {current.title}\n\n")

        if not tracks:
            description += (f"{EMOJIS['warning']} "
                            f"Queue is empty.")

        else:

            for index, track in enumerate(tracks, start=start + 1):
                duration = (PlayerManager.format_time(track.length))
                description += (f"`{index}.` "
                                f"{track.title}\n"
                                f"> {EMOJIS['waveform']} "
                                f"`{track.author}` "
                                f"• "
                                f"`{duration}`\n\n")

        embed.description = description
        total_pages = max(1, (len(queue) - 1) // self.per_page + 1)
        embed.set_footer(text=(f"Page "
                               f"{self.page + 1}/{total_pages} "
                               f"• "
                               f"{len(queue)} tracks queued"))

        return embed

    # PREVIOUS
    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction,
                            button: discord.ui.Button):
        self.page = max(0, self.page - 1)
        await interaction.response.edit_message(embed=self.build_embed(),
                                                view=self)

    # NEXT
    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction,
                        button: discord.ui.Button):

        queue = list(self.player.queue)
        max_page = max(0, (len(queue) - 1) // self.per_page)
        self.page = min(max_page, self.page + 1)
        await interaction.response.edit_message(embed=self.build_embed(),
                                                view=self)
