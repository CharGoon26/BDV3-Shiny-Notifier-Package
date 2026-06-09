from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands, tasks

from ballsdex.core.utils.checks import app_check, is_staff
from bd_models.models import BallInstance

from .models import ShinyNotifierConfig

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot

log = logging.getLogger("ballsdex.packages.shiny_notifier")
POLL_INTERVAL_SECONDS = 5
DEFAULT_EVENT_NAME = "Shiny"


def is_shiny(ball_instance: BallInstance, event_name: str) -> bool:
    special = ball_instance.special
    return bool(special and special.name.casefold() == event_name.casefold())


@app_commands.guild_only()
class ShinyNotifier(commands.GroupCog, group_name="shiny"):
    notifier = app_commands.Group(name="notifier", description="Manage shiny notifications")

    def __init__(self, bot: "BallsDexBot"):
        self.bot = bot

    async def cog_load(self):
        await self._ensure_config()
        if not self.poll_shiny_catches.is_running():
            self.poll_shiny_catches.start()

    def cog_unload(self):
        if self.poll_shiny_catches.is_running():
            self.poll_shiny_catches.cancel()

    async def _get_latest_ballinstance_id(self) -> int:
        latest = await BallInstance.objects.order_by("-pk").only("pk").afirst()
        return latest.pk if latest else 0

    async def _ensure_config(self) -> ShinyNotifierConfig:
        latest_id = await self._get_latest_ballinstance_id()
        config, created = await ShinyNotifierConfig.objects.aget_or_create(
            pk=1,
            defaults={
                "channel_id": None,
                "enabled": True,
                "event_name": DEFAULT_EVENT_NAME,
                "include_server_name": True,
                "include_user_name": False,
                "last_seen_ballinstance_id": latest_id,
            },
        )
        if not created and config.last_seen_ballinstance_id == 0 and latest_id:
            config.last_seen_ballinstance_id = latest_id
            await config.asave(update_fields=("last_seen_ballinstance_id",))
        return config

    async def _resolve_notification_channel(self, channel_id: int) -> discord.abc.Messageable | None:
        channel = self.bot.get_channel(channel_id)
        if channel is not None:
            return channel
        try:
            fetched_channel = await self.bot.fetch_channel(channel_id)
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            return None
        return fetched_channel if isinstance(fetched_channel, discord.abc.Messageable) else None

    async def _send_notification(self, ball_instance: BallInstance, config: ShinyNotifierConfig) -> bool:
        if not config.channel_id:
            return False

        channel = await self._resolve_notification_channel(config.channel_id)
        if channel is None:
            log.warning("Shiny notifier channel %s could not be resolved.", config.channel_id)
            return False

        parts = [f"✨ Someone caught a shiny **{ball_instance.ball.country}**!"]

        if config.include_user_name:
            parts.append(f"User: <@{ball_instance.player.discord_id}>")

        try:
            await channel.send("\n".join(parts))
            return True
        except (discord.Forbidden, discord.HTTPException):
            log.exception("Failed to send shiny notification for BallInstance %s", ball_instance.pk)
            return False

    @notifier.command(name="channel")
    @app_check(is_staff())
    async def channel(self, interaction: discord.Interaction["BallsDexBot"], channel: discord.TextChannel):
        config = await self._ensure_config()
        config.channel_id = channel.id
        config.enabled = True
        await config.asave(update_fields=("channel_id", "enabled"))
        await interaction.response.send_message(f"Shiny notifier channel set to {channel.mention}.", ephemeral=True)

    @notifier.command(name="status")
    @app_check(is_staff())
    async def status(self, interaction: discord.Interaction["BallsDexBot"]):
        config = await self._ensure_config()
        if not config.channel_id:
            channel_text = "not configured"
        elif interaction.guild:
            channel = interaction.guild.get_channel(config.channel_id)
            channel_text = channel.mention if channel else f"`{config.channel_id}`"
        else:
            channel_text = f"`{config.channel_id}`"
        await interaction.response.send_message(
            f"Enabled: **{config.enabled}**\nChannel: {channel_text}\nEvent: **{config.event_name}**",
            ephemeral=True,
        )

    @tasks.loop(seconds=POLL_INTERVAL_SECONDS)
    async def poll_shiny_catches(self):
        config = await self._ensure_config()
        latest_processed_id = config.last_seen_ballinstance_id
        latest_ballinstance_id = await self._get_latest_ballinstance_id()

        if latest_ballinstance_id <= config.last_seen_ballinstance_id:
            return

        shiny_name = (config.event_name or DEFAULT_EVENT_NAME).strip() or DEFAULT_EVENT_NAME
        new_instances = (
            BallInstance.objects.filter(pk__gt=config.last_seen_ballinstance_id, pk__lte=latest_ballinstance_id)
            .select_related("ball", "player", "special")
            .order_by("pk")
        )

        async for ball_instance in new_instances:
            latest_processed_id = ball_instance.pk
            if is_shiny(ball_instance, shiny_name) and config.enabled and config.channel_id:
                await self._send_notification(ball_instance, config)

        if latest_processed_id > config.last_seen_ballinstance_id:
            config.last_seen_ballinstance_id = latest_processed_id
            await config.asave(update_fields=("last_seen_ballinstance_id",))

    @poll_shiny_catches.before_loop
    async def before_poll_shiny_catches(self):
        await self.bot.wait_until_ready()
