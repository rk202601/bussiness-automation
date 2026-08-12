"""
scraper.py — Playwright-based Google Maps business lead scraper.

Uses stealth patches, ARIA selectors, and human-like delays to
extract business name, phone, and address from Google Maps listings.
"""

import logging
import random
import re
import time
from dataclasses import dataclass, field

from typing import Callable
from playwright.sync_api import sync_playwright, Page, Browser, Playwright, TimeoutError as PwTimeout

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Data model
# ──────────────────────────────────────────────────────────────

@dataclass
class Lead:
    name: str
    phone: str
    area: str
    state: str
    source: str = "Google Map"
    status: str = "Not Contacted"

    def to_row(self) -> list[str]:
        return [self.name, self.phone, self.area, self.state, self.source, self.status]


# ──────────────────────────────────────────────────────────────
# Scraper
# ──────────────────────────────────────────────────────────────

class GoogleMapsScraper:
    """Launches a Playwright browser and scrapes Google Maps search results."""

    MAPS_URL = "https://www.google.com/maps"

    def __init__(
        self,
        headless: bool = True,
        scroll_pause: float = 1.5,
        action_delay: float = 2.0,
    ):
        self.headless = headless
        self.scroll_pause = scroll_pause
        self.action_delay = action_delay

        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._context = None
        self._page: Page | None = None

    # ── Lifecycle ────────────────────────────────────────────

    def start(self) -> None:
        """Launch the browser with stealth settings."""
        logger.info("Launching browser (headless=%s)…", self.headless)
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        self._context = self._browser.new_context(
            viewport={"width": 1366, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        self._page = self._context.new_page()

        # Apply stealth patches
        try:
            from playwright_stealth import stealth_sync  # type: ignore
            stealth_sync(self._page)
            logger.info("Stealth patches applied.")
        except ImportError:
            logger.warning(
                "playwright-stealth not installed — running without stealth patches. "
                "Install it with: pip install playwright-stealth"
            )

    def stop(self) -> None:
        """Close browser, context, and Playwright cleanly + terminate zombie child processes."""
        if self._page:
            try:
                if not self._page.is_closed():
                    self._page.close()
            except Exception:
                pass
            self._page = None

        if self._context:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None

        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._pw:
            try:
                self._pw.stop()
            except Exception:
                pass
            self._pw = None

        _cleanup_zombie_child_processes()
        logger.info("Browser closed and zombie processes cleaned.")

    # ── Public API ───────────────────────────────────────────

    def scrape_all(
        self,
        keywords: list[str],
        cities: list[str],
        state: str,
    ) -> list[Lead]:
        """
        Iterate every city × keyword combination and return all leads found.
        Continues on individual failures.
        """
        all_leads: list[Lead] = []

        for city in cities:
            for keyword in keywords:
                query = f"{keyword} in {city}"
                logger.info("━━━ Searching: %s ━━━", query)
                try:
                    leads = self._search_and_extract(keyword, city, state)
                    all_leads.extend(leads)
                    logger.info(
                        "✓ Found %d leads for '%s'", len(leads), query
                    )
                except Exception:
                    logger.exception("✗ Failed for '%s' — skipping.", query)

        return all_leads

    # ── Internal workflow ────────────────────────────────────

    def _search_and_extract(
        self, keyword: str, city: str, state: str,
        on_lead: Callable[[Lead], None] | None = None,
    ) -> list[Lead]:
        """Search one keyword+city and extract all visible listings.

        on_lead: optional callback invoked immediately when each lead is extracted.
        """
        page = self._page
        assert page is not None

        # Build search URL directly — faster and more reliable than typing in the search box
        import urllib.parse
        query = f"{keyword} in {city}"
        search_url = f"https://www.google.com/maps/search/{urllib.parse.quote(query)}"
        logger.info("Navigating to: %s", search_url)

        page.goto(search_url, wait_until="domcontentloaded", timeout=30_000)
        self._human_delay()

        # Accept cookies/consent if present
        self._dismiss_consent(page)
        self._human_delay()

        # If search input exists, press Enter to trigger query submit if needed
        try:
            search_input = page.locator('#searchboxinput, input[name="q"]')
            if search_input.count() > 0 and search_input.first.is_visible():
                search_input.first.press("Enter")
                self._human_delay()
        except Exception:
            pass

        # Wait for results feed or listing links to appear
        feed_locator = page.locator('div[role="feed"], a[href*="/maps/place/"]')
        try:
            feed_locator.first.wait_for(state="visible", timeout=25_000)
        except PwTimeout:
            logger.warning("No results feed appeared for '%s' — may be zero results.", query)
            return []

        self._human_delay()

        # Scroll to load all results
        self._scroll_results(page)

        # Collect listing HREFs upfront — avoids stale element references after navigation
        listing_hrefs = self._get_listing_hrefs(page)
        logger.info("Found %d listing cards to process.", len(listing_hrefs))

        leads: list[Lead] = []
        for idx, href in enumerate(listing_hrefs, 1):
            try:
                # Always pass self._page so browser restart mid-loop uses the active page
                lead = self._extract_listing_by_url(self._page, href, idx, state, city)
                if lead:
                    leads.append(lead)
                    if on_lead is not None:
                        on_lead(lead)
            except Exception:
                logger.exception("  Failed to extract listing #%d — skipping.", idx)

            # ── Random pause every 10 listings (anti rate-limit) ──
            if idx % 10 == 0:
                wait = round(random.uniform(1.0, 10.0), 1)
                logger.info("")
                logger.info("  +------------------------------------------+")
                logger.info("  |  [PAUSE] Batch of 10 done (#%d-#%d)      ", idx - 9, idx)
                logger.info("  |  Waiting %.1fs to avoid rate limits...   ", wait)
                logger.info("  +------------------------------------------+")
                logger.info("")
                time.sleep(wait)

        return leads

    # ── Scrolling ────────────────────────────────────────────

    def _scroll_results(self, page: Page) -> None:
        """Scroll the results sidebar until all results are loaded."""
        previous_count = 0
        stale_rounds = 0
        max_stale = 5  # stop after 5 rounds of no new results

        while stale_rounds < max_stale:
            # Scroll feed or results container to bottom
            page.evaluate(
                """
                const feed = document.querySelector('div[role="feed"]') || document.querySelector('div[aria-label*="Results for"]');
                if (feed) feed.scrollTo(0, feed.scrollHeight);
                """
            )
            time.sleep(self.scroll_pause + random.uniform(0.3, 1.0))

            # Check if we've reached the end
            end_marker = page.locator('p.fontBodyMedium span:has-text("You\'ve reached the end")')
            if end_marker.count() > 0:
                logger.info("Reached end of results list.")
                break

            # Count current listings
            current_count = page.locator('a[href*="/maps/place/"]').count()
            if current_count == previous_count:
                stale_rounds += 1
            else:
                stale_rounds = 0
                previous_count = current_count

        logger.info("Scrolling complete. Total listing cards visible: %d", previous_count)

    # ── Listing collection ───────────────────────────────────

    def _get_listing_hrefs(self, page: Page) -> list[str]:
        """Collect all unique listing URLs from the results feed."""
        links = page.locator('a[href*="/maps/place/"]').all()
        seen = set()
        hrefs = []
        for link in links:
            try:
                href = link.get_attribute("href") or ""
                if href and href not in seen:
                    seen.add(href)
                    hrefs.append(href)
            except Exception:
                pass
        return hrefs

    # ── Detail extraction ────────────────────────────────────

    def _extract_listing_by_url(
        self, page: Page, href: str, idx: int, state: str, city: str
    ) -> Lead | None:
        """Navigate directly to a listing URL and extract lead details."""
        try:
            page.goto(href, wait_until="domcontentloaded", timeout=20_000)
        except Exception:
            logger.warning("  Could not navigate to listing #%d.", idx)
            return None

        self._human_delay(1.5)

        # Wait for the detail panel to load
        # Google Maps has TWO div[role="main"] elements: the results list + the detail panel.
        # The detail panel always has an aria-label with the business name.
        # We use .last to get the detail panel (it appears after the list panel).
        detail_panel = page.locator('div[role="main"][aria-label]')
        try:
            detail_panel.last.wait_for(state="visible", timeout=10_000)
        except Exception:
            logger.warning("  Detail panel didn't load for listing #%d.", idx)
            return None

        # ── Extract name ─────────────────────────────────────
        name = self._extract_name(page)
        if not name:
            logger.warning("  Could not extract name for listing #%d.", idx)
            return None

        # ── Extract phone ────────────────────────────────────
        phone = self._extract_phone(page)

        # ── Extract address ──────────────────────────────────
        area = self._extract_address(page, city)

        logger.info(
            "  #%d  %-35s  Phone: %-15s  Area: %s",
            idx, name[:35], phone or "(none)", area[:40] if area else "(none)"
        )

        return Lead(
            name=name,
            phone=phone,
            area=area,
            state=state,
        )

    def _extract_name(self, page: Page) -> str:
        """Extract business name from the detail panel."""
        # Primary: <h1> inside the detail panel (the one with aria-label)
        h1 = page.locator('div[role="main"][aria-label] h1')
        if h1.count() > 0:
            text = h1.first.inner_text().strip()
            if text:
                return text

        # Fallback: aria-label on the detail panel container
        main = page.locator('div[role="main"][aria-label]')
        if main.count() > 0:
            label = main.last.get_attribute("aria-label") or ""
            if label:
                return label.strip()

        return ""

    def _extract_phone(self, page: Page) -> str:
        """Extract phone number from the detail panel."""
        # Strategy 1: Button with data-tooltip="Copy phone number"
        phone_btn = page.locator('button[data-tooltip="Copy phone number"]')
        if phone_btn.count() > 0:
            aria = phone_btn.first.get_attribute("aria-label") or ""
            # aria-label is usually like "Phone: 098765 43210"
            match = re.search(r"[\d\s\-+()]{7,}", aria)
            if match:
                return match.group().strip()
            # Fallback: inner text
            text = phone_btn.first.inner_text().strip()
            match = re.search(r"[\d\s\-+()]{7,}", text)
            if match:
                return match.group().strip()

        # Strategy 2: Look for phone icon + text in info rows
        # Google Maps uses an <img> or icon with aria-label containing "Phone"
        phone_rows = page.locator('button[aria-label*="Phone"]')
        if phone_rows.count() > 0:
            label = phone_rows.first.get_attribute("aria-label") or ""
            match = re.search(r"[\d\s\-+()]{7,}", label)
            if match:
                return match.group().strip()

        # Strategy 3: Scan all text for Indian phone pattern
        try:
            all_text = page.locator('div[role="main"]').first.inner_text()
            # Indian phone numbers: +91, 0-prefixed, or plain 10-digit
            matches = re.findall(r'(?:\+91[\s-]?)?(?:0)?[6-9]\d{4}[\s-]?\d{5}', all_text)
            if matches:
                return matches[0].strip()
        except Exception:
            pass

        return ""

    def _extract_address(self, page: Page, city: str) -> str:
        """Extract address/area from the detail panel."""
        # Strategy 1: Button with data-tooltip="Copy address"
        addr_btn = page.locator('button[data-tooltip="Copy address"]')
        if addr_btn.count() > 0:
            aria = addr_btn.first.get_attribute("aria-label") or ""
            # aria-label is usually like "Address: 123, Main Rd, Sector 14, Gurugram"
            address = re.sub(r'^Address:\s*', '', aria, flags=re.IGNORECASE).strip()
            if address:
                return address

            text = addr_btn.first.inner_text().strip()
            if text:
                return text

        # Strategy 2: aria-label containing "Address"
        addr_rows = page.locator('button[aria-label*="Address"]')
        if addr_rows.count() > 0:
            label = addr_rows.first.get_attribute("aria-label") or ""
            address = re.sub(r'^Address:\s*', '', label, flags=re.IGNORECASE).strip()
            if address:
                return address

        # Fallback: return city name
        return city

    # ── Navigation helpers ───────────────────────────────────

    def _go_back_to_results(self, page: Page) -> None:
        """Navigate back to the results list from a detail view."""
        try:
            back_btn = page.locator('button[aria-label="Back"]')
            if back_btn.count() > 0:
                back_btn.first.click(timeout=3_000)
                self._human_delay(1.0)
                return
        except Exception:
            pass

        # Fallback: browser back
        try:
            page.go_back(wait_until="domcontentloaded", timeout=5_000)
            self._human_delay(1.0)
        except Exception:
            pass

    def _dismiss_consent(self, page: Page) -> None:
        """Dismiss Google consent/cookie dialogs if present."""
        try:
            # Common consent button selectors
            for selector in [
                'button:has-text("Accept all")',
                'button:has-text("Reject all")',
                'button[aria-label="Accept all"]',
                'form[action*="consent"] button',
            ]:
                btn = page.locator(selector)
                if btn.count() > 0:
                    btn.first.click(timeout=3_000)
                    self._human_delay(1.0)
                    logger.info("Dismissed consent dialog.")
                    return
        except Exception:
            pass

    # ── Delay helpers ────────────────────────────────────────

    def _human_delay(self, base: float | None = None) -> None:
        """Sleep a random duration to appear human-like and avoid rate limits.

        If base is given: sleeps base +/- 30% jitter.
        If base is None:  sleeps a fully random 1.0 – 3.0 s (navigation delay).
        """
        if base is None:
            duration = random.uniform(1.0, 3.0)
        else:
            jitter = base * 0.3
            duration = base + random.uniform(-jitter, jitter)
        time.sleep(max(0.5, duration))


def _cleanup_zombie_child_processes() -> None:
    """Force terminate any orphaned child processes (Chromium / Playwright node driver) of this script."""
    import os
    import subprocess

    pid = os.getpid()
    if os.name == "nt":  # Windows
        try:
            cmd = f'wmic process where (ParentProcessId={pid} and Name!="python.exe") get ProcessId'
            res = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=5)
            if res.returncode == 0:
                pids = [p.strip() for p in res.stdout.splitlines() if p.strip().isdigit()]
                for child_pid in pids:
                    subprocess.run(["taskkill", "/F", "/PID", child_pid], capture_output=True, check=False)
        except Exception:
            pass

