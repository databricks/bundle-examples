# This is the entry point for this example.
# By successfully importing the private wheel, we demonstrate that
# it is possible to include an arbitrary wheel file in your bundle
# directory, deploy it, and use it from within your code.
import example_private_wheel

if __name__ == '__main__':
    example_private_wheel.main()
