import os
import time
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright
from fastapi import FastAPI, Query, HTTPException
from starlette.concurrency import run_in_threadpool
from cpcb import fetchNearestCpcbStation
import sys

from test2 import scrape_aqicn_station_from_page_sync

app = FastAPI(title="AQI API", version="1.0")


def fetch_aqicn_via_map(station_name: str) -> dict:
    """
    Opens aqicn.org/map, searches for station name,
    clicks first dropdown result, returns scraped AQICN data.
    """

    with sync_playwright() as p:
        debug = 0
        headless = os.environ.get("HEADLESS", "0" if debug else "1") != "0"
        slow_mo_ms = int(os.environ.get("SLOW_MO_MS", "200") or "0")
        keep_open = os.environ.get("KEEP_OPEN") == "1"


        # You asked for ~1 second per letter (configurable).
        char_delay_ms = int(os.environ.get("AQICN_CHAR_DELAY_MS", "100") or "1")

        browser = p.chromium.launch(headless=headless, slow_mo=slow_mo_ms)
        page = browser.new_page()

        try:
            out_dir = Path(__file__).parent
            if debug:
                page.on(
                    "console",
                    lambda msg: print(f"[aqicn:console] {msg.type}: {msg.text}"),
                )

            # 1️⃣ Open AQICN map
            page.goto("https://aqicn.org/map", timeout=60000, wait_until="domcontentloaded")
            
            # 2️⃣ Wait for search input
            page.wait_for_selector("#full-page-search-input", timeout=60000)

            # 3️⃣ Type station name (letter-by-letter)
            search = page.locator("#full-page-search-input")
            search.fill("")
            search.type(station_name, delay=char_delay_ms)


            

            # 4️⃣ Wait for dropdown results
            page.wait_for_selector("#searchResults a", timeout=60000)

            # 5️⃣ Click first search result
            first = page.locator("#searchResults a").first
            # first.wait_for(state="visible", timeout=15000)
            # wait for domcontentloaded
            page.wait_for_load_state("domcontentloaded", timeout=60000)
            first.click()

            # 6️⃣ Wait for station panel to render (AQICN is a SPA; URL may stay /map)
            page.wait_for_selector(
                "#station-header, .aqivalue, table.station-table-species",
                timeout=60000,
            )

            station_url = page.url


            if debug:
                try:
                    station_header = page.locator("#station-header").inner_text(timeout=2000).strip()
                    # if station_header:
                        # print(f"[aqicn] station_header={station_header}")
                except Exception:
                    pass

            if keep_open and not headless:
                # print("KEEP_OPEN=1 set. Close the browser window (or wait 60s) to continue...")
                page.wait_for_timeout(60000)

            return scrape_aqicn_station_from_page_sync(page, station_url)
        finally:
            browser.close()


def fetch_combined_aqi(latitude: float, longitude: float) -> dict:
    url = "https://airquality.cpcb.gov.in/caaqms/iit_rss_feed_with_coordinates?"

    allow_insecure_tls = os.environ.get("CPCB_INSECURE_TLS") == "1"
    verify_tls = not allow_insecure_tls

    headers = {
        "Accept-Encoding": "gzip, deflate, br",
        "User-Agent": "Mozilla/5.0",
    }

    # ---------------- FETCH CPCB ----------------
    response = requests.get(
        url,
        timeout=20,
        verify=verify_tls,
        headers=headers,
    )
    response.raise_for_status()

    # ---------------- COMPUTE NEAREST ----------------
    nearest = fetchNearestCpcbStation(response.json(), latitude, longitude)
    if not nearest:
        raise HTTPException(status_code=404, detail="No CPCB station found for the given coordinates.")

    # ---------------- AQICN ----------------
    station_name = nearest.get("station", {}).get("name") or "NA"
    aqicn = fetch_aqicn_via_map(station_name)

    return {"nearestStation": nearest, "aqicn": aqicn}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/aqi")
async def aqi(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
) -> dict:
    # Playwright + requests here are sync/blocking; run them in a thread to keep Uvicorn responsive.
    return await run_in_threadpool(fetch_combined_aqi, latitude, longitude)


def main():
    # latitude = 12.9828393
    # longitude = 77.6791966
    # latitude = float(sys.argv[1])
    # longitude = float(sys.argv[2])
    if len(sys.argv) >= 3:
        latitude = float(sys.argv[1])
        longitude = float(sys.argv[2])

    print("Using coordinates:", latitude, longitude)

    

    print("Fetching combined AQI...")
    t0 = time.perf_counter()
    result = fetch_combined_aqi(latitude, longitude)
    print(f"done {time.perf_counter() - t0:.3f}s")

    print("\nFINAL RESULT\n")
    print(result)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Error:", e)
