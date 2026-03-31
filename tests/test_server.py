import os
import shutil
import subprocess
import threading
import time
import unittest
import urllib.request
from git_smart_http.server import run_server

class TestGitSmartHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = "127.0.0.1"
        cls.port = 3001
        cls.repo_dir = "test_repos"
        cls.trusted_addresses = ["127.0.0.1", "localhost"]
        
        if os.path.exists(cls.repo_dir):
            shutil.rmtree(cls.repo_dir)
        os.makedirs(cls.repo_dir)

        cls.server_thread = threading.Thread(
            target=run_server,
            args=(cls.host, cls.port, cls.repo_dir, cls.trusted_addresses),
            daemon=True
        )
        cls.server_thread.start()
        time.sleep(1)  # Wait for server to start

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.repo_dir):
            shutil.rmtree(cls.repo_dir)

    def test_list_repositories(self):
        # The custom root handler should list directories in repo_dir
        # Create a dummy repository directory
        repo_name = "test-repo"
        os.makedirs(os.path.join(self.repo_dir, repo_name), exist_ok=True)
        
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
        repo_path = os.path.join(self.repo_dir, repo_name)
        os.makedirs(repo_path, exist_ok=True)
        
        test_file = "test_file.txt"
        with open(os.path.join(repo_path, test_file), "w") as f:
            f.write("test content")
            
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
        clone_dir = "test_clone"
        
        if os.path.exists(clone_dir):
            shutil.rmtree(clone_dir)

        # Clone should auto-create the repo because we are on a trusted host
        subprocess.run(['git', 'clone', repo_url, clone_dir], check=True)
        
        self.assertTrue(os.path.exists(os.path.join(self.repo_dir, repo_name)))
        self.assertTrue(os.path.exists(clone_dir))
        
        shutil.rmtree(clone_dir)

    def test_push_pull(self):
        repo_name = "push-pull.git"
        repo_url = f"http://{self.host}:{self.port}/{repo_name}"
        clone_dir = "test_push_pull"
        
        if os.path.exists(clone_dir):
            shutil.rmtree(clone_dir)

        # 1. Clone (auto-creates)
        subprocess.run(['git', 'clone', repo_url, clone_dir], check=True)
        
        # 2. Add a file and commit
        with open(os.path.join(clone_dir, "hello.txt"), "w") as f:
            f.write("world")
        
        subprocess.run(['git', 'add', '.'], cwd=clone_dir, check=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=clone_dir, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=clone_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'initial commit'], cwd=clone_dir, check=True)
        
        # 3. Push
        subprocess.run(['git', 'push', 'origin', 'master'], cwd=clone_dir, check=True)
        
        # 4. Clone to another dir to verify push
        clone_dir_2 = "test_clone_verify"
        if os.path.exists(clone_dir_2):
            shutil.rmtree(clone_dir_2)
            
        subprocess.run(['git', 'clone', repo_url, clone_dir_2], check=True)
        self.assertTrue(os.path.exists(os.path.join(clone_dir_2, "hello.txt")))
        
        shutil.rmtree(clone_dir)
        shutil.rmtree(clone_dir_2)

if __name__ == "__main__":
    unittest.main()
