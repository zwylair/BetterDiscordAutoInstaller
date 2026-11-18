from typing import Optional

import config

DISABLE_DISCORD_VERSION_CHECKING: bool = False
DISABLE_BDAI_AUTOUPDATE: bool = False
USE_BD_CI_RELEASES: bool = False
RERUN_DISCORD_EDITION: Optional[str] = config.DiscordEdition.STABLE.to_str()

DISCORD_PARENT_PATHS: dict[config.DiscordEdition, Optional[str]] = {edition: None for edition in config.DiscordEdition}
LAST_INSTALLED_DISCORD_VERSIONS: dict[config.DiscordEdition, Optional[str]] = {edition: None for edition in config.DiscordEdition}

LAST_INSTALLED_BD_VERSION: Optional[str] = None
LAST_INSTALLED_BD_CI_VERSION: Optional[str] = None

INSTALL_PLUGINS: list[str] = []
