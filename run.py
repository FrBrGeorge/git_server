import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from git_smart_http.__main__ import main

if __name__ == "__main__":
    main()
