"""Headless preview renders of the viewer, one PNG per preset view."""
import asyncio
import os
import sys

from playwright.async_api import async_playwright

VIEWS = ["face", "threeq", "profile", "bust", "full", "shield"]


async def run(html_path, out_dir, views):
    os.makedirs(out_dir, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/opt/pw-browsers/chromium",
            args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        page = await browser.new_page(viewport={"width": 1100, "height": 1100}, device_scale_factor=1)
        page.on("console", lambda m: print("console:", m.text))
        await page.goto("file://" + os.path.abspath(html_path))
        await page.wait_for_function("window.__frameCount > 2", timeout=120000)
        for v in views:
            await page.evaluate(f"window.setView('{v}')")
            await page.wait_for_function("window.__frameCount > 0")
            await page.evaluate("window.__frameCount = 0")
            await page.wait_for_function("window.__frameCount > 3")
            await page.screenshot(path=os.path.join(out_dir, f"athena_{v}.png"))
            print("rendered", v)
        await browser.close()


if __name__ == "__main__":
    html = sys.argv[1]
    out = sys.argv[2]
    views = sys.argv[3].split(",") if len(sys.argv) > 3 else VIEWS
    asyncio.run(run(html, out, views))
