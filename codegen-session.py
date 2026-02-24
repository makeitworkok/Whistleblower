# Copyright (c) 2025-2026 Chris Favre - MIT License
# See LICENSE file for full terms
import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width":1920,"height":1080})
    page = context.new_page()
    page.goto("https://tracersynchronydemo.trane.com/hui/index.html")
    page.locator("#userid").click()
    page.get_by_role("textbox", name="User ID").fill("SalesDemo")
    page.get_by_role("textbox", name="User ID").press("Tab")
    page.get_by_role("textbox", name="Password").fill("DemoSales")
    page.get_by_role("button", name="Log In").click()
    page.goto("https://tracersynchronydemo.trane.com/hui/hui.html#app=graphics&view=STATUS&obj=/uidata/Custom%20Graphics/CHWS/CHWS.html")

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
