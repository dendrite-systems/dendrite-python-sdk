from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union, overload
from loguru import logger
from typing_extensions import Literal

from dendrite.browser._common.constants import STEALTH_ARGS

if TYPE_CHECKING:
    from dendrite.browser.async_api._core.dendrite_browser import AsyncDendrite

from playwright.async_api import Browser, Download, Playwright, BrowserContext

from dendrite.browser.async_api._core._impl_browser import ImplBrowser
from dendrite.browser.async_api._core._type_spec import PlaywrightPage

import tempfile
import shutil
import os


class LocalImpl(ImplBrowser):
    def __init__(self) -> None:
        pass

    @overload
    async def start_browser(
        self, playwright: Playwright, pw_options: dict, user_data_dir: str
    ) -> BrowserContext: ...

    @overload
    async def start_browser(
        self, playwright: Playwright, pw_options: dict, user_data_dir: None = None
    ) -> Browser: ...

    async def start_browser(
        self,
        playwright: Playwright,
        pw_options: dict,
        user_data_dir: Optional[str] = None,
    ) -> Union[Browser, BrowserContext]:
        if user_data_dir is not None:
            args = {
                "user_data_dir": user_data_dir,
                "ignore_default_args": ["--enable-automation"],
            }
            
            # Check if profile is locked
            singleton_lock = os.path.join(user_data_dir, "SingletonLock")
            logger.warning(f"Checking for singleton lock at {os.path.abspath(singleton_lock)}")
            
            res = Path("/Users/arian/Projects/dendrite/dendrite-python-sdk/browser_profiles/my_google_profile/SingletonLock").is_symlink()
            if res:
                is_locked = True
            else:
                is_locked = False
            
            logger.warning(f"Profile is locked: {is_locked}")
            if is_locked:
                logger.warning("Profile is locked, creating a temporary copy")
                # Create a temporary copy of the user data directory
                temp_dir = tempfile.mkdtemp()
                temp_user_data = os.path.join(temp_dir, "chrome_data")
                
                def copy_ignore(src, names):
                    return [
                        'SingletonSocket', 'SingletonLock', 'SingletonCookie',
                        'DeferredBrowserMetrics', 'RunningChromeVersion',
                        '.org.chromium.Chromium.*'
                    ]
                
                # Copy tree with error handling
                shutil.copytree(
                    user_data_dir, 
                    temp_user_data, 
                    ignore=copy_ignore,
                    dirs_exist_ok=True
                )
                args["user_data_dir"] = temp_user_data
            
            pw_options.update(args)
            return await playwright.chromium.launch_persistent_context(
                channel="chrome",
                **pw_options
            )
        
        return await playwright.chromium.launch(**pw_options)

    async def get_download(
        self,
        dendrite_browser: "AsyncDendrite",
        pw_page: PlaywrightPage,
        timeout: float,
    ) -> Download:
        return await dendrite_browser._download_handler.get_data(pw_page, timeout)

    async def configure_context(self, browser: "AsyncDendrite"):
        pass

    async def stop_session(self):
        pass
