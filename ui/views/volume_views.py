from __future__ import annotations
import time
from typing import cast
import discord
import wavelink
from config.emojis import EMOJIS


class VolumeControls(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=120)
        self.cooldowns: dict[int, float] = {}

    # RATE LIMIT
    def is_rate_limited(self, user_id: int) -> bool:
        now = time.time()
        last = self.cooldowns.get(user_id, 0)
        if now - last < 1.5:
            return True
        self.cooldowns[user_id] = now
        return False

    # GET PLAYER
    def get_player(self,
                   interaction: discord.Interaction) -> wavelink.Player | None:

        return cast(
            wavelink.Player | None,
            interaction.guild.voice_client if interaction.guild else None)

    # VALIDATE
    async def validate(
            self, interaction: discord.Interaction) -> wavelink.Player | None:
        player = self.get_player(interaction)
        if not player:

            embed = discord.Embed(color=0x5865F2)
            embed.description = (f"{EMOJIS['fail']} "
                                 f"No active player found.")
            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)
            return None

        member = cast(discord.Member, interaction.user)
        if not member.voice:
            embed = discord.Embed(color=0x5865F2)
            embed.description = (f"{EMOJIS['warning']} "
                                 f"Join a voice channel first.")
            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)
            return None
        if not player.channel:
            return None

        if member.voice.channel.id != player.channel.id:  # type: ignore
            embed = discord.Embed(color=0x5865F2)
            embed.description = (f"{EMOJIS['warning']} "
                                 f"You must be in the same voice channel.")
            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)
            return None
        return player

    # BUILD EMBED
    def build_embed(self, volume: int):
        embed = discord.Embed(color=0x5865F2)
        embed.description = (f"{EMOJIS['volume']} "
                             f"**Volume Controller**\n\n"
                             f"## `{volume}%`")

        return embed

    # VOLUME DOWN
    @discord.ui.button(emoji="➖", style=discord.ButtonStyle.secondary)
    async def volume_down(self, interaction: discord.Interaction,
                          button: discord.ui.Button):
        if self.is_rate_limited(interaction.user.id):
            return
        player = await self.validate(interaction)
        if not player:
            return

        new_volume = max(0, player.volume - 2)
        await player.set_volume(new_volume)
        embed = self.build_embed(new_volume)
        await interaction.response.edit_message(embed=embed, view=self)

    # VOLUME UP
    @discord.ui.button(emoji="➕", style=discord.ButtonStyle.primary)
    async def volume_up(self, interaction: discord.Interaction,
                        button: discord.ui.Button):

        if self.is_rate_limited(interaction.user.id):
            return

        player = await self.validate(interaction)
        if not player:
            return

        new_volume = min(100, player.volume + 2)
        await player.set_volume(new_volume)
        embed = self.build_embed(new_volume)
        await interaction.response.edit_message(embed=embed, view=self)

    # MUTE
    @discord.ui.button(emoji="🔇", style=discord.ButtonStyle.danger)
    async def mute(self, interaction: discord.Interaction,
                   button: discord.ui.Button):
        player = await self.validate(interaction)

        if not player:
            return

        await player.set_volume(0)
        embed = self.build_embed(0)
        await interaction.response.edit_message(embed=embed, view=self)

    # MAX
    @discord.ui.button(emoji=EMOJIS["volume"],
                       style=discord.ButtonStyle.success)
    async def max_volume(self, interaction: discord.Interaction,
                         button: discord.ui.Button):
        player = await self.validate(interaction)
        if not player:
            return

        await player.set_volume(100)
        embed = self.build_embed(100)
        await interaction.response.edit_message(embed=embed, view=self)
