# Git Smart HTTP Server

[![Tests](https://github.com/frbrgeorge/git-smart-http/actions/workflows/test.yml/badge.svg)](https://github.com/frbrgeorge/git-smart-http/actions/workflows/test.yml)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/frbrgeorge/git-smart-http)](https://github.com/frbrgeorge/git-smart-http/releases)

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
- `-b`, `--browser`: Open the server URL in the default web browser.
- `--version`: Show the version number and exit.

### Client Usage
A **trusted host** is an IP address explicitly allowed to perform write operations (pushing and auto-creating repositories) via the `-t` or `--trusted-host` CLI option. By default, only `127.0.0.1` is trusted if no other hosts are specified.

**Creating a new repository:**
If the host is trusted, cloning a non-existent repository will auto-create it:
```bash
git clone http://localhost:3000/my-new-repo.git
```

**Cloning:**
- **Read-Write Access (Trusted Host):**
  Cloning from a trusted host allows full smart HTTP protocol support, including pushing back to the server.
  ```bash
  git clone http://localhost:3000/repo.git
  ```
- **Read-Only Access (Untrusted Host):**
  Untrusted hosts can still clone existing repositories but cannot push or trigger auto-creation.
  ```bash
  # Assuming the server is running on 192.168.1.50 and this host is not trusted
  git clone http://192.168.1.50:3000/repo.git
  ```

**Pushing:**
Pushing is only allowed from trusted hosts.
```bash
git push origin main
```

**Listing Repositories:**
Open `http://localhost:3000/` in your browser to see the list of repositories using the built-in simple HTTP server.

## Authors
- **[Fr. Br. George](https://github.com/frbrgeorge)**
- **[AI Studio Build](https://ai.studio/build)**

## Development
This project was built using **Google AI Studio**. To run tests:
```bash
PYTHONPATH=src python3 -m pytest tests/test_server.py
```
