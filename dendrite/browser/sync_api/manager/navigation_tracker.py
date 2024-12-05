import time
import time
from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from ..dendrite_page import Page


class NavigationTracker:

    def __init__(self, page: "Page"):
        self.playwright_page = page.playwright_page
        self._nav_start_timestamp: Optional[float] = None
        self.playwright_page.on("framenavigated", self._on_frame_navigated)
        self.playwright_page.on("popup", self._on_popup)
        self._last_events: Dict[str, Optional[float]] = {
            "framenavigated": None,
            "popup": None,
        }

    def _on_frame_navigated(self, frame):
        self._last_events["framenavigated"] = time.time()
        if frame is self.playwright_page.main_frame:
            self._last_main_frame_url = frame.url
            self._last_frame_navigated_timestamp = time.time()

    def _on_popup(self, page):
        self._last_events["popup"] = time.time()

    def start_nav_tracking(self):
        """Call this just before performing an action that might trigger navigation"""
        self._nav_start_timestamp = time.time()
        for event in self._last_events:
            self._last_events[event] = None

    def get_nav_events_since_start(self):
        """
        Returns which events have fired since start_nav_tracking() was called
        and how long after the start they occurred
        """
        if self._nav_start_timestamp is None:
            return "Navigation tracking not started. Call start_nav_tracking() first."
        results = {}
        for event, timestamp in self._last_events.items():
            if timestamp is not None:
                delay = timestamp - self._nav_start_timestamp
                results[event] = f"{delay:.3f}s"
            else:
                results[event] = "not fired"
        return results

    def has_navigated_since_start(self):
        """Returns True if any navigation event has occurred since start_nav_tracking()"""
        if self._nav_start_timestamp is None:
            return False
        start_time = time.time()
        max_wait = 1.0
        while time.time() - start_time < max_wait:
            if any(
                (
                    timestamp is not None and timestamp > self._nav_start_timestamp
                    for timestamp in self._last_events.values()
                )
            ):
                return True
            time.sleep(0.1)
        return False
