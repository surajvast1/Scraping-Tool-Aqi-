# 🌍 AQI Scraper (CPCB + AQICN)

A production-ready Air Quality Index (AQI) scraper that:

- Fetches **nearest CPCB monitoring station** based on latitude & longitude
- Uses **Haversine distance** for accurate proximity calculation
- Scrapes **real-time AQI data from AQICN** using Playwright (Chromium)
- Runs fully **headless**, **Dockerized**, and **cloud-ready**
- Deployable for free on **Railway**

---

## 🧠 How it works

1. Fetches all CPCB stations from the official CPCB API
2. Computes the nearest station using geographic distance
3. Searches the station on `aqicn.org/map`
4. Extracts live AQI data from the station page
5. Outputs combined CPCB + AQICN data

---

## 📦 Project Structure
---

## 🚀 Run locally

Install dependencies:

```bash
cd scraping-aqi
pip install -r requirements.txt
playwright install chromium
```

Start the API:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Health check:

- `GET /health`

Fetch combined AQI:

- `GET /aqi?latitude=12.9828393&longitude=77.6791966`

---

## 🚄 Deploy on Railway (Docker)

- Create a new Railway project
- Add a new service from **GitHub repo**
- Set the **Root Directory** to `scraping-aqi` (important)
- Railway will detect the `Dockerfile` and build it
- No start command needed (Docker `CMD` runs `uvicorn`)

Notes:
- Railway injects the `PORT` env var automatically; the container binds to it.
- If CPCB TLS verification fails in your environment, set `CPCB_INSECURE_TLS=1` (not recommended for production).


