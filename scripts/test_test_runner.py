"""Regression checks for test isolation and failure cleanup."""

import os
import subprocess
import unittest
from unittest.mock import patch

from run_tests import COMPOSE, test_environment, test_services


class TestRunnerTests(unittest.TestCase):
    def test_inherited_credentials_urls_and_proxies_are_not_forwarded(self):
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgres://production.invalid/shop",
                "AWS_SECRET_ACCESS_KEY": "never-forward-this",
                "HTTP_PROXY": "http://external.invalid",
                "NEXT_PUBLIC_API_URL": "https://production.invalid",
            },
        ):
            environment = test_environment()
        self.assertNotIn("DATABASE_URL", environment)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", environment)
        self.assertNotIn("HTTP_PROXY", environment)
        self.assertEqual(environment["NEXT_PUBLIC_API_URL"], "http://127.0.0.1:8100/api/v1")
        self.assertEqual(environment["DJANGO_SETTINGS_MODULE"], "config.test_settings")

    def test_inaccessible_docker_does_not_repeat_cleanup(self):
        with patch("run_tests.compose", side_effect=PermissionError("Docker access denied")) as compose:
            with self.assertRaises(PermissionError), test_services():
                self.fail("Unavailable Docker must not execute tests")
        compose.assert_called_once_with("down", "--volumes", "--remove-orphans")

    def test_cleanup_runs_when_service_startup_fails(self):
        with patch("run_tests.compose") as compose:
            compose.side_effect = [
                None,
                subprocess.CalledProcessError(1, "docker"),
                None,
            ]
            with self.assertRaises(subprocess.CalledProcessError), test_services():
                self.fail("Failed startup must not execute tests")
        self.assertEqual(compose.call_args.args, ("down", "--volumes", "--remove-orphans"))
        self.assertEqual(compose.call_count, 3)

    def test_cleanup_runs_when_tests_fail(self):
        with (
            patch("run_tests.compose") as compose,
            self.assertRaisesRegex(RuntimeError, "test failed"),
            test_services(),
        ):
            raise RuntimeError("test failed")
        self.assertEqual(compose.call_args.args, ("down", "--volumes", "--remove-orphans"))

    def test_compose_targets_only_the_test_project_and_no_environment_file(self):
        self.assertIn("shop-tests", COMPOSE)
        self.assertEqual(COMPOSE[COMPOSE.index("--env-file") + 1], os.devnull)
        self.assertTrue(COMPOSE[-1].endswith("infra/compose.test.yml"))
