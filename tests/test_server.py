import shutil
import socket
import subprocess
import threading
import time
import unittest
import urllib.request
from pathlib import Path
from git_smart_http.server import run_server

class TestGitSmartHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = "127.0.0.1"
        # Find a free port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            cls.port = s.getsockname()[1]
        cls.repo_dir = Path("test_repos")
        cls.trusted_addresses = ["127.0.0.1", "::1"]
        
        if cls.repo_dir.exists():
            shutil.rmtree(cls.repo_dir)
        cls.repo_dir.mkdir(parents=True)

        cls.server_thread = threading.Thread(
            target=run_server,
            args=(cls.host, cls.port, str(cls.repo_dir), cls.trusted_addresses),
            daemon=True
        )
        cls.server_thread.start()
        time.sleep(1)  # Wait for server to start

    @classmethod
    def tearDownClass(cls):
        if cls.repo_dir.exists():
            shutil.rmtree(cls.repo_dir)

    def test_list_repositories(self):
        # The custom root handler should list directories in repo_dir
        # Create a dummy repository directory
        repo_name = "test-repo"
        (self.repo_dir / repo_name).mkdir(parents=True, exist_ok=True)
        
        url = f"http://{self.host}:{self.port}/"
        with urllib.request.urlopen(url) as response:
            self.assertEqual(response.status, 200)
            body = response.read().decode('utf-8')
            self.assertIn("Git Smart HTTP Server", body)
            self.assertIn(repo_name, body)
            self.assertIn("How to Use", body)
            self.assertIn("Create a New Repository", body)
            self.assertIn("Clone an Existing Repository", body)

    def test_repo_directory_listing(self):
        # Create a repo and a file inside it
        repo_name = "listing-repo"
        repo_path = self.repo_dir / repo_name
        repo_path.mkdir(parents=True, exist_ok=True)
        
        test_file = "test_file.txt"
        (repo_path / test_file).write_text("test content")
            
        # Request the repo directory listing
        url = f"http://{self.host}:{self.port}/{repo_name}/"
        with urllib.request.urlopen(url) as response:
            self.assertEqual(response.status, 200)
            body = response.read().decode('utf-8')
            # SimpleHTTPRequestHandler uses "Directory listing for ..."
            self.assertIn(f"Directory listing for /{repo_name}/", body)
            self.assertIn(test_file, body)

    def test_clone_auto_create(self):
        repo_name = "auto-created.git"
        repo_url = f"http://{self.host}:{self.port}/{repo_name}"
        clone_dir = Path("test_clone")
        
        if clone_dir.exists():
            shutil.rmtree(clone_dir)

        # Clone should auto-create the repo because we are on a trusted host
        subprocess.run(['git', 'clone', repo_url, str(clone_dir)], check=True)
        
        self.assertTrue((self.repo_dir / repo_name).exists())
        self.assertTrue(clone_dir.exists())
        
        shutil.rmtree(clone_dir)

    def test_push_pull(self):
        repo_name = "push-pull.git"
        repo_url = f"http://{self.host}:{self.port}/{repo_name}"
        clone_dir = Path("test_push_pull")
        
        if clone_dir.exists():
            shutil.rmtree(clone_dir)

        # 1. Clone (auto-creates)
        subprocess.run(['git', 'clone', repo_url, str(clone_dir)], check=True)
        
        # 2. Add a file and commit
        (clone_dir / "hello.txt").write_text("world")
        
        subprocess.run(['git', 'add', '.'], cwd=str(clone_dir), check=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=str(clone_dir), check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=str(clone_dir), check=True)
        subprocess.run(['git', 'commit', '-m', 'initial commit'], cwd=str(clone_dir), check=True)
        
        # 3. Push
        subprocess.run(['git', 'push', 'origin', 'master'], cwd=str(clone_dir), check=True)
        
        # 4. Clone to another dir to verify push
        clone_dir_2 = Path("test_clone_verify")
        if clone_dir_2.exists():
            shutil.rmtree(clone_dir_2)
            
        subprocess.run(['git', 'clone', repo_url, str(clone_dir_2)], check=True)
        self.assertTrue((clone_dir_2 / "hello.txt").exists())
        
        shutil.rmtree(clone_dir)
        shutil.rmtree(clone_dir_2)

if __name__ == "__main__":
    unittest.main()
