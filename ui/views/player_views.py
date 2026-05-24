from __future__ import annotations
from typing import cast
import discord
import wavelink
from config.emojis import EMOJIS


class PlayerControls(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    # GET PLAYER
    def get_player(self,
                   interaction: discord.Interaction) -> wavelink.Player | None:
        return cast(
            wavelink.Player | None,
            interaction.guild.voice_client if interaction.guild else None)

    # VALIDATE VC
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
                                 f"**Playback Resumed**\n\n"
                                 f"{EMOJIS['waveform']} "
                                 f"Music playback has resumed.")
            return await interaction.response.send_message(embed=embed,
                                                           ephemeral=True)

        # PAUSE
        await player.pause(True)
        button.emoji = EMOJIS["play"]
        embed = discord.Embed(color=0x5865F2)
        embed.description = (f"{EMOJIS['pause']} "
                             f"**Playback Paused**\n\n"
                             f"{EMOJIS['waveform']} "
                             f"Music playback has been paused.")
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

        if current:
            embed.description = (f"{EMOJIS['skip']} "
                                 f"**Track Skipped**\n\n"
                                 f"{EMOJIS['waveform']} "
                                 f"Skipped **{current.title}**")

        else:

            embed.description = (f"{EMOJIS['skip']} "
                                 f"**Track Skipped**")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # STOP
    @discord.ui.button(emoji=EMOJIS["stop"],
                       style=discord.ButtonStyle.danger,
                       custom_id="music_stop")
    async def stop(  # type: ignore
            self, interaction: discord.Interaction, button: discord.ui.Button):

        player = await self.validate(interaction)

        if not player:
            return
        player.queue.clear()
        await player.disconnect()

        embed = discord.Embed(color=0x5865F2)

        embed.description = (f"{EMOJIS['stop']} "
                             f"**Playback Stopped**\n\n"
                             f"{EMOJIS['leave']} "
                             f"Disconnected from voice channel.")

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
                                 f"**Queue Is Empty**")
            return await interaction.response.send_message(embed=embed,
                                                           ephemeral=True)
        entries = []
        for index, track in enumerate(player.queue, start=1):
            entries.append(f"`{index}.` "
                           f"**{track.title}**")
            if index >= 10:
                break
        embed = discord.Embed(color=0x5865F2)
        embed.description = (f"{EMOJIS['queue']} "
                             f"**Music Queue**\n\n"
                             f"{chr(10).join(entries)}")

        embed.set_footer(text=(f"{len(player.queue)} "
                               f"tracks queued"))
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # DISCONNECT
    @discord.ui.button(emoji=EMOJIS["leave"],
                       style=discord.ButtonStyle.secondary,
                       custom_id="music_disconnect")
    async def disconnect(self, interaction: discord.Interaction,
                         button: discord.ui.Button):

        player = await self.validate(interaction)
        if not player:
            return
        player.queue.clear()
        await player.disconnect()
        embed = discord.Embed(color=0x5865F2)
        embed.description = (f"{EMOJIS['leave']} "
                             f"**Disconnected**\n\n"
                             f"{EMOJIS['music_player']} "
                             f"DV-Music left the voice channel.")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # DISABLE ON TIMEOUT
    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
