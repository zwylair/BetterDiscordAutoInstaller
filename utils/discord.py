import os
import re
import glob
import time
import logging
import subprocess

import psutil

import config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="(%(asctime)s) %(message)s")


def get_log_file_path(edition: config.DiscordEdition) -> str:
    return f"{config.APPDATA}/{edition.to_str().lower()}/logs/{edition}_updater_rCURRENT.log"


def find_discord_path(edition: config.DiscordEdition) -> str | None:
    for path in config.DISCORD_POSSIBLE_PATHS.get(edition):
        if os.path.exists(path) and any(i.startswith("app-") for i in os.listdir(path)):
            return path
    return None


def get_latest_installed_discord_folder_name(discord_parent_path: str) -> str:
    if not os.path.exists(discord_parent_path):
        raise FileNotFoundError(f"Discord directory not found: {discord_parent_path}")

    discord_versions = [i for i in os.listdir(discord_parent_path) if re.fullmatch(r"app-\d+(\.\d+)*", i)]
    if not discord_versions:
        raise FileNotFoundError(f"No 'app-*' folders found in: {discord_parent_path}")

    discord_versions.sort(key=lambda i: [int(n) for n in re.findall(r"\d+", i)])
    return discord_versions[-1]


def find_core_index_path(discord_path: str) -> str | None:
    core_paths = glob.glob(os.path.join(discord_path, "modules/discord_desktop_core-*/discord_desktop_core"))
    core_paths.sort(key=lambda i: int(re.search(r"core-(\d+)", i).group(1)), reverse=True)

    for core_path in core_paths:
        index_js_path = os.path.join(core_path, "index.js")

        if os.path.exists(index_js_path):
            return index_js_path
    return None


def kill_discord(edition: config.DiscordEdition) -> bool:
    executable_name = edition.to_str() + ".exe"
    was_running = False

    for process in psutil.process_iter(["name"]):
        if process.info["name"] == executable_name:
            was_running = True

            try:
                logger.info(f"Killing process: {process.info["name"]} (PID: {process.pid})")
                process.kill()
            except psutil.NoSuchProcess:
                pass
    return was_running


def start_discord(edition: config.DiscordEdition, discord_parent_path: str):
    logger.info(f"Starting Discord from {discord_parent_path}...")
    executable_name = edition.to_str() + ".exe"

    update_exe = os.path.join(discord_parent_path, "Update.exe")
    if not os.path.exists(update_exe):
        raise FileNotFoundError(f"Update.exe not found in: {discord_parent_path}")

    command = [update_exe, "--processStart", executable_name]
    logger.info(f"Starting Discord using command: {command}")
    subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        close_fds=True
    )


def is_discord_running(edition: config.DiscordEdition) -> bool:
    executable_name = edition.to_str() + ".exe"
    for process in psutil.process_iter(["name"]):
        if process.info.get("name") == executable_name:
            return True
    return False


def is_discord_updating(edition: config.DiscordEdition, discord_parent_path: str) -> bool:
    update_finished_messages = ("Updater main thread exiting", "Already up to date. Nothing to do", "determined update is optional")

    try:
        with open(get_log_file_path(edition), encoding="utf-8", errors="replace") as updater_log_file:
            content = updater_log_file.read()

        for message in update_finished_messages:
            if message in content:
                logger.info(f"Detected update end message: {message}")
                return False

        log_idle_time = time.time() - os.path.getmtime(get_log_file_path(edition))
        latest_app_path = os.path.join(discord_parent_path, get_latest_installed_discord_folder_name(discord_parent_path))

        if log_idle_time > config.DISCORD_UPDATER_LOG_IDLE_TIMEOUT and find_core_index_path(latest_app_path):
            logger.info("Updater log has not changed for a while and Discord core is installed. Considering update ended.")
            return False
        return True
    except PermissionError as e:
        logger.error("Cannot read log file.", exc_info=e)
        return False
    except FileNotFoundError as e:
        logger.error("Log file not found.", exc_info=e)
        return False
