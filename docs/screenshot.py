"""Takes a screenshot of the running Streamlit dashboard (run inside the Playwright Docker image)."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1400, "height": 2000})
    page.goto("http://host.docker.internal:8501", wait_until="networkidle")
    page.wait_for_timeout(6000)
    page.screenshot(path="/out/dashboard.png", full_page=True)
    browser.close()
