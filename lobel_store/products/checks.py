from django.conf import settings
from django.core.checks import Warning, register


@register()
def media_storage_check(app_configs, **kwargs):
    if (
        not settings.DEBUG and not settings.TESTING
        and settings.MEDIA_STORAGE_BACKEND == "local"
        and not getattr(settings, "MEDIA_LOCAL_STORAGE_IS_PERSISTENT", False)
    ):
        return [
            Warning(
                "Local media storage may be ephemeral in production.",
                hint="Configure and persist MEDIA_ROOT or install a cloud Django Storage backend.",
                id="media.W001",
            )
        ]
    return []
