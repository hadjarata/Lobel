import logging

from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

logger = logging.getLogger(__name__)


def normalize_email(value):
    value = (value or "").strip()
    if "@" not in value:
        return value
    local, domain = value.rsplit("@", 1)
    return f"{local}@{domain.lower()}"


def can_authenticate_user(user, *, require_verified=True):
    if not user or not user.is_active:
        return False
    profile = getattr(user, "customer", None)
    if profile is None or profile.is_suspended:
        return False
    return not require_verified or profile.email_verified_at is not None


def revoke_user_tokens(user):
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)
    profile = getattr(user, "customer", None)
    if profile:
        profile.token_version += 1
        profile.save(update_fields=["token_version"])
    logger.info("auth.sessions_revoked user_id=%s", user.pk)


@transaction.atomic
def suspend_user(user, *, reason=""):
    profile = user.customer
    profile.suspended_at = timezone.now()
    profile.suspension_reason = reason.strip()
    profile.save(update_fields=["suspended_at", "suspension_reason"])
    revoke_user_tokens(user)
    logger.info("auth.account_suspended user_id=%s", user.pk)
    return profile


@transaction.atomic
def unsuspend_user(user):
    profile = user.customer
    profile.suspended_at = None
    profile.suspension_reason = ""
    profile.save(update_fields=["suspended_at", "suspension_reason"])
    logger.info("auth.account_unsuspended user_id=%s", user.pk)
    return profile
