import shutil
import socket
import threading
import time
import unittest
import urllib.request
from pathlib import Path
from git_smart_http.server import run_server

class TestIPv6DualStack(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Find a free port
        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
            s.bind(('::', 0))
            cls.port = s.getsockname()[1]
        cls.repo_dir = Path("test_repos_ipv6")
        cls.trusted_addresses = ["127.0.0.1", "::1"]
        
        if cls.repo_dir.exists():
            shutil.rmtree(cls.repo_dir)
        cls.repo_dir.mkdir(parents=True)

        # Start server on :: (dual stack)
        cls.server_thread = threading.Thread(
            target=run_server,
            args=("::", cls.port, str(cls.repo_dir), cls.trusted_addresses),
            daemon=True
        )
        cls.server_thread.start()
        
        # Wait for server to start by polling
        start_time = time.time()
        while time.time() - start_time < 5:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{cls.port}/", timeout=1) as r:
                    if r.status == 200:
                        break
            except Exception:
                time.sleep(0.1)
        else:
            raise RuntimeError("Server failed to start within timeout")

    @classmethod
    def tearDownClass(cls):
        if cls.repo_dir.exists():
            shutil.rmtree(cls.repo_dir)

    def test_ipv4_access(self):
        url = f"http://127.0.0.1:{self.port}/"
        with urllib.request.urlopen(url) as response:
            self.assertEqual(response.status, 200)
            body = response.read().decode('utf-8')
            self.assertIn("Git Smart HTTP Server", body)

    def test_ipv6_access(self):
        # Check if IPv6 is supported on this host
        try:
            s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            s.close()
        except socket.error:
            self.skipTest("IPv6 not supported on this host")

        # Note: [::1] is the standard way to represent IPv6 loopback in a URL
        url = f"http://[::1]:{self.port}/"
        try:
            with urllib.request.urlopen(url) as response:
                self.assertEqual(response.status, 200)
                body = response.read().decode('utf-8')
                self.assertIn("Git Smart HTTP Server", body)
        except Exception as e:
            self.fail(f"Failed to access server via IPv6: {e}")

if __name__ == "__main__":
    unittest.main()
