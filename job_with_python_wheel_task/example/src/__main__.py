"""
The entry point of the Python Wheel
"""

import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "common"))

from lib import some_lib_method


def main():
    # This method will print the provided arguments
    print("Hello from my example")
    some_lib_method()


if __name__ == "__main__":
    main()
