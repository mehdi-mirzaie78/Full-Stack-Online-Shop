"""Transient registry errors may recover; invalid images and assertions must fail."""
import unittest
from unittest.mock import Mock, patch

from check_observability import pull_images


class PullImagesTests(unittest.TestCase):
    @patch("check_observability.time.sleep")
    def test_recovers_after_docker_hub_502(self, sleep):
        docker = Mock(side_effect=[AssertionError("received unexpected HTTP status: 502 Bad Gateway"), "pulled"])
        pull_images(docker)
        self.assertEqual(docker.call_args_list, [(('pull', '--policy', 'missing'),), (('pull', '--policy', 'missing'),)])
        sleep.assert_called_once_with(5)

    @patch("check_observability.time.sleep")
    def test_exhausted_errors_still_fail(self, sleep):
        docker = Mock(side_effect=AssertionError("503 Service Unavailable"))
        with self.assertRaisesRegex(AssertionError, "503"):
            pull_images(docker)
        self.assertEqual(docker.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    @patch("check_observability.time.sleep")
    def test_permanent_errors_fail_without_retry(self, sleep):
        for message in ("manifest unknown", "unauthorized", "permission denied", "invalid config"):
            docker = Mock(side_effect=AssertionError(message))
            with self.assertRaisesRegex(AssertionError, message):
                pull_images(docker)
            docker.assert_called_once_with("pull", "--policy", "missing")
        sleep.assert_not_called()
