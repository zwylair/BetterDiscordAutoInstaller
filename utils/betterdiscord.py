import os
import glob
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
    core_path_pattern = os.path.join(discord_path, "modules/discord_desktop_core-*/discord_desktop_core")
    core_paths = glob.glob(core_path_pattern)

    if not core_paths:
        logger.warning("Discord core path not found when checking BetterDiscord injection.")
        return False

    index_js_path = os.path.join(core_paths[0], "index.js")
    if not os.path.exists(index_js_path):
        logger.warning("Discord index.js not found.")
        return False

    with open(index_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    return f'require("{get_asar_path(is_ci)}");' in content


def _fetch_bd_stable_digest() -> str | None:
    """GET latest BetterDiscord.asar checksum"""
    try:
        resp = requests.get(config.BD_RELEASE_API_URL, timeout=5)
        resp.raise_for_status()
        assets = resp.json().get("assets", [])
        for asset in assets:
            if asset.get("name") == "betterdiscord.asar":
                digest = asset.get("digest", "")
                if digest.startswith("sha256:"):
                    return digest[len("sha256:"):]
        logger.error("betterdiscord.asar asset or digest not found in release API response.")
    except Exception as e:
        logger.error(f"Failed to fetch release digest: {e}")
    return None


def _download_bd_stable_asar(dest_path: str, max_retries: int = 3) -> bool:
    expected_digest = _fetch_bd_stable_digest() # Get .asar checksum

    # Fail if unable to get checksum
    if not expected_digest:
        return False

    tmp_path = dest_path + ".tmp"

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Downloading BetterDiscord Stable asar (attempt {attempt}/{max_retries})...")
            response = requests.get(config.BD_ASAR_URL, timeout=30)
            response.raise_for_status()

            # Compile and compare checksum
            actual_digest = hashlib.sha256(response.content).hexdigest()
            if actual_digest != expected_digest:
                raise requests.exceptions.RequestException(
                    f"SHA256 mismatch (attempt {attempt}): expected {expected_digest}, got {actual_digest}"
                )

            # Write to .tmp then swap to dest_path so the used .asar is never left half written
            # that would cause Discord to crash on startup
            with open(tmp_path, "wb") as f:
                f.write(response.content)
            os.replace(tmp_path, dest_path)
            logger.info("BetterDiscord Stable asar downloaded and verified successfully.")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Download error (attempt {attempt}): {e}")
            if attempt < max_retries:
                time.sleep(2 ** (attempt - 1))

    logger.error(f"Failed to download BetterDiscord Stable asar after {max_retries} attempts.")
    return False


def update_bd_asar_only(is_ci: bool):
    if is_ci:
        if update_bd_ci_asar():
            logger.info("BetterDiscord CI has been updated successfully.")
            return

        logger.info("BetterDiscord CI update failed.")
        return

    os.makedirs(os.path.dirname(config.BD_ASAR_PATH), exist_ok=True)

    if not _download_bd_stable_asar(config.BD_ASAR_PATH):
        logger.error("BetterDiscord Stable asar update failed.")
        return

    config.LAST_INSTALLED_BD_VERSION = fetch_latest_bd_release()
    config.dump_settings()


def inject_patch(discord_path: str, is_ci: bool):
    core_path_pattern = os.path.join(discord_path, "modules/discord_desktop_core-*/discord_desktop_core")
    core_paths = glob.glob(core_path_pattern)

    if not core_paths:
        raise FileNotFoundError(f"No matching discord_desktop_core-* folder found in: {discord_path}")

    index_js_path = os.path.join(core_paths[0], "index.js")

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


def fetch_latest_bd_release() -> str:
    logger.info("Fetching latest BetterDiscord Stable version.")
    latest_release_url = requests.head(config.BD_LATEST_RELEASE_PAGE_URL, allow_redirects=True)
    return latest_release_url.url.split("/")[-1]


def check_for_bd_updates(is_ci: bool) -> bool:
    """Checks for updates and return True if there is an available update, False otherwise"""
    logger.info("Checking for BetterDiscord updates...")
    return check_for_bd_ci_updates() if is_ci else fetch_latest_bd_release() != config.LAST_INSTALLED_BD_VERSION


def check_for_bd_ci_updates() -> bool:
    """Checks for updates and return True if there is an available update, False otherwise"""
    return utils.get_artifacts_from_successful_run(
        config.BD_CI_WORKFLOWS_RUNS_URL,
        config.BD_CI_WORKFLOW_REPO,
        config.BD_CI_WORKFLOW_AUTHOR
    ).run_id != config.LAST_INSTALLED_BD_CI_VERSION


def update_bd_ci_asar() -> bool:
    """Updates BD CI and returns False if there is any error, True otherwise"""

    release_meta = utils.get_artifacts_from_successful_run(config.BD_CI_WORKFLOWS_RUNS_URL, config.BD_CI_WORKFLOW_REPO, config.BD_CI_WORKFLOW_AUTHOR)
    if not release_meta:
        logger.info(f"Failed to fetch BetterDiscord CI artifacts from workflow run.")
        return False

    artifact = utils.find_artefact(release_meta.artifacts)
    if not artifact:
        logger.info(f"Failed to find BetterDiscord CI artifact ({release_meta.run_id}).")
        return False

    success = utils.download_artifact(artifact)
    if not success:
        return False

    config.LAST_INSTALLED_BD_CI_VERSION = release_meta.run_id
    config.dump_settings()
    return True
