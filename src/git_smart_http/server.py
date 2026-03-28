import logging
import os
import subprocess
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import List, Optional

logger = logging.getLogger(__name__)

class GitSmartHTTPHandler(SimpleHTTPRequestHandler):
    """
    Custom HTTP request handler for Git Smart HTTP protocol.
    Extends SimpleHTTPRequestHandler to provide Git-specific endpoints and fallback to static file serving.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize the handler with repository directory and trusted hosts.

        :param args: Positional arguments for SimpleHTTPRequestHandler.
        :param kwargs: Keyword arguments, including 'directory' for repo storage and 'trusted_hosts'.
        """
        self.repo_dir = kwargs.get('directory', os.getcwd())
        self.trusted_hosts = kwargs.pop('trusted_hosts', ['127.0.0.1', 'localhost'])
        super().__init__(*args, **kwargs)

    def is_trusted(self) -> bool:
        """
        Check if the client's IP address is in the list of trusted hosts.

        :return: True if trusted, False otherwise.
        :rtype: bool
        """
        client_address = self.client_address[0]
        return client_address in self.trusted_hosts

    def do_GET(self):
        """
        Handle GET requests. Routes to Git info/refs or falls back to SimpleHTTPRequestHandler.
        """
        path = urllib.parse.urlparse(self.path).path
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)

        if path.endswith('/info/refs'):
            service = query.get('service', [None])[0]
            if service in ['git-upload-pack', 'git-receive-pack']:
                self.handle_info_refs(path, service)
                return

        # Fallback to simple HTTP server
        super().do_GET()

    def do_POST(self):
        """
        Handle POST requests. Routes to git-upload-pack or git-receive-pack services.
        """
        path = urllib.parse.urlparse(self.path).path
        if path.endswith('/git-upload-pack'):
            self.handle_git_service(path, 'git-upload-pack')
        elif path.endswith('/git-receive-pack'):
            if not self.is_trusted():
                self.send_error(403, "Forbidden: Push only allowed from trusted hosts")
                return
            self.handle_git_service(path, 'git-receive-pack')
        else:
            self.send_error(404, "Not Found")

    def handle_info_refs(self, path: str, service: str):
        """
        Handle the Git info/refs advertisement request.

        :param path: The request path.
        :type path: str
        :param service: The requested Git service (git-upload-pack or git-receive-pack).
        :type service: str
        """
        repo_name = path.split('/info/refs')[0].strip('/')
        repo_path = os.path.join(self.repo_dir, repo_name)

        if not os.path.exists(repo_path):
            if self.is_trusted() and service == 'git-upload-pack':
                logger.info(f"Auto-creating repository: {repo_path}")
                os.makedirs(repo_path, exist_ok=True)
                subprocess.run(['git', 'init', '--bare'], cwd=repo_path, check=True)
            else:
                self.send_error(404, "Repository Not Found")
                return

        if service == 'git-receive-pack' and not self.is_trusted():
            self.send_error(403, "Forbidden: Push only allowed from trusted hosts")
            return

        self.send_response(200)
        self.send_header('Content-Type', f'application/x-{service}-advertisement')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()

        # Packet line format: 4 hex chars length + content
        # Service advertisement: # service=git-upload-pack\n0000
        prefix = f"# service={service}\n"
        length = f"{len(prefix) + 4:04x}"
        self.wfile.write(f"{length}{prefix}0000".encode('utf-8'))

        # Call git service with --stateless-rpc --advertise-refs
        cmd = ['git', service.split('git-')[-1], '--stateless-rpc', '--advertise-refs', repo_path]
        subprocess.run(cmd, stdout=self.wfile, check=True)

    def handle_git_service(self, path: str, service: str):
        """
        Handle Git service POST requests (upload-pack or receive-pack).

        :param path: The request path.
        :type path: str
        :param service: The Git service to execute.
        :type service: str
        """
        repo_name = path.split(f'/{service}')[0].strip('/')
        repo_path = os.path.join(self.repo_dir, repo_name)

        if not os.path.exists(repo_path):
            self.send_error(404, "Repository Not Found")
            return

        self.send_response(200)
        self.send_header('Content-Type', f'application/x-{service}-result')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()

        # Read POST body and pipe to git service
        content_length = int(self.headers.get('Content-Length', 0))
        
        # We use a subprocess to handle the git command
        cmd = ['git', service.split('git-')[-1], '--stateless-rpc', repo_path]
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Read body in chunks if necessary, but for simplicity we'll read all
        # Git Smart HTTP POSTs can be large, but usually they are manageable
        body = self.rfile.read(content_length)
        stdout, stderr = process.communicate(input=body)
        
        if stderr:
            logger.error(f"Git service error: {stderr.decode('utf-8')}")
        
        self.wfile.write(stdout)

def run_server(host: str, port: int, repo_dir: str, trusted_hosts: List[str]):
    """
    Run the Git Smart HTTP server.

    :param host: The host address to bind to.
    :type host: str
    :param port: The port number to bind to.
    :type port: int
    :param repo_dir: The directory where repositories are stored.
    :type repo_dir: str
    :param trusted_hosts: A list of IP addresses allowed to perform administrative actions (push, auto-create).
    :type trusted_hosts: List[str]
    """
    os.makedirs(repo_dir, exist_ok=True)
    
    def handler_factory(*args, **kwargs):
        return GitSmartHTTPHandler(*args, directory=repo_dir, trusted_hosts=trusted_hosts, **kwargs)
    
    server = HTTPServer((host, port), handler_factory)
    logger.info(f"Starting Git Smart HTTP server on {host}:{port}")
    logger.info(f"Repositories directory: {repo_dir}")
    logger.info(f"Trusted hosts: {trusted_hosts}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        server.server_close()
