import streamlit as st
import urllib.request
import json
from datetime import datetime, timedelta

st.set_page_config(
    page_title="TerraSignal",
    page_icon="🌍",
    layout="centered"
)

# --------------------------------------------------
# TerraSignal
# Missed-call based environmental warning prototype
# --------------------------------------------------

st.title("🌍 TerraSignal")
st.subheader("Earth intelligence. Human reach.")

st.markdown("---")

# Demo registered users
users = {
    "Grandmother": {
        "city": "Colombo",
        "latitude": 6.9271,
        "longitude": 79.8612
    },
    "Grandfather": {
        "city": "Kandy",
        "latitude": 7.2906,
        "longitude": 80.6337
    },
    "Family Member": {
        "city": "Galle",
        "latitude": 6.0329,
        "longitude": 80.2168
    }
}

user_name = st.selectbox(
    "Registered phone:",
    list(users.keys())
)

st.caption("Demo mode — simulating a missed call from a basic phone.")

if st.button("📞 Simulate Missed Call", use_container_width=True):

    user = users[user_name]

    st.success("📞 Missed call received")

    st.markdown("### 👤 User")
    st.write(user_name)

    st.markdown("### 📍 Registered location")
    st.write(user["city"])

    st.markdown("---")

    st.markdown("### 🛰️ TerraSignal is checking Earth data...")

    # Get last 3 days of NASA POWER data
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=3)

    start = start_date.strftime("%Y%m%d")
    end = today.strftime("%Y%m%d")

    url = (
        "https://power.larc.nasa.gov/api/temporal/daily/point"
        "?parameters=T2M_MAX,PRECTOTCORR"
        f"&community=AG"
        f"&longitude={user['longitude']}"
        f"&latitude={user['latitude']}"
        f"&start={start}"
        f"&end={end}"
        "&format=JSON"
    )

    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            data = json.loads(response.read().decode())

        temperature_data = data["properties"]["parameter"]["T2M_MAX"]
        rainfall_data = data["properties"]["parameter"]["PRECTOTCORR"]

        dates = sorted(temperature_data.keys())

        latest_date = dates[-1]

        latest_temperature = temperature_data[latest_date]
        latest_rainfall = rainfall_data[latest_date]

        recent_rainfall = sum(
            rainfall_data[d]
            for d in dates
            if rainfall_data[d] >= 0
        )

        # --------------------------------------------------
        # Prototype risk engine
        # These thresholds are experimental and must be
        # scientifically validated before real-world use.
        # --------------------------------------------------

        risk_score = 0
        signals = []

        if latest_rainfall >= 20:
            risk_score += 2
            signals.append("Heavy rainfall signal")

        elif latest_rainfall >= 5:
            risk_score += 1
            signals.append("Rainfall signal")

        if latest_temperature >= 35:
            risk_score += 2
            signals.append("High temperature signal")

        elif latest_temperature >= 32:
            risk_score += 1
            signals.append("Elevated temperature")

        if risk_score >= 3:
            risk_level = "HIGH"
        elif risk_score >= 1:
            risk_level = "WATCH"
        else:
            risk_level = "LOW"

        # --------------------------------------------------
        # TerraSignal result
        # --------------------------------------------------

        st.markdown("---")

        st.markdown("## 📡 EARTH SIGNAL")

        if risk_level == "HIGH":
            st.error("⚠️ HIGH RISK SIGNAL")

        elif risk_level == "WATCH":
            st.warning("🟠 WATCH SIGNAL")

        else:
            st.success("🟢 LOW RISK SIGNAL")

        st.write("Detected signals:")

        if signals:
            for signal in signals:
                st.write(f"• {signal}")
        else:
            st.write("• No major signal detected")

        st.markdown("---")

        # --------------------------------------------------
        # Personalized SMS
        # --------------------------------------------------

        st.markdown("## 📱 SMS READY")

        if risk_level == "HIGH":
            sms = (
                f"ටෙරාසිග්නල්: {user['city']} ප්‍රදේශයේ "
                "අයහපත් කාලගුණික තත්ත්වයක සංඥාවක් හඳුනාගෙන ඇත. "
                "ප්‍රවේශම් වන්න."
            )

        elif risk_level == "WATCH":
            sms = (
                f"ටෙරාසිග්නල්: {user['city']} ප්‍රදේශයේ "
                "කාලගුණික වෙනසක් නිරීක්ෂණය වී ඇත. "
                "යන විට ප්‍රවේශම් වන්න."
            )

        else:
            sms = (
                f"ටෙරාසිග්නල්: {user['city']} ප්‍රදේශයේ "
                "දැනට විශේෂ අවදානම් සංඥාවක් හඳුනාගෙන නැත."
            )

        st.info(sms)

        # --------------------------------------------------
        # Voice message
        # --------------------------------------------------

        st.markdown("## 🗣️ VOICE MESSAGE")

        if risk_level == "HIGH":
            voice_message = (
                f"ආයුබෝවන්. {user['city']} ප්‍රදේශය සඳහා "
                "ප්‍රවේශම් වීමේ කාලගුණික සංඥාවක් ලැබී ඇත. "
                "කරුණාකර ආරක්ෂිතව සිටින්න."
            )

        elif risk_level == "WATCH":
            voice_message = (
                f"ආයුබෝවන්. {user['city']} ප්‍රදේශයේ "
                "කාලගුණික වෙනසක් නිරීක්ෂණය වී ඇත. "
                "කරුණාකර ප්‍රවේශම් වන්න."
            )

        else:
            voice_message = (
                f"ආයුබෝවන්. {user['city']} සඳහා "
                "දැනට විශේෂ කාලගුණික අවදානමක් හඳුනාගෙන නැත."
            )

        st.info(voice_message)

        # --------------------------------------------------
        # Data evidence
        # --------------------------------------------------

        with st.expander("🔬 NASA data used"):

            st.write(
                f"Latest NASA POWER temperature: "
                f"{latest_temperature:.1f} °C"
            )

            st.write(
                f"Latest NASA POWER precipitation: "
                f"{latest_rainfall:.1f} mm"
            )

            st.write(
                f"Recent rainfall total: "
                f"{recent_rainfall:.1f} mm"
            )

            st.write(
                f"Data date: {latest_date}"
            )

    except Exception as error:

        st.error("TerraSignal could not retrieve NASA data.")

        st.code(str(error))

st.markdown("---")

st.caption(
    "TerraSignal prototype | NASA POWER environmental data"
)

st.caption(
    "Built by TharidiDev | NASA Space Apps Colombo 2026"
)
