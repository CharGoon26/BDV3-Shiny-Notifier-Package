from django.contrib import admin

from .models import ShinyNotifierConfig


@admin.register(ShinyNotifierConfig)
class ShinyNotifierConfigAdmin(admin.ModelAdmin):
    list_display = (
        "channel_id",
        "enabled",
        "event_name",
        "include_server_name",
        "include_user_name",
        "last_seen_ballinstance_id",
    )
    search_fields = ("channel_id", "event_name")
    list_filter = ("enabled", "include_server_name", "include_user_name")
    readonly_fields = ("last_seen_ballinstance_id",)

    def has_add_permission(self, request):
        return super().has_add_permission(request) and not ShinyNotifierConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
