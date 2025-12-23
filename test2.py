from playwright.sync_api import Page, sync_playwright



def scrape_aqicn_station_from_page(page: Page) -> dict:
    # Wait until ANY known AQICN layout appears
    page.wait_for_function(
        """
        () => (
            document.querySelector("#station-header") ||
            document.querySelector("#aqiwgtvalue") ||
            document.querySelector("#cur_pm25")
        )
        """,
        polling=100,
        timeout=60000,
    )

    data = page.evaluate(
        """
            () => {
                const result = {
                    sourceLayout: null,
                    aqi: null,
                    message: null,
                    updated: null,
                    pm25: null,
                    pm10: null
                };

                /* =========================================================
                LAYOUT A — Station Page
                ========================================================= */
                const header = document.querySelector("#station-header");
                if (header) {
                    result.sourceLayout = "station-header";

                    // AQI number
                    result.aqi = header.querySelector("td")?.innerText?.trim() ?? null;
                    // AQI message
                    const main = header.querySelector("span");
                    const sub = main?.nextElementSibling;
                    if (main && sub) {
                        result.message =
                            main.innerText.trim() + " " + sub.innerText.trim();
                    }

                    // Updated time
                    result.updated = Array.from(header.querySelectorAll("span"))
                        .find(s => s.innerText.toLowerCase().startsWith("updated"))
                        ?.innerText?.trim() ?? null;

                    // PM table
                    document
                        .querySelectorAll("table.station-table-species tr")
                        .forEach(row => {
                            const nameEl = row.querySelector(".station-specie-name");
                            const valEl = row.querySelector(".station-specie-aqi");
                            if (!nameEl || !valEl) return;

                            const name = nameEl.innerText.replace(/\s+/g, "");
                            const val = valEl.innerText.trim();

                            if (name === "PM2.5") result.pm25 = val;
                            if (name === "PM10") result.pm10 = val;
                        });

                    return result;
                }

                /* =========================================================
                LAYOUT B — Widget Page
                ========================================================= */
                const aqiEl = document.querySelector("#aqiwgtvalue");
                if (aqiEl) {
                    result.sourceLayout = "widget";

                    result.aqi = aqiEl.innerText.trim();
                    result.message =
                        document.querySelector("#aqiwgtinfo")?.innerText?.trim() ?? null;
                    result.updated =
                        document.querySelector("#aqiwgtutime")?.innerText?.trim() ?? null;

                    result.pm25 =
                        document.querySelector("#cur_pm25")?.innerText?.trim() ?? null;
                    result.pm10 =
                        document.querySelector("#cur_pm10")?.innerText?.trim() ?? null;

                    return result;
                }

                /* =========================================================
                NOTHING FOUND
                ========================================================= */
                result.sourceLayout = "none";
                return result;
            }
        """
    )
    return data


def fetch_aqicn_station(URL: str) -> dict:
    # Standalone helper (creates its own browser). If you're already inside Playwright,
    # use scrape_aqicn_station_from_page(page) instead to avoid nested sync_playwright().
    with sync_playwright() as p:
        print("Fetching AQICN station:", URL)
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(URL, timeout=90000, wait_until="domcontentloaded")
            return scrape_aqicn_station_from_page(page)
        finally:
            browser.close()
