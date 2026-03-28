import logging
import os
import socket
import subprocess
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import List, Optional

logger = logging.getLogger(__name__)

ROOT_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Git Smart HTTP Server</title>
    <style>
        body {{ font-family: sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; background: #f4f4f9; color: #333; }}
        h1 {{ border-bottom: 2px solid #333; padding-bottom: 10px; }}
        h2 {{ color: #444; margin-top: 30px; }}
        pre {{ background: #eee; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ background: #fff; margin-bottom: 10px; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .repo-name {{ font-weight: bold; font-size: 1.2em; display: block; margin-bottom: 5px; }}
        .link-group {{ margin-top: 10px; }}
        .link-label {{ font-size: 0.9em; color: #666; width: 100px; display: inline-block; }}
        code {{ background: #f9f9f9; padding: 2px 5px; border-radius: 3px; font-family: monospace; }}
        .trusted-info {{ font-size: 0.8em; color: #888; margin-top: 5px; }}
    </style>
</head>
<body>
    <h1>Git Smart HTTP Server</h1>
    
    <h2>Available Repositories</h2>
    {repo_list_html}

    <h2>How to Use</h2>
    
    <h3>Create a New Repository</h3>
    <p>To create a new repository, simply push to a non-existent path from a trusted host:</p>
    <pre>git remote add origin http://localhost:{port}/my-new-repo
git push -u origin main</pre>

    <h3>Clone an Existing Repository</h3>
    <p>From any host:</p>
    <pre>git clone http://{local_ip}:{port}/repository-name</pre>
    
    <p>From a trusted host (allows pushing back):</p>
    <pre>git clone http://localhost:{port}/repository-name</pre>

    <hr>
    <p style="font-size: 0.8em; color: #777;">Server IP: {local_ip} | Port: {port}</p>
</body>
</html>
"""

REPO_ITEM_HTML_TEMPLATE = """
<li>
    <span class="repo-name">{repo}</span>
    <div class="link-group">
        <span class="link-label">Read/Write:</span> <code>http://localhost:{port}/{repo}</code>
        <div class="trusted-info">(Only accessible from trusted hosts: {trusted_hosts})</div>
    </div>
    <div class="link-group">
        <span class="link-label">Read-Only:</span> <code>http://{local_ip}:{port}/{repo}</code>
    </div>
</li>
"""

def get_local_ip() -> str:
    """
    Determine the local IP address of the server.

    :return: The local IP address.
    :rtype: str
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

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
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        if path == '/' or path == '':
            self.handle_root()
            return

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

    def handle_root(self):
        """
        Serve a simple HTML page listing repositories and providing instructions.
        """
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()

        local_ip = get_local_ip()
        port = self.server.server_port
        
        # List repositories
        repos = []
        if os.path.exists(self.repo_dir):
            for entry in os.listdir(self.repo_dir):
                if os.path.isdir(os.path.join(self.repo_dir, entry)):
                    repos.append(entry)
        repos.sort()

        if repos:
            repo_items = []
            trusted_hosts_str = ", ".join(self.trusted_hosts)
            for repo in repos:
                item = REPO_ITEM_HTML_TEMPLATE.format(
                    repo=repo,
                    port=port,
                    trusted_hosts=trusted_hosts_str,
                    local_ip=local_ip
                )
                repo_items.append(item)
            repo_list_html = "<ul>" + "".join(repo_items) + "</ul>"
        else:
            repo_list_html = "<p>No repositories found.</p>"

        html = ROOT_HTML_TEMPLATE.format(
            repo_list_html=repo_list_html,
            local_ip=local_ip,
            port=port
        )
        self.wfile.write(html.encode('utf-8'))

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
