# app/utils/file_generation.py

import io
import zipfile
import logging
import asyncio
import os
from typing import Optional, Dict

from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)
if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


# -------------------------------------------------------------------
# Capture PDF directly from a URL (BEST + STABLE APPROACH)
# -------------------------------------------------------------------
def _capture_pdf_sync(url: str) -> Optional[bytes]:
    try:
        logger.info("Playwright sync capture start url=%s", url)
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )

            page = browser.new_page()

            response = page.goto(url, wait_until="domcontentloaded", timeout=60000)
            if response:
                logger.info("Playwright sync response status=%s", response.status)
            if response and response.status >= 400:
                raise ValueError(f"Bad response status: {response.status}")

            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except Exception:
                pass

            try:
                page.wait_for_function(
                    "document.body && document.body.innerText && document.body.innerText.trim().length > 200",
                    timeout=15000,
                )
            except Exception:
                pass
            try:
                text_length = page.evaluate("document.body && document.body.innerText ? document.body.innerText.trim().length : 0")
                logger.info("Playwright sync text length=%s", text_length)
            except Exception:
                logger.exception("Playwright sync text length check failed")

            page.emulate_media(media="screen", color_scheme="light", forced_colors="none")
            try:
                page.add_style_tag(content="""
                  :root { color-scheme: light !important; }
                  html, body { background: #ffffff !important; background-color: #ffffff !important; }
                  * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; box-shadow: none !important; text-shadow: none !important; filter: none !important; }
                """)
            except Exception:
                logger.exception("Playwright sync CSS inject failed")

            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                margin={
                    "top": "20px",
                    "right": "20px",
                    "bottom": "20px",
                    "left": "20px",
                },
            )

            browser.close()
            if not pdf_bytes:
                logger.error("Playwright PDF capture returned empty bytes")
                return None
            logger.info("Playwright sync PDF bytes=%s", len(pdf_bytes))
            return pdf_bytes

    except Exception:
        logger.exception("Playwright sync PDF capture failed")
        return None


async def capture_pdf_and_html(url: str) -> Optional[bytes]:
    """
    Loads a frontend URL in Chromium and exports a high-fidelity PDF.
    Works on:
    - Python 3.13
    - Windows
    - FastAPI / Starlette
    """

    if os.name == "nt":
        logger.info("Playwright capture using sync path on Windows url=%s", url)
        return await asyncio.to_thread(_capture_pdf_sync, url)

    try:
        logger.info("Playwright async capture start url=%s", url)
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )

            page = await browser.new_page()

            response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            if response:
                logger.info("Playwright async response status=%s", response.status)
            if response and response.status >= 400:
                raise ValueError(f"Bad response status: {response.status}")

            try:
                await page.wait_for_load_state("networkidle", timeout=30000)
            except Exception:
                pass

            try:
                await page.wait_for_function(
                    "document.body && document.body.innerText && document.body.innerText.trim().length > 200",
                    timeout=15000,
                )
            except Exception:
                pass
            try:
                text_length = await page.evaluate("document.body && document.body.innerText ? document.body.innerText.trim().length : 0")
                logger.info("Playwright async text length=%s", text_length)
            except Exception:
                logger.exception("Playwright async text length check failed")

            await page.emulate_media(media="screen", color_scheme="light", forced_colors="none")
            try:
                await page.add_style_tag(content="""
                  :root { color-scheme: light !important; }
                  html, body { background: #ffffff !important; background-color: #ffffff !important; }
                  * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; box-shadow: none !important; text-shadow: none !important; filter: none !important; }
                """)
            except Exception:
                logger.exception("Playwright async CSS inject failed")

            pdf_bytes = await page.pdf(
                format="A4",
                print_background=True,
                margin={
                    "top": "20px",
                    "right": "20px",
                    "bottom": "20px",
                    "left": "20px",
                },
            )

            await browser.close()
            if not pdf_bytes:
                logger.error("Playwright PDF capture returned empty bytes")
                return None
            logger.info("Playwright async PDF bytes=%s", len(pdf_bytes))
            return pdf_bytes

    except NotImplementedError:
        return await asyncio.to_thread(_capture_pdf_sync, url)
    except Exception as e:
        if isinstance(e, NotImplementedError) or "NotImplementedError" in str(e):
            return await asyncio.to_thread(_capture_pdf_sync, url)
        logger.exception("Playwright PDF capture failed")
        return None


# -------------------------------------------------------------------
# OPTIONAL: High-fidelity HTML → PDF (ASYNC ONLY)
# Use ONLY if you MUST modify raw HTML before rendering
# -------------------------------------------------------------------
async def high_fidelity_html_to_pdf_bytes(html: str) -> Optional[bytes]:
    """
    Converts raw HTML into a PDF using Playwright.
    DO NOT call from threads.
    DO NOT wrap in asyncio.run().
    """

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )

            page = await browser.new_page()
            await page.set_content(html, wait_until="networkidle")
            await page.emulate_media(media="screen")
            try:
                await page.add_style_tag(content="""
                  :root { color-scheme: light !important; }
                  html, body { background: #ffffff !important; background-color: #ffffff !important; }
                  * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; box-shadow: none !important; text-shadow: none !important; filter: none !important; }
                """)
            except Exception:
                logger.exception("Playwright HTML CSS inject failed")

            pdf_bytes = await page.pdf(
                format="A4",
                print_background=True,
                margin={
                    "top": "20px",
                    "right": "20px",
                    "bottom": "20px",
                    "left": "20px",
                },
            )

            await browser.close()
            return pdf_bytes

    except Exception:
        logger.exception("HTML → PDF conversion failed")
        return None


# -------------------------------------------------------------------
# ZIP BUILDER
# -------------------------------------------------------------------
def build_zip(files: Dict[str, bytes]) -> io.BytesIO:
    """
    Builds an in-memory ZIP file.
    Raises if any file content is missing.
    """

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(
        zip_buffer,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as zf:
        for filename, content in files.items():
            if not content:
                raise ValueError(f"No content for file: {filename}")
            zf.writestr(filename, content)

    zip_buffer.seek(0)
    return zip_buffer
