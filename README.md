# Git Smart HTTP Server

A pure Python implementation of a Git Smart HTTP server with no run dependencies. Developed and maintained using **Google AI Studio**.

## Features
- Smart HTTP protocol support (`git-upload-pack`, `git-receive-pack`)
- Auto-creation of repositories for trusted hosts
- Push support for trusted hosts
- Simple HTTP server for non-smart requests
- Configurable via CLI

## Usage Documentation

### Installation
You can build the wheel using the provided `pyproject.toml`:
```bash
python3 -m pip install build
python3 -m build
pip install dist/*.whl
```

### Running the Server
Start the server with default settings (port 3000, repos in `./repos`):
```bash
# Using the module
PYTHONPATH=src python3 -m git_smart_http

# If installed via pip
git-smart-http
```

### CLI Options
- `repo_dir`: Positional argument for the directory to store repositories (default: repos).
- `-H`, `--host`: Host to bind to (default: 0.0.0.0).
- `-p`, `--port`: Port to bind to (default: 3000).
- `-v`, `--verbose`: Increase console verbosity (can be used multiple times).
- `-l`, `--logfile`: Enable logging to a file (file log level is always fixed at INFO).
- `-t`, `--trusted-host`: Add a trusted host IP (can be used multiple times).
- `--version`: Show the version number and exit.

### Client Usage
**Cloning:**
If the host is trusted, cloning a non-existent repository will auto-create it:
```bash
git clone http://localhost:3000/my-new-repo.git
```

**Pushing:**
Pushing is only allowed from trusted hosts:
```bash
git push origin main
```

**Listing Repositories:**
Open `http://localhost:3000/` in your browser to see the list of repositories using the built-in simple HTTP server.

## Authors
- **Fr. Br. George**
- **AI Studio Build**

## Development
This project was built using **Google AI Studio**. To run tests:
```bash
PYTHONPATH=src python3 -m pytest tests/test_server.py
```
