import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import _machine_health as mh  # noqa: E402


class XcodeDirsTest(unittest.TestCase):
    def test_internal_dir_ok_and_missing_dir_ok(self):
        with tempfile.TemporaryDirectory() as d:
            mh.XCODE_DIRS = [d, os.path.join(d, "not-yet-created")]
            self.assertEqual(mh.xcode_dirs_state(), [])

    def test_symlink_to_volumes_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            link = os.path.join(d, "DerivedData")
            os.symlink("/Volumes/SOME-EXTERNAL/DerivedData", link)
            mh.XCODE_DIRS = [link]
            reasons = mh.xcode_dirs_state()
            self.assertEqual(len(reasons), 1)
            self.assertIn("external volume", reasons[0])


class PublishDispatchTest(unittest.TestCase):
    def test_missing_file_is_none(self):
        with tempfile.TemporaryDirectory() as d:
            mh.PUBLISH_DISPATCH_PATH = os.path.join(d, "publish-dispatch.json")
            self.assertIsNone(mh.publish_dispatch_state())

    def test_failed_dispatch_read_back(self):
        with tempfile.TemporaryDirectory() as d:
            mh.PUBLISH_DISPATCH_PATH = os.path.join(d, "publish-dispatch.json")
            with open(mh.PUBLISH_DISPATCH_PATH, "w") as f:
                json.dump({"at": "2026-10-09T13:00:00Z", "ok": False, "rc": 1, "output": "HTTP 401"}, f)
            self.assertFalse(mh.publish_dispatch_state()["ok"])


class RunnerConfigTest(unittest.TestCase):
    def test_missing_config_is_an_empty_fleet(self):
        import _runner_stats_build as rs
        self.assertEqual(rs.load_config("/nonexistent/runners.local.json"), {})

    def test_example_has_every_key(self):
        import _runner_stats_build as rs
        cfg = rs.load_config(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                                          "runners.example.json"))
        for key in ("owner", "repo_owners", "repo_instances", "launchd_labels", "publish", "keychain_lock"):
            self.assertIn(key, cfg)

    def test_repair_refuses_without_a_lock(self):
        saved = mh.TF_LOCK
        mh.TF_LOCK = ""
        try:
            r = mh.keychain_repair({"search_list": [], "orphans": []})
            self.assertFalse(r["repaired"])
            self.assertTrue(r["skipped"])
        finally:
            mh.TF_LOCK = saved


if __name__ == "__main__":
    unittest.main()
