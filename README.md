# Omarchy Flatpak

Search, install, and remove Flatpak apps from the Omarchy menu, with a fuzzy finder like the built-in AUR installer.

## Install with one command

Run in a terminal as your normal desktop user:

```bash
curl -fsSL https://raw.githubusercontent.com/metrospeed/omarchy-flatpak/main/install.sh | bash
```

Requires Omarchy with the JSONC menu extension system and `xdg-terminal-exec`. The installer installs missing Flatpak, fzf, Python, and curl packages through pacman, configures system-wide Flathub, and adds **Install → Flatpak** and **Remove → Flatpak**. It may prompt for your sudo password. Curl must already be available for the one-command download.

Reopen the Omarchy menu after installation. Run the same command again to update.

## Use

- Type to search; **Tab** selects multiple apps.
- **Enter** starts the operation with Flatpak's normal confirmation.
- **Esc** cancels; **Alt+P** toggles details.
- Install searches system Flathub. Remove lists both default system and user-installed apps, with their scope shown.
- Removal keeps saved app data. Custom named Flatpak installations are not included.

You can also run `~/.local/bin/omarchy-pkg-flatpak-install` or `~/.local/bin/omarchy-pkg-flatpak-remove` directly.

The installer adds local desktop/icon links so apps can appear even in sessions started before Flatpak was installed. The remover cleans up broken Flatpak links while preserving custom launchers.

## What setup changes

Scripts are installed in `~/.local/bin`. Menu entries are merged into `${XDG_CONFIG_HOME:-~/.config}/omarchy/extensions/omarchy-menu.jsonc`, retaining other settings and comments. Existing files are backed up beneath `${XDG_STATE_HOME:-~/.local/state}/omarchy-flatpak/backups/`. No packaged Omarchy files are edited.

To inspect before running, download `install.sh` or clone this repository and run `bash install.sh`. The online installer resolves the repository revision once and downloads its payload from that commit.

## Uninstall the integration

Remove the `install.flatpak` and `remove.flatpak` entries from your menu extension file, then delete the two `omarchy-pkg-flatpak-*` scripts from `~/.local/bin`. This leaves installed Flatpak apps, Flathub, and saved app data in place. Backups are available for restoring prior versions of the files; restoring the entire menu backup also restores its older settings.

## Development

```bash
python -m unittest discover -s tests -v
bash -n install.sh bin/omarchy-pkg-flatpak-install bin/omarchy-pkg-flatpak-remove
```

Tests simulate package operations; they do not install or remove apps. This is an independent community project, not an official Omarchy component.
