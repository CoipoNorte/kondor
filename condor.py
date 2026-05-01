import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import AutoBuilder

if __name__ == "__main__":
    app = AutoBuilder()
    app.run()
