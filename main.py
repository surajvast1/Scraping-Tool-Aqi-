import os
import requests
from fastapi import FastAPI, Query, HTTPException
from playwright.async_api import async_playwright

from cpcb import fetchNearestCpcbStation
from test2 import scrape_aqicn_station_from_page  # scrape directly from the current page

app = FastAPI(title="AQI API", version="1.0")


def _to_absolute_aqicn_url(href: str | None) -> str | None:
    if not href:
        return None
    trimmed = href.strip()
    if not trimmed:
        return None
    if trimmed.startswith("http://") or trimmed.startswith("https://"):
        return trimmed
    if trimmed.startswith("/"):
        return f"https://aqicn.org{trimmed}"
    # Best-effort fallback (covers relative paths without leading slash)
    return f"https://aqicn.org/{trimmed.lstrip('/')}"


async def fetch_aqicn_via_map(station_name: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )

        page = await browser.new_page()

        try:
            # AQICN is flaky / SPA-driven. Retry once if the station panel doesn't load.
            last_err: Exception | None = None
            for _attempt in range(2):
                try:
                    await page.goto(
                        "https://aqicn.org/map",
                        timeout=60000,
                        wait_until="domcontentloaded",
                    )

                    await page.wait_for_selector("#full-page-search-input", timeout=60000)

                    search = page.locator("#full-page-search-input")
                    await search.fill("")
                    await search.type(station_name, delay=15)
                    await page.wait_for_timeout(600)

                    await page.wait_for_selector("#searchResults a", timeout=60000)

                    # Prefer the result href (more stable than relying on page.url staying in sync).
                    first_link = page.locator("#searchResults a").first
                    await first_link.wait_for(state="visible", timeout=15000)

                    href = await first_link.get_attribute("href")
                    candidate_url = _to_absolute_aqicn_url(href)

                    if candidate_url:
                        await page.goto(
                            candidate_url,
                            timeout=60000,
                            wait_until="domcontentloaded",
                        )
                    else:
                        await first_link.click()

                    # Wait for station content (either station page or station panel within /map).
                    await page.wait_for_selector(
                        "#station-header, .aqivalue, table.station-table-species, #aqiwgtvalue, #cur_pm25",
                        timeout=60000,
                    )

                    effective_url = candidate_url or page.url
                    return await scrape_aqicn_station_from_page(page, effective_url)
                except Exception as e:
                    last_err = e
                    # Try again from a clean state.
                    try:
                        await page.goto("about:blank")
                    except Exception:
                        pass

            raise last_err or RuntimeError("Failed to load AQICN station data")

        finally:
            await browser.close()


@app.get("/aqi")
async def get_aqi(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
):
    try:
        url = "https://airquality.cpcb.gov.in/caaqms/iit_rss_feed_with_coordinates?"

        headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "User-Agent": "Mozilla/5.0",
        }

        response = requests.get(url, timeout=20, headers=headers)
        response.raise_for_status()

        nearest = fetchNearestCpcbStation(
            response.json(),
            lat,
            lon,
        )

        if not nearest:
            raise HTTPException(status_code=404, detail="No CPCB station found")

        aqicn = await fetch_aqicn_via_map(nearest["station"]["name"])

        return {
            "latitude": lat,
            "longitude": lon,
            "nearestStation": nearest,
            "aqicn": aqicn,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
