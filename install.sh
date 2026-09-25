#!/bin/bash
# Install from a checkout or directly with curl | bash.
set -euo pipefail
[[ $EUID != 0 ]] || { echo 'Run as your desktop user, not with sudo.' >&2; exit 1; }
command -v omarchy >/dev/null || { echo 'This installer requires Omarchy.' >&2; exit 1; }
omarchy_root=${OMARCHY_PATH:-/usr/share/omarchy}
[[ -f $omarchy_root/default/omarchy/omarchy-menu.jsonc ]] || {
  echo 'This installer needs the Omarchy JSONC menu extension system. Update Omarchy first.' >&2
  exit 1
}
command -v xdg-terminal-exec >/dev/null || { echo 'xdg-terminal-exec is required.' >&2; exit 1; }
missing=()
for dependency in flatpak fzf python curl; do
  command -v "$dependency" >/dev/null || missing+=("$dependency")
done
if (( ${#missing[@]} )); then sudo pacman -S --needed "${missing[@]}"; fi
scratch=$(mktemp -d)
trap 'rm -rf -- "$scratch"' EXIT
source_dir=''
if [[ -n ${BASH_SOURCE[0]:-} && -f ${BASH_SOURCE[0]} ]]; then
  source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fi
if [[ ! -f $source_dir/scripts/menu.py ]]; then
  # Resolve main once, then download all files from the same immutable commit.
  revision=$(curl -fsSL https://api.github.com/repos/metrospeed/omarchy-flatpak/commits/main |
    python -c 'import json,sys; print(json.load(sys.stdin)["sha"])')
  [[ $revision =~ ^[0-9a-f]{40}$ ]] || { echo 'Invalid repository revision.' >&2; exit 1; }
  source_dir=$scratch/source
  mkdir -p "$source_dir/bin" "$source_dir/scripts"
  for file in bin/omarchy-pkg-flatpak-install bin/omarchy-pkg-flatpak-remove scripts/menu.py; do
    curl -fsSL "https://raw.githubusercontent.com/metrospeed/omarchy-flatpak/$revision/$file" -o "$source_dir/$file"
  done
fi
for script in "$source_dir"/bin/*; do bash -n "$script"; done
bindir=$HOME/.local/bin
menu=${XDG_CONFIG_HOME:-$HOME/.config}/omarchy/extensions/omarchy-menu.jsonc
python "$source_dir/scripts/menu.py" "$menu" "$scratch/menu.jsonc" "$bindir"
# System scope matches Omarchy's package installer and existing Flatpak apps.
sudo flatpak remote-add --system --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
backup=${XDG_STATE_HOME:-$HOME/.local/state}/omarchy-flatpak/backups/$(date +%Y%m%d-%H%M%S)-$$
mkdir -p "$backup" "$bindir" "$(dirname "$menu")"
[[ ! -e $menu ]] || cp -p "$menu" "$backup/omarchy-menu.jsonc"
for name in omarchy-pkg-flatpak-install omarchy-pkg-flatpak-remove; do
  [[ ! -e $bindir/$name ]] || cp -p "$bindir/$name" "$backup/$name"
  install -m 755 "$source_dir/bin/$name" "$bindir/$name"
done
install -m 644 "$scratch/menu.jsonc" "$menu"
printf '\nInstalled! Open Omarchy → Install → Flatpak or Remove → Flatpak.\nBackups: %s\n' "$backup"
