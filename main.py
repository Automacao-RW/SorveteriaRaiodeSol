import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from view.app import interface

if __name__ == "__main__":
    interface()
    
