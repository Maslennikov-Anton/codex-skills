from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("tracker_api.sh")


class TrackerApiScriptTest(unittest.TestCase):
    def run_helper(self, *args: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            temp_dir = Path(directory)
            capture = temp_dir / "curl-args.txt"
            fake_curl = temp_dir / "curl"
            fake_curl.write_text(
                "#!/usr/bin/env bash\nprintf '%s\\n' \"$@\" > \"$TRACKER_TEST_CAPTURE\"\n",
                encoding="utf-8",
            )
            fake_curl.chmod(0o755)
            env = os.environ.copy()
            env.update(
                {
                    "PATH": f"{temp_dir}:{env['PATH']}",
                    "TRACKER_TOKEN": "test-token",
                    "TRACKER_ORG_ID": "test-org",
                    "TRACKER_TEST_CAPTURE": str(capture),
                }
            )
            subprocess.run([str(SCRIPT), *args], env=env, check=True)
            return capture.read_text(encoding="utf-8").splitlines()

    def test_two_argument_get_has_no_body(self) -> None:
        arguments = self.run_helper("GET", "/myself")
        self.assertIn("https://api.tracker.yandex.net/v3/myself", arguments)
        self.assertNotIn("--data", arguments)

    def test_get_query_is_appended_to_url(self) -> None:
        arguments = self.run_helper("GET", "/users", "?page=2")
        self.assertIn("https://api.tracker.yandex.net/v3/users?page=2", arguments)
        self.assertNotIn("--data", arguments)

    def test_file_mode_uses_third_argument_as_file_path(self) -> None:
        arguments = self.run_helper(
            "FILE", "/issues/TEST-1/attachments/", "/tmp/image.png"
        )
        self.assertIn("POST", arguments)
        self.assertIn("file=@/tmp/image.png", arguments)

    def test_query_and_json_body_remain_distinct(self) -> None:
        arguments = self.run_helper("POST", "/issues/_search", "?page=2", '{"q":"x"}')
        self.assertIn("https://api.tracker.yandex.net/v3/issues/_search?page=2", arguments)
        self.assertIn("--data", arguments)
        self.assertIn('{"q":"x"}', arguments)


if __name__ == "__main__":
    unittest.main()
