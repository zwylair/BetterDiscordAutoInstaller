import os
import sys

import config

APPDATA = os.getenv("appdata")
LOCALAPPDATA = os.getenv("localappdata")
USERPROFILE = os.getenv("userprofile")

BDAI_SCRIPT_VERSION = "1.5.0"
BDAI_LATEST_RELEASE_PAGE_URL = "https://github.com/Zwylair/BetterDiscordAutoInstaller/releases/latest"
BDAI_RAW_RELEASE_URL_TEMPLATE = "https://github.com/Zwylair/BetterDiscordAutoInstaller/archive/refs/tags/{tag}.zip"
BDAI_RELEASE_URL_TEMPLATE = "https://github.com/Zwylair/BetterDiscordAutoInstaller/releases/download/{tag}/BetterDiscordAutoInstaller-{tag}.zip"
if getattr(sys, "frozen", False):
    BDAI_ROOT_PATH = os.path.dirname(sys.executable)

    if not os.path.basename(sys.executable).lower().startswith("updater"):
        BDAI_ROOT_PATH = os.path.dirname(BDAI_ROOT_PATH)
else:
    BDAI_ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SETTINGS_PATH = os.path.join(BDAI_ROOT_PATH, "settings.json")

DISCORD_UPDATE_WAIT_TIMEOUT = 300
DISCORD_UPDATER_LOG_IDLE_TIMEOUT = 30

BD_LATEST_RELEASE_PAGE_URL = "https://github.com/rauenzi/BetterDiscordApp/releases/latest"
BD_RELEASE_API_URL = "https://api.github.com/repos/rauenzi/BetterDiscordApp/releases/latest"
BD_ASAR_URL = "https://github.com/rauenzi/BetterDiscordApp/releases/latest/download/betterdiscord.asar"
BD_ASAR_PATH = os.path.join(APPDATA, "BetterDiscord", "data", "betterdiscord.asar")
BD_CI_ASAR_PATH = os.path.join(APPDATA, "BetterDiscord", "data", "betterdiscord-ci.asar")
BD_CI_RELEASE_API_URL = "https://api.github.com/repos/BetterDiscord/BetterDiscord/releases/tags/canary"
BD_CI_ASAR_URL = "https://github.com/BetterDiscord/BetterDiscord/releases/download/canary/betterdiscord.asar"

DISCORD_PARENT_PATH_SETTING_KEYS = {
    config.DiscordEdition.STABLE: "discord_installed_path",
    config.DiscordEdition.CANARY: "discord_canary_installed_path",
    config.DiscordEdition.PTB: "discord_ptb_installed_path",
}
LAST_INSTALLED_DISCORD_VERSION_SETTING_KEYS = {
    config.DiscordEdition.STABLE: "last_installed_discord_version",
    config.DiscordEdition.CANARY: "last_installed_discord_canary_version",
    config.DiscordEdition.PTB: "last_installed_discord_ptb_version",
}

DISCORD_POSSIBLE_PATHS = {
    config.DiscordEdition.STABLE: [os.path.join(LOCALAPPDATA, "Discord")],
    config.DiscordEdition.CANARY: [os.path.join(LOCALAPPDATA, "DiscordCanary")],
    config.DiscordEdition.PTB: [os.path.join(LOCALAPPDATA, "DiscordPTB")],
}
