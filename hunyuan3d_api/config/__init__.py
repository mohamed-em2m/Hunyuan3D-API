"""
hunyuan3d_api.config — dynaconf-powered settings loader.

Usage anywhere in the package:
    from hunyuan3d_api.config import settings

    host = settings.server.host
    port = settings.server.port

Environment selection (set before running):
    ENV_FOR_DYNACONF=development   (options: default | development | production)

Secret overrides (gitignored):
    .secrets.toml

Environment-variable overrides (prefix HUNYUAN3D__, double-underscore for nesting):
    HUNYUAN3D__SERVER__PORT=9000
    HUNYUAN3D__MODEL__DEVICE=cpu
"""

from dynaconf import Dynaconf

settings = Dynaconf(
    # Env-var prefix: HUNYUAN3D__KEY__SUBKEY=value
    envvar_prefix="HUNYUAN3D",
    # Config files loaded in order; later files have higher priority
    settings_files=[
        "config/settings.toml",
        ".secrets.toml",
    ],
    # Enable environment layering (default / development / production)
    environments=True,
    # Fall back to [default] when ENV_FOR_DYNACONF is not set
    default_env="default",
    env_switcher="ENV_FOR_DYNACONF",
    # Automatically load .env if present
    load_dotenv=True,
    # Nested sections in TOML are resolved as DynaBox objects
    # merge_enabled keeps sub-keys from parent env when child only overrides some
    merge_enabled=True,
)

__all__ = ["settings"]
