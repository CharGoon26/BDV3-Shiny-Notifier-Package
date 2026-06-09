from django.db import models


class ShinyNotifierConfig(models.Model):
    channel_id = models.BigIntegerField(
        blank=True,
        null=True,
        help_text="Discord channel ID where shiny notifications will be posted.",
    )
    enabled = models.BooleanField(default=True, help_text="Whether shiny notifications are sent.")
    event_name = models.CharField(max_length=64, default="Shiny", help_text="Special event name to watch for.")
    include_server_name = models.BooleanField(default=True, help_text="Include the server name in notifications.")
    include_user_name = models.BooleanField(default=False, help_text="Include the catcher mention in notifications.")
    last_seen_ballinstance_id = models.PositiveBigIntegerField(
        default=0, help_text="Last BallInstance ID already processed by the poller."
    )

    class Meta:
        db_table = "shiny_notifier_config"
        verbose_name = "Shiny notifier config"
        verbose_name_plural = "Shiny notifier config"

    def __str__(self) -> str:
        return f"ShinyNotifier -> {self.channel_id or 'unconfigured'}"
