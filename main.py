import os
import sys
import time
import logging

import utils
import config
import plugins

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="(%(asctime)s) %(message)s")


def main():
    config.load_settings()

    logger.info(f"BetterDiscordAutoInstaller v{config.BDAI_SCRIPT_VERSION}")

    logger.info("Checking for BetterDiscordAutoInstaller updates...")
    if utils.check_for_bdai_updates() and not config.DISABLE_BDAI_AUTOUPDATE:
        utils.run_updater()

    found_new_paths = False

    for edition in config.DISCORD_PARENT_PATHS:
        logger.info(f"Retrieving {edition} installation folder...")

        if not config.DISCORD_PARENT_PATHS[edition]:
            config.DISCORD_PARENT_PATHS[edition] = utils.find_discord_path(edition)
            found_new_paths = found_new_paths or bool(config.DISCORD_PARENT_PATHS[edition])

    if not any(config.DISCORD_PARENT_PATHS.values()):
        logger.error("No any valid Discord installation found.")
        logger.info("Enter the path to your Discord Stable installation")

        try:
            config.DISCORD_PARENT_PATHS[config.DiscordEdition.STABLE] = input(">>> ").strip()
        except EOFError:
            logger.error(f"Cannot ask for the path without a console. Set it in {config.SETTINGS_PATH}")
            sys.exit(1)

        if not os.path.exists(config.DISCORD_PARENT_PATHS[config.DiscordEdition.STABLE]):
            logger.error(f"Invalid path provided: {config.DISCORD_PARENT_PATHS[config.DiscordEdition.STABLE]}")
            sys.exit(1)

        found_new_paths = True

    if found_new_paths or not os.path.exists(config.SETTINGS_PATH):
        config.dump_settings()

    bd_release_tag = utils.get_release_tag(config.USE_BD_CI_RELEASES)
    bd_has_updates = utils.check_for_bd_updates(config.USE_BD_CI_RELEASES)
    force_update_flag = "--force" in sys.argv

    for discord_edition, discord_parent_path in config.DISCORD_PARENT_PATHS.items():
        if not discord_parent_path:
            continue

        logger.info("")
        logger.info(f"Processing {discord_edition} installation: {discord_parent_path}")

        if not utils.is_discord_running(discord_edition):
            logger.info("")

            # wipe logs, because discord doesn't do that after every updater run
            try:
                with open(utils.get_log_file_path(discord_edition), "w") as f:
                    f.write("")
            except OSError as e:
                logger.warning(f"Cannot wipe {discord_edition} updater log: {e}")

            logger.info(f"{discord_edition} is not running. Starting updater.")
            utils.start_discord(discord_edition, discord_parent_path)
            time.sleep(1)

            logger.info(f"Waiting for end of {discord_edition} updating.")
            wait_deadline = time.monotonic() + config.DISCORD_UPDATE_WAIT_TIMEOUT
            while utils.is_discord_updating(discord_edition, discord_parent_path):
                if time.monotonic() > wait_deadline:
                    logger.warning(f"Updating of {discord_edition} takes too long. Continuing anyway.")
                    break
                time.sleep(0.5)

        discord_core_folder = utils.get_latest_installed_discord_folder_name(discord_parent_path)
        discord_path = os.path.join(discord_parent_path, discord_core_folder)

        if not utils.find_core_index_path(discord_path):
            logger.error(f"{discord_edition} is not ready: discord_desktop_core is not installed yet. Skipping it.")
            continue

        is_last_patch_is_up_to_date = discord_core_folder == config.LAST_INSTALLED_DISCORD_VERSIONS[discord_edition]
        is_bd_injected_already = utils.is_bd_injected(discord_path, config.USE_BD_CI_RELEASES)

        if (
                not is_last_patch_is_up_to_date
                or not is_bd_injected_already
                or bd_has_updates
                or force_update_flag
        ):
            logger.info("")
            logger.info(f"Killing any running {discord_edition} processes...")
            was_discord_running = utils.kill_discord(discord_edition)
            time.sleep(2)

            logger.info("")

            if force_update_flag:
                logger.info("Force-set update flags.")
                is_last_patch_is_up_to_date = False
                bd_has_updates = True

            if not is_last_patch_is_up_to_date:
                logger.info(f"{discord_edition} was updated. Verifying injection patch...")
                config.LAST_INSTALLED_DISCORD_VERSIONS[discord_edition] = discord_core_folder
                config.dump_settings()
                is_bd_injected_already = False

            if bd_has_updates:
                logger.info(f"BetterDiscord {bd_release_tag} has a new version, updating asar only.")
                utils.update_bd_asar_only(config.USE_BD_CI_RELEASES)
                bd_has_updates = False

            if not is_bd_injected_already:
                if os.path.exists(utils.get_asar_path(config.USE_BD_CI_RELEASES)):
                    logger.info(f"Verifying BetterDiscord {bd_release_tag} injection patch.")
                    utils.inject_patch(discord_path, config.USE_BD_CI_RELEASES)
                else:
                    logger.error(f"BetterDiscord {bd_release_tag} asar is missing, Discord would not start with the patch. Skipping it.")

            if was_discord_running or discord_edition.to_str() == config.RERUN_DISCORD_EDITION:
                logger.info("")
                logger.info(f"Restarting {discord_edition}...")
                utils.start_discord(discord_edition, discord_parent_path)
        else:
            logger.info(f"BetterDiscord {bd_release_tag} ({discord_edition}) is up to date and injected. No action needed.")
        logger.info("")

    for plugin_info in [plugins.PluginInfo.from_url(plugin) for plugin in config.INSTALL_PLUGINS]:
        logger.info(f"Installing {plugin_info.get_name()} plugin...")
        plugins.download_plugin(plugin_info)

    logger.info("Installation complete. Exiting in 3 seconds...")
    time.sleep(3)
    sys.exit(0)


if __name__ == "__main__":
    main()
