```python
import streamlit as st
import urllib.request
import json
from datetime import datetime, timedelta

# =========================================================
# TERRASIGNAL
# Missed-call based environmental warning prototype
# =========================================================

st.set_page_config(
    page_title="TerraSignal",
    page_icon="🌍",
    layout="centered"
)

# =========================================================
# TITLE
# =========================================================

st.title("🌍 TerraSignal")
st.subheader("Earth intelligence. Human reach.")

st.markdown(
    "### 📞 One missed call. No smartphone. No app."
)

st.write(
    "TerraSignal is a prototype that transforms environmental "
    "data into simple alerts for people using basic phones."
)

st.markdown("---")

# =========================================================
# USER REGISTRATION
# =========================================================

if "users" not in st.session_state:
    st.session_state.users = {}

st.markdown("## 👤 Register a User")

with st.form("register_user_form"):

    name = st.text_input(
        "User Name",
        placeholder="Grandmother"
    )

    caller_id = st.text_input(
        "Phone / Caller ID",
        placeholder="DEMO001"
    )

    location = st.selectbox(
        "Location",
        ["Colombo", "Kandy", "Galle"]
    )

    register = st.form_submit_button(
        "➕ Register User"
    )

    if register:

        if name and caller_id:

            locations = {
                "Colombo": {
                    "latitude": 6.9271,
                    "longitude": 79.8612
                },

                "Kandy": {
                    "latitude": 7.2906,
                    "longitude": 80.6337
                },

                "Galle": {
                    "latitude": 6.0329,
                    "longitude": 80.2168
                }
            }

            st.session_state.users[caller_id] = {
                "name": name,
                "location": location,
                "latitude": locations[location]["latitude"],
                "longitude": locations[location]["longitude"]
            }

            st.success(
                f"✅ {name} registered successfully!"
            )

        else:

            st.error(
                "Please enter both name and caller ID."
            )


# =========================================================
# INCOMING CALL
# =========================================================

st.markdown("---")
st.markdown("## 📞 Incoming Call")

caller_id_input = st.text_input(
    "Incoming Caller ID",
    placeholder="DEMO001"
)

if st.button(
    "📞 Simulate Missed Call",
    use_container_width=True
):

    # -----------------------------------------------------
    # Check registered user
    # -----------------------------------------------------

    if caller_id_input not in st.session_state.users:

        st.error(
            "❌ Caller not registered. Please register the user first."
        )

    else:

        user = st.session_state.users[caller_id_input]

        st.success(
            "📞 Missed call received!"
        )

        st.write(
            f"👤 **User:** {user['name']}"
        )

        st.write(
            f"📍 **Location:** {user['location']}"
        )

        st.caption(
            "Demo mode: this simulates one missed call from a basic phone."
        )

        # =================================================
        # NASA DATA
        # =================================================

        st.markdown("---")
        st.markdown("## 🛰️ Earth Data Analysis")

        st.info(
            "TerraSignal is checking NASA environmental data..."
        )

        today = datetime.utcnow().date()

        start_date = today - timedelta(days=7)

        start = start_date.strftime("%Y%m%d")
        end = today.strftime("%Y%m%d")

        nasa_url = (
            "https://power.larc.nasa.gov/api/temporal/daily/point"
            "?parameters=T2M_MAX,PRECTOTCORR"
            "&community=AG"
            f"&longitude={user['longitude']}"
            f"&latitude={user['latitude']}"
            f"&start={start}"
            f"&end={end}"
            "&format=JSON"
        )

        try:

            # -------------------------------------------------
            # Request NASA POWER data
            # -------------------------------------------------

            with urllib.request.urlopen(
                nasa_url,
                timeout=20
            ) as response:

                data = json.loads(
                    response.read().decode()
                )

            parameters = data["properties"]["parameter"]

            temperature_data = parameters["T2M_MAX"]

            rainfall_data = parameters["PRECTOTCORR"]

            dates = sorted(
                temperature_data.keys()
            )

            if not dates:

                raise ValueError(
                    "No NASA data returned."
                )

            # -------------------------------------------------
            # Latest data
            # -------------------------------------------------

            latest_date = dates[-1]

            latest_temperature = (
                temperature_data[latest_date]
            )

            latest_rainfall = (
                rainfall_data[latest_date]
            )

            recent_rainfall = sum(
                max(0, rainfall_data[d])
                for d in dates
            )

            # =================================================
            # RISK ENGINE
            # =================================================

            risk_score = 0

            signals = []

            # Daily rainfall

            if latest_rainfall >= 20:

                risk_score += 3

                signals.append(
                    "High daily rainfall signal"
                )

            elif latest_rainfall >= 5:

                risk_score += 1

                signals.append(
                    "Rainfall signal"
                )

            # Recent rainfall
            if recent_rainfall >= 40:

                risk_score += 2

                signals.append(
                    "High recent rainfall accumulation"
                )

            elif recent_rainfall >= 15:

                risk_score += 1

                signals.append(
                    "Recent rainfall accumulation"
                )
