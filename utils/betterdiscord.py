import os
import hashlib
import logging
import time

import requests

import config
import utils

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="(%(asctime)s) %(message)s")


def get_asar_path(is_ci: bool) -> str:
    return utils.backslash_path(config.BD_CI_ASAR_PATH if is_ci else config.BD_ASAR_PATH)


def get_require_line(is_ci: bool) -> str:
    return f'require("{get_asar_path(is_ci)}");\n'


def get_release_tag(is_ci: bool) -> str:
    return "CI" if is_ci else "Stable"


def is_bd_injected(discord_path: str, is_ci: bool) -> bool:
    index_js_path = utils.find_core_index_path(discord_path)

    if not index_js_path:
        logger.warning("Discord index.js not found when checking BetterDiscord injection.")
        return False

    with open(index_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    return f'require("{get_asar_path(is_ci)}");' in content


def get_release_api_url(is_ci: bool) -> str:
    return config.BD_CI_RELEASE_API_URL if is_ci else config.BD_RELEASE_API_URL


def fetch_bd_asar_digest(is_ci: bool) -> str | None:
    try:
        resp = requests.get(get_release_api_url(is_ci), timeout=15)
        resp.raise_for_status()
        assets = resp.json().get("assets", [])
        for asset in assets:
            if asset.get("name") == "betterdiscord.asar":
                digest = asset.get("digest", "")
                if digest.startswith("sha256:"):
                    return digest[len("sha256:"):]
        logger.warning("betterdiscord.asar asset or digest not found in release API response.")
    except Exception as e:
        logger.warning(f"Failed to fetch release digest: {e}")
    return None


def _download_bd_asar(is_ci: bool, expected_digest: str | None, max_retries: int = 3) -> bool:
    dest_path = config.BD_CI_ASAR_PATH if is_ci else config.BD_ASAR_PATH
    release_tag = get_release_tag(is_ci)

    if not expected_digest:
        logger.warning("Checksum of the BetterDiscord asar is unavailable, skipping its verification.")

    tmp_path = dest_path + ".tmp"

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Downloading BetterDiscord {release_tag} asar (attempt {attempt}/{max_retries})...")
            response = requests.get(config.BD_CI_ASAR_URL if is_ci else config.BD_ASAR_URL, timeout=30)
            response.raise_for_status()

            actual_digest = hashlib.sha256(response.content).hexdigest()
            if expected_digest and actual_digest != expected_digest:
                raise requests.exceptions.RequestException(
                    f"SHA256 mismatch (attempt {attempt}): expected {expected_digest}, got {actual_digest}"
                )

            with open(tmp_path, "wb") as f:
                f.write(response.content)
            os.replace(tmp_path, dest_path)
            logger.info(f"BetterDiscord {release_tag} asar downloaded and verified successfully.")
            return True

        except (requests.exceptions.RequestException, OSError) as e:
            logger.error(f"Download error (attempt {attempt}): {e}")
            if attempt < max_retries:
                time.sleep(2 ** (attempt - 1))

    logger.error(f"Failed to download BetterDiscord {release_tag} asar after {max_retries} attempts.")
    return False


def update_bd_asar_only(is_ci: bool):
    os.makedirs(os.path.dirname(config.BD_CI_ASAR_PATH if is_ci else config.BD_ASAR_PATH), exist_ok=True)
    expected_digest = fetch_bd_asar_digest(is_ci)

    if not _download_bd_asar(is_ci, expected_digest):
        logger.error(f"BetterDiscord {get_release_tag(is_ci)} asar update failed.")
        return

    if is_ci:
        if expected_digest:
            config.LAST_INSTALLED_BD_CI_VERSION = expected_digest
            config.dump_settings()
        return

    latest_release = fetch_latest_bd_release()
    if latest_release:
        config.LAST_INSTALLED_BD_VERSION = latest_release
        config.dump_settings()


def inject_patch(discord_path: str, is_ci: bool):
    index_js_path = utils.find_core_index_path(discord_path)

    if not index_js_path:
        raise FileNotFoundError(f"Discord index.js not found in: {discord_path}")

    with open(index_js_path, "r", encoding="utf-8") as f:
        content = f.readlines()

    require_line = get_require_line(is_ci)
    other_release_require_line = get_require_line(not is_ci)
    release_tag = get_release_tag(is_ci)
    other_release_tag = get_release_tag(not is_ci)

    if any(other_release_require_line.strip() in line for line in content):
        logger.info(f"Found BetterDiscord {other_release_tag} injection. Removing it.")
        content = utils.remove_item_from_list(other_release_require_line, content)

    if any(require_line.strip() in line for line in content):
        logger.info(f"BetterDiscord {release_tag} is already injected. Skipping patch.")
        return

    content.insert(0, require_line)

    with open(index_js_path, "w", encoding="utf-8") as f:
        f.writelines(content)

    logger.info(f"Patched {index_js_path} to include BetterDiscord {release_tag}.")


def remove_patch(discord_path: str, is_ci: bool):
    index_js_path = utils.find_core_index_path(discord_path)

    if not index_js_path:
        return

    with open(index_js_path, "r", encoding="utf-8") as f:
        content = f.readlines()

    with open(index_js_path, "w", encoding="utf-8") as f:
        f.writelines(utils.remove_item_from_list(get_require_line(is_ci), content))

    logger.info(f"Removed BetterDiscord {get_release_tag(is_ci)} from {index_js_path}.")


def fetch_latest_bd_release() -> str | None:
    logger.info("Fetching latest BetterDiscord Stable version.")
    return utils.fetch_latest_release_tag(config.BD_LATEST_RELEASE_PAGE_URL)


def check_for_bd_updates(is_ci: bool) -> bool:
    """Checks for updates and return True if there is an available update, False otherwise"""
    logger.info("Checking for BetterDiscord updates...")

    if not os.path.exists(get_asar_path(is_ci)):
        logger.info("BetterDiscord asar is missing.")
        return True

    if is_ci:
        return check_for_bd_ci_updates()

    latest_release = fetch_latest_bd_release()
    return latest_release is not None and latest_release != config.LAST_INSTALLED_BD_VERSION


def check_for_bd_ci_updates() -> bool:
    """Checks for updates and return True if there is an available update, False otherwise"""
    latest_digest = fetch_bd_asar_digest(True)
    return latest_digest is not None and latest_digest != config.LAST_INSTALLED_BD_CI_VERSION
