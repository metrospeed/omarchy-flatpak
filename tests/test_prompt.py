"""Exercise the bootstrap's package prompt with piped script input and a real PTY."""
import os
from pathlib import Path
import pty
import select
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PromptTests(unittest.TestCase):
    def test_piped_installer_reads_confirmation_from_terminal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            menu = root/'default/omarchy/omarchy-menu.jsonc'
            menu.parent.mkdir(parents=True)
            menu.write_text('{}')
            # Run the actual dependency-check portion, with harmless shell stubs.
            bootstrap = (ROOT/'install.sh').read_text().split('scratch=$(mktemp -d)')[0]
            bootstrap = bootstrap.replace('[[ $EUID != 0 ]]', '[[ 1 == 1 ]]')
            payload = '''command() { [[ $* != '-v flatpak' ]]; }
sudo() {
  printf 'Proceed with installation? [Y/n] ' >/dev/tty
  read -r answer
  [[ $answer == y ]] || return 42
  echo CONFIRMED
}
'''+bootstrap+'\necho BOOTSTRAP_FINISHED\n'
            pid, fd = pty.fork()
            if pid == 0:
                result = subprocess.run(['bash'], input=payload, text=True,
                                        env=dict(os.environ, OMARCHY_PATH=str(root)))
                os._exit(result.returncode)
            output = b''
            answered = False
            deadline = time.monotonic()+10
            try:
                while time.monotonic() < deadline:
                    if select.select([fd], [], [], 0.1)[0]:
                        try: chunk = os.read(fd, 4096)
                        except OSError: break
                        if not chunk: break
                        output += chunk
                        if b'[Y/n]' in output and not answered:
                            os.write(fd, b'y\n')
                            answered = True
                else:
                    os.kill(pid, 9)
                    self.fail('Timed out waiting for prompt: '+repr(output))
                _, status = os.waitpid(pid, 0)
                self.assertEqual(os.waitstatus_to_exitcode(status), 0, output)
                self.assertIn(b'CONFIRMED', output)
                self.assertIn(b'BOOTSTRAP_FINISHED', output)
            finally:
                os.close(fd)


if __name__ == '__main__': unittest.main()
