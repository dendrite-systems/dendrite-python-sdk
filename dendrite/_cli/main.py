import argparse
import asyncio
import subprocess
import sys

from dendrite.browser.async_api import AsyncDendrite
from dendrite.logic.config import Config


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


async def setup_auth(url: str):
    try:
        async with AsyncDendrite() as browser:
            await browser.setup_auth(
                url=url,
                message="Please log in to the website. Once done, press Enter to continue...",
            )
    except Exception as e:
        print(f"Error during authentication setup: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Dendrite SDK CLI tool")
    parser.add_argument(
        "command", choices=["install", "auth"], help="Command to execute"
    )

    # Add auth-specific arguments
    parser.add_argument("--url", help="URL to navigate to for authentication")

    args = parser.parse_args()

    if args.command == "install":
        run_playwright_install()
    elif args.command == "auth":
        if not args.url:
            parser.error("The --url argument is required for the auth command")
        asyncio.run(setup_auth(args.url))


if __name__ == "__main__":
    main()
