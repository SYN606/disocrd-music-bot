from __future__ import annotations
import discord
import wavelink
from config.emojis import EMOJIS
from manager.handlers.queue_manager import QueueManager


class QueueControls(discord.ui.View):

    def __init__(self, player: wavelink.Player, track: wavelink.Playable,
                 requester_id: int):

        super().__init__(timeout=120)
        self.player = player
        self.track = track
        self.requester_id = requester_id

    # VALIDATE USER
    async def interaction_check(self, interaction: discord.Interaction):

        if interaction.user.id != self.requester_id:
            embed = discord.Embed(color=0x5865F2)
            embed.description = (f"{EMOJIS['warning']} "
                                 f"**Access Denied**\n\n"
                                 f"{EMOJIS['developer']} "
                                 f"Only the requester can remove this track.")
            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)

            return False
        return True

    # REMOVE TRACK
    @discord.ui.button(emoji=EMOJIS["fail"],
                       label="Remove",
                       style=discord.ButtonStyle.danger,
                       custom_id="queue_remove_track")
    async def remove_track(self, interaction: discord.Interaction,
                           button: discord.ui.Button):
        removed = QueueManager.remove_track(self.player, self.track)

        # TRACK NOT FOUND
        if not removed:

            embed = discord.Embed(color=0x5865F2)
            embed.description = (f"{EMOJIS['warning']} "
                                 f"**Track Missing**\n\n"
                                 f"{EMOJIS['queue']} "
                                 f"This track no longer exists in queue.")

            return await interaction.response.send_message(embed=embed,
                                                           ephemeral=True)

        # DISABLE BUTTON
        button.disabled = True
        embed = discord.Embed(color=0x5865F2)
        embed.description = (f"{EMOJIS['success']} "
                             f"**Track Removed**\n\n"
                             f"## {self.track.title}\n\n"
                             f"{EMOJIS['waveform']} "
                             f"`{self.track.author}`\n\n"
                             f"{EMOJIS['queue']} "
                             f"Successfully removed from queue.")

        if self.track.artwork:
            embed.set_thumbnail(url=self.track.artwork)
        embed.set_footer(text="DV-Music Queue Manager")
        await interaction.response.edit_message(embed=embed, view=self)

    # DISABLE BUTTONS ON TIMEOUT
    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
