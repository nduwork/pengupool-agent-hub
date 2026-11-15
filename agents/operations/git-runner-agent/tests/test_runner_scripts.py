import os
import subprocess
import tempfile
import unittest

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


class RunnerScriptsTest(unittest.TestCase):
    """git_runners.sh and setup_runners.sh in a sandbox HOME, with launchctl stubbed."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        bin_dir = os.path.join(self.root, "bin")
        os.makedirs(bin_dir)
        stub = os.path.join(bin_dir, "launchctl")
        with open(stub, "w") as f:  # "print" says not running; bootstrap succeeds
            f.write('#!/bin/sh\n[ "$1" = print ] && exit 1\nexit 0\n')
        os.chmod(stub, 0o755)
        self.env = dict(os.environ, HOME=self.root, RUNNER_ROOT=os.path.join(self.root, "runners"),
                        PATH=bin_dir + os.pathsep + os.environ["PATH"], RUNNER_NAMES="r1 r2")
        self.env.pop("PROCESS_TYPE", None)
        for name in ("r1", "r2"):
            run = os.path.join(self.instance(name), "run.sh")
            os.makedirs(os.path.dirname(run))
            with open(run, "w") as f:
                f.write("#!/bin/sh\n")
            os.chmod(run, 0o755)

    def tearDown(self):
        self.tmp.cleanup()

    def instance(self, name):
        return os.path.join(self.root, "runners", "instances", name)

    def plist(self, name):
        with open(os.path.join(self.root, "Library", "LaunchAgents", f"com.github.actions.{name}.plist")) as f:
            return f.read()

    def test_bad_setting_skips_only_that_runner(self):
        with open(os.path.join(self.instance("r1"), ".process_type"), "w") as f:
            f.write("Fast\n")
        r = subprocess.run([os.path.join(HERE, "git_runners.sh"), "start"], env=self.env,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Skipping r1", r.stderr)
        self.assertIn("<string>Background</string>", self.plist("r2"))

    def test_setup_keeps_saved_settings(self):
        template = os.path.join(self.root, "runners", "template")
        os.makedirs(template)
        with open(os.path.join(self.instance("r1"), ".process_type"), "w") as f:
            f.write("Standard\n")
        # clone_instance only: drop the script's last line, which runs main.
        script = f'eval "$(sed \'$d\' "{HERE}/setup_runners.sh")"; clone_instance r1; clone_instance r2'
        subprocess.run(["bash", "-c", script], env=dict(self.env, GITHUB_OWNER="o", GITHUB_REPO="r"),
                       check=True)
        with open(os.path.join(self.instance("r1"), ".process_type")) as f:
            self.assertEqual(f.read(), "Standard\n")
        self.assertFalse(os.path.exists(os.path.join(self.instance("r1"), "run.sh")))
        self.assertFalse(os.path.exists(os.path.join(self.instance("r2"), ".process_type")))


if __name__ == "__main__":
    unittest.main()
