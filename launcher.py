"""PyInstaller entry point.

Must live outside the package and use absolute imports: a script inside the
package run as the frozen __main__ has no parent package, so relative imports
crash at startup.
"""

import sys

from vnlens.main import main

if __name__ == "__main__":
    sys.exit(main())
