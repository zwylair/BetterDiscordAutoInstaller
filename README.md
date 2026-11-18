<h1 align="center">
    BetterDiscordAutoInstaller
</h1>

<p align="center">
    <img src="https://img.shields.io/badge/python-3.14-green?logo=python&logoColor=white&style=for-the-badge">
    <img src="https://img.shields.io/badge/LICENSE-MIT-green?style=for-the-badge">
    <img src="https://img.shields.io/github/languages/code-size/Zwylair/BetterDiscordAutoInstaller?style=for-the-badge">
</p>

## About

BetterDiscordAutoInstaller is a script that do the same work as official [BetterDiscord installer](https://betterdiscord.app/) on
applying mod on Discord (PTB, Canary too). It automatically downloads `betterdiscord.asar` file from the
official [BetterDiscord GitHub repo](https://github.com/BetterDiscord/BetterDiscord) and makes it load. If you have more than one discord
(PTB or/and Canary) installed, BDAI will also patch them. But you need to specify paths to them in
`settings.json`.

### Supported OS

Currently, BetterDiscordAutoInstaller is supported for **[Windows](https://github.com/Zwylair/BetterDiscordAutoInstaller/tree/master)** and **[macOS](https://github.com/Zwylair/BetterDiscordAutoInstaller/tree/macos)** OSes.

### BetterDiscord CI

It is also possible to use the [BetterDiscord Canary release](https://github.com/BetterDiscord/BetterDiscord/releases/tag/canary),
which is built from every commit to the development branch. Change the `use_betterdiscord_ci_releases` option to `true` in
the `settings.json` file.

### Autostart

BDAI also allows you to add/remove it from autostart, without having to run it manually  every time.
For macOS, the user can also choose to bind script to a keyboard shortcut to manually update.

### Plugins

BDAI can download BetterDiscord plugins for you. List their direct links in the `install_plugins` setting of
`settings.json` (empty by default), e.g. `"install_plugins": ["https://raw.githubusercontent.com/riolubruh/YABDP4Nitro/main/YABDP4Nitro.plugin.js"]`.
Already installed plugins are not overwritten.

### Restarting Discord

BDAI restarts every Discord edition it had to close. The edition set in `rerun_discord_edition` (Stable by default)
is started even if it was not running.

### Self update checks

BDAI will check if it is up to date. You can disable autoupdate by changing the `disable_bdai_autoupdate`
setting to `true` in the `settings.json` file (but you will still  receive a message that a new version
has been released).

## Setup and Dependencies

### Windows
- Clone repo: `git clone https://github.com/Zwylair/BetterDiscordAutoInstaller.git`
- Install uv: `py -V:3.14 -m pip install uv`
- Setup environment: `uv venv .venv --python 3.14`
- Install dependencies: `uv sync`

To add BetterDiscordAutoInstaller to your startup apps: `py -V:3.14 startup_manager.py`

### MacOS
You need to go to [this](https://github.com/Zwylair/BetterDiscordAutoInstaller/tree/macos?tab=readme-ov-file#setup-and-dependencies) README.md

## Building

### Windows
- [Install all dependencies](https://github.com/Zwylair/BetterDiscordAutoInstaller#windows)
- Run build script: `uv run --group build python setup.py build`

## Contributing
I will be grateful for any contribution and help given to improve the quality of the project :)

### Fork
Well, just fork it

## License
This project is under the [MIT license](./LICENSE).
