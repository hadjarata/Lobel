import os
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured


def env_required(name):
    value = os.getenv(name)
    if value is None or not value.strip():
        raise ImproperlyConfigured(f"Missing required environment variable: {name}")
    return value.strip()


def env_optional(name, default=""):
    value = os.getenv(name)
    return default if value is None else value.strip()


def env_bool(name, default=None):
    raw = os.getenv(name)
    if raw is None:
        if default is None:
            raise ImproperlyConfigured(f"Missing required environment variable: {name}")
        return default
    values = {
        "true": True, "1": True, "yes": True, "on": True,
        "false": False, "0": False, "no": False, "off": False,
    }
    try:
        return values[raw.strip().lower()]
    except KeyError as exc:
        raise ImproperlyConfigured(f"Invalid boolean environment variable: {name}") from exc


def env_int(name, default=None, minimum=None):
    raw = os.getenv(name)
    if raw is None:
        if default is None:
            raise ImproperlyConfigured(f"Missing required environment variable: {name}")
        value = default
    else:
        try:
            value = int(raw.strip())
        except ValueError as exc:
            raise ImproperlyConfigured(f"Invalid integer environment variable: {name}") from exc
    if minimum is not None and value < minimum:
        raise ImproperlyConfigured(f"Environment variable {name} is below its minimum.")
    return value


def env_list_required(name):
    values = [part.strip() for part in env_required(name).split(",") if part.strip()]
    if not values:
        raise ImproperlyConfigured(f"Environment variable list is empty: {name}")
    return values


def env_https_url(name):
    value = env_required(name)
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.hostname in {"localhost", "127.0.0.1"}:
        raise ImproperlyConfigured(f"Environment variable {name} must be an absolute public HTTPS URL.")
    if "*" in value:
        raise ImproperlyConfigured(f"Wildcard is forbidden in environment variable: {name}")
    return value.rstrip("/")


def env_https_url_list(name):
    values = env_list_required(name)
    for value in values:
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.netloc or parsed.path not in ("", "/") or "*" in value:
            raise ImproperlyConfigured(f"Environment variable {name} must contain HTTPS origins only.")
    return [value.rstrip("/") for value in values]
