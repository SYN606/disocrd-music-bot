from __future__ import annotations

import time
from typing import cast

import discord
import wavelink
from config.emojis import EMOJIS


class VolumeControls(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=120)
        # BUTTON COOLDOWNS
        self.cooldowns: dict[int, float] = {}

    # COOLDOWN CHECK
    def is_rate_limited(self, user_id: int) -> bool:
        now = time.time()

        last = self.cooldowns.get(user_id, 0)
        # 1.5s cooldown
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

    # VALIDATE PLAYER
    async def validate(
            self, interaction: discord.Interaction) -> wavelink.Player | None:
        player = self.get_player(interaction)

        if not player:
            await interaction.response.send_message(
                (f"{EMOJIS['fail']} "
                 f"No active player found."),
                ephemeral=True)
            return None

        member = cast(discord.Member, interaction.user)

        if not member.voice:
            await interaction.response.send_message(
                (f"{EMOJIS['warning']} "
                 f"You must join the voice channel first."),
                ephemeral=True)
            return None

        if not player.channel:
            await interaction.response.send_message(
                (f"{EMOJIS['warning']} "
                 f"Bot is not connected to voice."),
                ephemeral=True)
            return None

        if member.voice.channel.id != player.channel.id:  # type: ignore
            await interaction.response.send_message(
                (f"{EMOJIS['warning']} "
                 f"You must be in the same voice channel."),
                ephemeral=True)
            return None
        return player

    # BUILD EMBED
    def build_embed(self, volume: int):
        embed = discord.Embed(color=0x5865F2)
        embed.description = (f"{EMOJIS['volume']} "
                             f"**Volume Controller**\n\n"
                             f"{EMOJIS['waveform']} "
                             f"Current Volume\n"
                             f"## `{volume}%`\n\n"
                             f"{EMOJIS['music_player']} "
                             f"Use the buttons below\n"
                             f"to control playback volume")

        embed.set_footer(text="Volume changes by 2%")
        return embed

    # VOLUME DOWN
    @discord.ui.button(emoji="➖",
                       style=discord.ButtonStyle.secondary,
                       custom_id="volume_down")
    async def volume_down(self, interaction: discord.Interaction,
                          button: discord.ui.Button):
        if self.is_rate_limited(interaction.user.id):
            return await interaction.response.send_message(
                (f"{EMOJIS['warning']} "
                 f"Slow down a bit."), ephemeral=True)
        player = await self.validate(interaction)

        if not player:
            return

        new_volume = max(0, player.volume - 2)
        await player.set_volume(new_volume)
        embed = self.build_embed(new_volume)
        await interaction.response.edit_message(embed=embed, view=self)

    # VOLUME UP
    @discord.ui.button(emoji="➕",
                       style=discord.ButtonStyle.primary,
                       custom_id="volume_up")
    async def volume_up(self, interaction: discord.Interaction,
                        button: discord.ui.Button):
        if self.is_rate_limited(interaction.user.id):
            return await interaction.response.send_message(
                (f"{EMOJIS['warning']} "
                 f"Slow down a bit."), ephemeral=True)
        player = await self.validate(interaction)
        if not player:
            return

        new_volume = min(100, player.volume + 2)
        await player.set_volume(new_volume)
        embed = self.build_embed(new_volume)
        await interaction.response.edit_message(embed=embed, view=self)

    # MUTE
    @discord.ui.button(emoji="🔇",
                       style=discord.ButtonStyle.danger,
                       custom_id="volume_mute")
    async def mute(self, interaction: discord.Interaction,
                   button: discord.ui.Button):
        if self.is_rate_limited(interaction.user.id):
            return await interaction.response.send_message(
                (f"{EMOJIS['warning']} "
                 f"Slow down a bit."), ephemeral=True)
        player = await self.validate(interaction)
        if not player:
            return
        await player.set_volume(0)
        embed = self.build_embed(0)
        await interaction.response.edit_message(embed=embed, view=self)

    # MAX VOLUME
    @discord.ui.button(emoji=EMOJIS["volume"],
                       style=discord.ButtonStyle.success,
                       custom_id="volume_max")
    async def max_volume(self, interaction: discord.Interaction,
                         button: discord.ui.Button):
        if self.is_rate_limited(interaction.user.id):
            return await interaction.response.send_message(
                (f"{EMOJIS['warning']} "
                 f"Slow down a bit."), ephemeral=True)

        player = await self.validate(interaction)
        if not player:
            return
        await player.set_volume(100)
        embed = self.build_embed(100)
        await interaction.response.edit_message(embed=embed, view=self)

    # DISABLE ON TIMEOUT
    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
