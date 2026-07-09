#!/usr/bin/env python3
"""Capture ADK Web screenshots by importing the committed raw event session.

This deliberately avoids a second Gemini call: screenshots always represent the same
raw evidence used by the article and do not consume model quota during documentation.
"""

import re
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8080/dev-ui/"
ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "assets" / "evidence" / "full-review.json"
OUT = ROOT / "assets" / "screenshots"


def screenshot(page, name: str) -> None:
    page.screenshot(path=str(OUT / name), full_page=False)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 900})
        page.goto(BASE_URL, wait_until="networkidle", timeout=60_000)

        select = page.get_by_role("button", name="Select an app")
        if select.is_visible():
            select.click()
            page.get_by_role("button", name="sandbox_analyst").last.click()

        new_session = page.get_by_role(
            "button", name=re.compile(r"new session", re.IGNORECASE)
        )
        new_session.click()
        with page.expect_file_chooser() as chooser:
            page.get_by_role("button", name="Import").click()
        chooser.value.set_files(str(EVIDENCE))

        try:
            page.get_by_text(
                "The sandboxed security review of the untrusted Python repository",
                exact=False,
            ).wait_for(state="visible", timeout=60_000)
        except Exception:
            screenshot(page, "adk-web-import-debug.png")
            print(page.locator("body").inner_text()[:6000])
            raise
        page.wait_for_timeout(500)
        ok = page.get_by_role("button", name="OK", exact=True)
        if ok.is_visible():
            ok.click()
        page.get_by_text(
            "start_review_workspace()", exact=True
        ).scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        screenshot(page, "adk-web-tool-sequence.png")

        page.get_by_text(
            "The sandboxed security review of the untrusted Python repository",
            exact=False,
        ).scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        screenshot(page, "adk-web-full-flow.png")

        # Select the exact function-response chip, not the call with arguments.
        page.get_by_role(
            "button", name="inspect_security_boundaries", exact=True
        ).click()
        page.wait_for_timeout(500)
        screenshot(page, "adk-web-security-probe.png")

        # Two test responses exist; the first is the intentionally failing baseline.
        page.get_by_role("button", name="run_test_suite", exact=True).first.click()
        page.wait_for_timeout(500)
        screenshot(page, "adk-web-failing-tests.png")
        browser.close()


if __name__ == "__main__":
    main()
