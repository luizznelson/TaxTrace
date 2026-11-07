import importlib.util
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch


class SmokeCleanupTest(unittest.TestCase):
    def test_creation_error_still_attempts_to_stop_named_test_container(self):
        path = Path(__file__).resolve().parent.parent / "scripts/smoke_container.py"
        spec = importlib.util.spec_from_file_location("smoke_cleanup_test", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with patch.object(
            module, "docker", side_effect=[subprocess.CalledProcessError(1, "docker"), ""]
        ) as docker:
            result = module.verificar("taxtrace:synthetic-test")
        self.assertFalse(result["aprovado"])
        self.assertEqual(result["tipo_de_falha"], "CalledProcessError")
        self.assertTrue(result["container_de_teste"].startswith("taxtrace-smoke-"))
        self.assertEqual(docker.call_count, 2)
        self.assertEqual(
            docker.call_args.args, ("stop", "--time", "5", result["container_de_teste"])
        )


if __name__ == "__main__":
    unittest.main()
