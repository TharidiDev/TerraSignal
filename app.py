import streamlit as st
import urllib.request
import json
from datetime import datetime

st.set_page_config(
    page_title="TerraSignal",
    page_icon="🌍"
)

st.title("🌍 TerraSignal")
st.subheader("Earth's signal, in simple words.")

st.markdown("---")

city_coordinates = {
    "Colombo": (6.9271, 79.8612),
    "Kandy": (7.2906, 80.6337),
    "Galle": (6.0329, 80.2168),
    "Jaffna": (9.6615, 80.0255),
    "Kurunegala": (7.4863, 80.3623),
    "Anuradhapura": (8.3114, 80.4037),
    "Batticaloa": (7.7310, 81.6747),
    "Matara": (5.9549, 80.5550)
}

location = st.selectbox(
    "Your City:",
    list(city_coordinates.keys())
)

if st.button("Get Earth's Signal 📻"):

    latitude, longitude = city_coordinates[location]

    today = datetime.utcnow().strftime("%Y%m%d")

    url = (
        "https://power.larc.nasa.gov/api/temporal/daily/point"
        f"?parameters=T2M,PRECTOTCORR"
        f"&community=AG"
        f"&longitude={longitude}"
        f"&latitude={latitude}"
        f"&start=20260920"
        f"&end={today}"
        f"&format=JSON"
    )

    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            data = json.loads(response.read().decode())

        values = data["properties"]["parameter"]

        temperature_data = values["T2M"]
        rain_data = values["PRECTOTCORR"]

        latest_date = sorted(temperature_data.keys())[-1]

        temperature = temperature_data[latest_date]
        rainfall = rain_data[latest_date]

        st.success(f"TerraSignal Report — {location}")

        st.markdown(f"### 🌡️ Temperature: {temperature:.1f} °C")
        st.markdown(f"### 🌧️ Precipitation: {rainfall:.1f} mm")
        st.markdown(f"### 📅 NASA data date: {latest_date}")

        if rainfall >= 20:
            st.warning("🌧️ Heavy rainfall signal detected.")
        elif rainfall >= 5:
            st.info("🌦️ Rainfall signal detected.")
        else:
            st.success("☀️ Low rainfall signal.")

        if temperature >= 35:
            st.warning("🔥 High temperature signal detected.")

    except Exception as error:
        st.error("Unable to retrieve NASA data.")
        st.code(str(error))

st.markdown("---")
st.caption("NASA POWER data | TerraSignal Prototype")
st.caption("Built by TharidiDev | NASA Space Apps Colombo 2026")

