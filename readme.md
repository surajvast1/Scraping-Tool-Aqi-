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

