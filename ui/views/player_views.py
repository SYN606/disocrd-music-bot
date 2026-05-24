from __future__ import annotations

from typing import cast

import discord
import wavelink

from config.emojis import EMOJIS
from manager.handlers.player_manager import PlayerManager


class PlayerControls(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

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
                                 f"**No Active Player**")

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

    # PAUSE / RESUME
    @discord.ui.button(emoji=EMOJIS["pause"],
                       style=discord.ButtonStyle.secondary,
                       custom_id="music_pause_resume")
    async def pause_resume(self, interaction: discord.Interaction,
                           button: discord.ui.Button):

        player = await self.validate(interaction)

        if not player:
            return

        # RESUME
        if player.paused:

            await player.pause(False)

            button.emoji = EMOJIS["pause"]

            embed = discord.Embed(color=0x5865F2)

            embed.description = (f"{EMOJIS['play']} "
                                 f"**Playback Resumed**")

            return await interaction.response.send_message(embed=embed,
                                                           ephemeral=True)

        # PAUSE
        await player.pause(True)

        button.emoji = EMOJIS["play"]

        embed = discord.Embed(color=0x5865F2)

        embed.description = (f"{EMOJIS['pause']} "
                             f"**Playback Paused**")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # SKIP
    @discord.ui.button(emoji=EMOJIS["skip"],
                       style=discord.ButtonStyle.primary,
                       custom_id="music_skip")
    async def skip(self, interaction: discord.Interaction,
                   button: discord.ui.Button):

        player = await self.validate(interaction)

        if not player:
            return

        current = player.current

        await player.skip()

        embed = discord.Embed(color=0x5865F2)

        embed.description = (f"{EMOJIS['skip']} "
                             f"Skipped "
                             f"**{current.title if current else 'track'}**")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # QUEUE
    @discord.ui.button(emoji=EMOJIS["queue"],
                       style=discord.ButtonStyle.success,
                       custom_id="music_queue")
    async def queue(self, interaction: discord.Interaction,
                    button: discord.ui.Button):

        player = await self.validate(interaction)

        if not player:
            return

        if player.queue.is_empty:

            embed = discord.Embed(color=0x5865F2)

            embed.description = (f"{EMOJIS['warning']} "
                                 f"Queue is empty.")

            return await interaction.response.send_message(embed=embed,
                                                           ephemeral=True)

        entries = []

        for index, track in enumerate(player.queue, start=1):

            entries.append(f"`{index}.` "
                           f"{track.title}")

            if index >= 10:
                break

        embed = discord.Embed(color=0x5865F2)

        embed.description = (f"{EMOJIS['queue']} "
                             f"**Current Queue**\n\n"
                             f"{chr(10).join(entries)}")

        embed.set_footer(text=f"{player.queue.count} tracks queued")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # STOP
    @discord.ui.button(emoji=EMOJIS["leave"],
                       style=discord.ButtonStyle.danger,
                       custom_id="music_leave")
    async def leave(self, interaction: discord.Interaction,
                    button: discord.ui.Button):

        player = await self.validate(interaction)

        if not player:
            return

        player.queue.clear()

        await player.disconnect()

        embed = discord.Embed(color=0x5865F2)

        embed.description = (f"{EMOJIS['leave']} "
                             f"Disconnected from voice channel.")

        await interaction.response.send_message(embed=embed, ephemeral=True)
