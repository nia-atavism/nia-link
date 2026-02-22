"""
Nia-Link Page Observer v0.9
Captures page state changes before and after interactions — URL, cookies, DOM mutations, console logs.
"""

import logging
from typing import Dict, List, Optional
from playwright.async_api import Page

logger = logging.getLogger("nia-link.observer")


class PageObserver:
    """
    Observes and records page state changes during interactions.
    
    Usage:
        observer = PageObserver()
        before = await observer.capture_state(page)
        # ... do interactions ...
        after = await observer.capture_state(page)
        diff = observer.compute_diff(before, after)
    """

    async def capture_state(self, page: Page) -> Dict:
        """
        Capture the current page state: URL, title, cookies, visible text, console.
        
        Returns:
            Dict with keys: url, title, cookies, dom_signature, forms
        """
        state = {
            "url": page.url,
            "title": await page.title(),
            "cookies": [],
            "dom_signature": {},
            "forms": [],
            "console_errors": []
        }

        # Capture cookies
        try:
            context = page.context
            cookies = await context.cookies()
            state["cookies"] = [
                {"name": c["name"], "domain": c.get("domain", ""), "value": c["value"][:20] + "..." if len(c.get("value", "")) > 20 else c.get("value", "")}
                for c in cookies
            ]
        except Exception as e:
            logger.debug(f"Cookie capture failed: {e}")

        # Capture DOM signature (element counts for key types)
        try:
            state["dom_signature"] = await page.evaluate("""() => {
                return {
                    forms: document.forms.length,
                    inputs: document.querySelectorAll('input').length,
                    buttons: document.querySelectorAll('button').length,
                    links: document.querySelectorAll('a').length,
                    images: document.querySelectorAll('img').length,
                    alerts: document.querySelectorAll('[role="alert"], .alert, .error, .success, .notification').length,
                    modals: document.querySelectorAll('[role="dialog"], .modal, .popup').length
                }
            }""")
        except Exception as e:
            logger.debug(f"DOM signature capture failed: {e}")

        # Capture visible forms
        try:
            state["forms"] = await page.evaluate("""() => {
                return Array.from(document.forms).slice(0, 5).map(form => ({
                    id: form.id || null,
                    action: form.action || null,
                    method: form.method || 'get',
                    fields: form.elements.length
                }))
            }""")
        except Exception as e:
            logger.debug(f"Form capture failed: {e}")

        return state

    def compute_diff(self, before: Dict, after: Dict) -> Dict:
        """
        Compare two page states and return a structured diff.
        
        Returns:
            Dict describing what changed between the two states.
        """
        diff = {
            "url_changed": before["url"] != after["url"],
            "title_changed": before["title"] != after["title"],
            "cookies_gained": [],
            "cookies_lost": [],
            "dom_changes": [],
            "new_alerts": 0,
            "new_modals": 0
        }

        if diff["url_changed"]:
            diff["old_url"] = before["url"]
            diff["new_url"] = after["url"]

        if diff["title_changed"]:
            diff["old_title"] = before["title"]
            diff["new_title"] = after["title"]

        # Cookie diff
        before_names = {c["name"] for c in before.get("cookies", [])}
        after_names = {c["name"] for c in after.get("cookies", [])}
        diff["cookies_gained"] = list(after_names - before_names)
        diff["cookies_lost"] = list(before_names - after_names)

        # DOM signature diff
        before_dom = before.get("dom_signature", {})
        after_dom = after.get("dom_signature", {})
        for key in set(list(before_dom.keys()) + list(after_dom.keys())):
            bv = before_dom.get(key, 0)
            av = after_dom.get(key, 0)
            if bv != av:
                diff["dom_changes"].append(f"{key}: {bv} → {av}")

        # Alert/modal changes
        diff["new_alerts"] = max(0, after_dom.get("alerts", 0) - before_dom.get("alerts", 0))
        diff["new_modals"] = max(0, after_dom.get("modals", 0) - before_dom.get("modals", 0))

        # Console errors from after state
        diff["console_errors"] = after.get("console_errors", [])

        return diff

    def setup_console_listener(self, page: Page, state: Dict):
        """
        Attach a console listener to capture errors during interactions.
        Call this before running actions, pass the 'after' state dict.
        """
        def on_console(msg):
            if msg.type in ("error", "warning"):
                state.setdefault("console_errors", []).append({
                    "type": msg.type,
                    "text": msg.text[:200]
                })
        page.on("console", on_console)
