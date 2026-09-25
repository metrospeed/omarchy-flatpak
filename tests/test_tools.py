import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('menu', ROOT / 'scripts/menu.py')
menu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(menu)


class MenuTests(unittest.TestCase):
    def test_preserves_comments_settings_and_repeated_install(self):
        for original in ('{}', '{// hello\n"custom": {"url":"https://a",},}',
                         '{"custom":true // hello\n}'):
            result = menu.update(original, Path('/home/test user/.local/bin'))
            parsed = json.loads(menu.masked(result))
            self.assertIn('install.flatpak', parsed)
            self.assertIn('remove.flatpak', parsed)
            self.assertEqual(result, menu.update(result, Path('/home/test user/.local/bin')))
            if '// hello' in original: self.assertIn('// hello', result)
            if 'custom' in original: self.assertEqual(parsed['custom'], json.loads(menu.masked(original))['custom'])

    def test_invalid_input(self):
        with self.assertRaises(ValueError): menu.update('{broken}', Path('/tmp/bin'))


class PickerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.log = self.root / 'log'
        self.env = dict(os.environ, PATH=str(self.bin)+':'+os.environ['PATH'],
                        XDG_DATA_HOME=str(self.root/'data'), TEST_LOG=str(self.log))
        self.mock('flatpak', '''case $1 in
list) [[ ${EMPTY:-0} == 1 ]] && exit 0; printf 'org.test.App/x86_64/stable\\tTest App\\t1\\n';;
remotes) echo flathub;;
remote-ls) printf 'app/org.test.App/x86_64/stable\\tTest App\\n';;
install|uninstall) printf '%s\\n' "$*" >> "$TEST_LOG"; exit "${FAIL:-0}";;
esac''')
        self.mock('fzf', '[[ ${CANCEL:-0} == 1 ]] && exit 130\ncat')

    def mock(self, name, body):
        file = self.bin/name
        file.write_text('#!/bin/bash\n'+body+'\n')
        file.chmod(0o755)

    def run_picker(self, operation, **env):
        return subprocess.run([str(ROOT/'bin'/('omarchy-pkg-flatpak-'+operation))],
                              env=dict(self.env, **env), capture_output=True, text=True)

    def test_remove_real_list_format_and_safe_cleanup(self):
        apps = self.root/'data/applications'
        apps.mkdir(parents=True)
        broken = apps/'org.test.App.desktop'
        broken.symlink_to('/var/lib/flatpak/exports/share/applications/org.test.App.desktop')
        custom = apps/'org.test.App.custom.desktop'
        custom.write_text('keep me')
        result = self.run_picker('remove')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.log.read_text().splitlines(), [
            'uninstall --system app/org.test.App/x86_64/stable',
            'uninstall --user app/org.test.App/x86_64/stable'])
        self.assertFalse(broken.is_symlink())
        self.assertEqual(custom.read_text(), 'keep me')

    def test_cancel_and_empty(self):
        for operation in ('install', 'remove'):
            self.assertEqual(self.run_picker(operation, CANCEL='1').returncode, 0)
            self.assertFalse(self.log.exists())
        self.assertEqual(self.run_picker('remove', EMPTY='1').returncode, 0)
        self.assertFalse(self.log.exists())

    def test_install_and_failures(self):
        self.assertEqual(self.run_picker('install').returncode, 0)
        self.assertEqual(self.log.read_text().strip(), 'install --system flathub app/org.test.App/x86_64/stable')
        for operation in ('install', 'remove'):
            self.assertEqual(self.run_picker(operation, FAIL='1').returncode, 1)


if __name__ == '__main__': unittest.main()
