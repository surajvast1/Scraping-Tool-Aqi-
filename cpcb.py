import math
from typing import Any, Dict, Optional


# ------------------ Distance ------------------
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0  # Earth radius in km

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )

    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ------------------ Safe number parsing ------------------
def parse_finite_number(value: Any) -> Optional[float]:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(value) else None

    if isinstance(value, str):
        trimmed = value.strip()
        if not trimmed or trimmed.upper() == "NA":
            return None
        try:
            num = float(trimmed)
            return num if math.isfinite(num) else None
        except ValueError:
            return None

    return None


# ------------------ MAIN FUNCTION ------------------
def fetchNearestCpcbStation(
    cpcb_response: Dict[str, Any],
    user_lat: float,
    user_lon: float,
) -> Optional[Dict[str, Any]]:

    print("Fetching nearest CPCB station...")
    # print(cpcb_response)
    # print("User latitude:", user_lat)
    # print("User longitude:", user_lon)
    best_station = None
    best_distance = float("inf")

    root = cpcb_response or {}

    for state in root.get("country", []):
        for city in state.get("citiesInState", []):
            for station in city.get("stationsInCity", []):

                lat = parse_finite_number(station.get("latitude"))
                lon = parse_finite_number(station.get("longitude"))
                aqi = parse_finite_number(station.get("airQualityIndexValue"))

                # CPCB data can contain NA/empty fields. Skip stations without coordinates.
                if lat is None or lon is None:
                    continue

                try:
                    dist = haversine(user_lat, user_lon, lat, lon)
                except Exception:
                    # If anything unexpected slips through (types, NaN, etc), ignore that station.
                    continue

                if dist < best_distance:
                    best_distance = dist
                    best_station = station

    if not best_station:
        return None


    station_name = best_station.get("stationName")
    if not station_name:
        station_name = best_station.get("name") or best_station.get("station") or "NA"

    return {
        "station": {
            "name": station_name
        },
        "source": "CPCB",
    }

