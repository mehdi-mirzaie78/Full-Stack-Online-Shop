"""Run with server/.venv/bin/python -m unittest discover -s scripts -p 'test_ci_*.py'."""
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class WorkflowTests(unittest.TestCase):
    def test_independent_fail_closed_gates(self):
        workflow = ROOT / ".github/workflows/ci.yml"
        self.assertTrue(workflow.exists())
        data = yaml.safe_load(workflow.read_text())
        self.assertEqual(set(data["on"]), {"push", "pull_request", "workflow_dispatch"})
        self.assertEqual(data["permissions"], {"contents": "read"})
        self.assertEqual(set(data["jobs"]), {"static", "client", "server", "browser", "observability"})
        for job in data["jobs"].values():
            self.assertLessEqual(job["timeout-minutes"], 20)
            self.assertFalse(job.get("continue-on-error", False))
        self.assertNotIn("services", data["jobs"]["server"])
        commands = "\n".join(str(s.get("run", "")) for s in data["jobs"]["server"]["steps"])
        self.assertIn("python scripts/run_tests.py backend", commands)
        self.assertIn("--cov-fail-under=85", (ROOT / "scripts/run_tests.py").read_text())
        browser_commands = "\n".join(str(s.get("run", "")) for s in data["jobs"]["browser"]["steps"])
        self.assertIn("python scripts/run_tests.py e2e", browser_commands)
        raw = workflow.read_text()
        self.assertNotIn("pull_request_target", raw)
        self.assertNotIn("secrets.", raw)
        for job in data["jobs"].values():
            for step in job["steps"]:
                if "uses" in step:
                    self.assertRegex(step["uses"], r"@[0-9a-f]{40}$")
                if step.get("uses", "").startswith("actions/checkout@"):
                    self.assertIs(step["with"]["persist-credentials"], False)
        self.assertIn("npm ci", raw)
        self.assertIn("npm --prefix client ci", raw)


if __name__ == "__main__":
    unittest.main()
