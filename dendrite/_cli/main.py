import argparse
import subprocess
import sys


def run_playwright_install():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
        print("Playwright browser installation completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error during Playwright browser installation: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(
            "Playwright command not found. Please ensure Playwright is installed in your environment."
        )
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Dendrite SDK CLI tool")
    parser.add_argument("command", choices=["install"], help="Command to execute")

    args = parser.parse_args()

    if args.command == "install":
        run_playwright_install()


if __name__ == "__main__":
    main()
