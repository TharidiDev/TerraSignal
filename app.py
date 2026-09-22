import streamlit as st
import urllib.request
import json
from datetime import datetime, timedelta

st.set_page_config(
    page_title="TerraSignal",
    page_icon="🌍",
    layout="centered"
)

# =========================================================
# TERRASIGNAL
# =========================================================

st.title("🌍 TerraSignal")
st.subheader("Earth intelligence. Human reach.")

st.markdown("### 📞 One missed call. No smartphone. No app.")

st.write(
    "TerraSignal transforms environmental data into "
    "simple alerts for people using basic phones."
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
# MISSED CALL
# =========================================================

st.markdown("---")
st.markdown("## 📞 Incoming Call")

incoming_caller_id = st.text_input(
    "Incoming Caller ID",
    placeholder="DEMO001"
)

if st.button(
    "📞 Simulate Missed Call",
    use_container_width=True
):

    if incoming_caller_id not in st.session_state.users:

        st.error(
            "❌ Caller not registered. Please register the user first."
        )

    else:

        user = st.session_state.users[incoming_caller_id]

        st.success(
            "📞 Missed call received!"
        )

        st.write(
            f"👤 **User:** {user['name']}"
        )

        st.write(
            f"📍 **Location:** {user['location']}"
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

            latest_date = dates[-1]

            latest_temperature = temperature_data[latest_date]

            latest_rainfall = rainfall_data[latest_date]

            recent_rainfall = sum(
                max(0, rainfall_data[d])
                for d in dates
            )

            # =================================================
            # RISK ENGINE
            # =================================================

            risk_score = 0

            signals = []

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

            if latest_temperature >= 35:

                risk_score += 2

                signals.append(
                    "High temperature signal"
                )

            elif latest_temperature >= 32:

                risk_score += 1

                signals.append(
                    "Elevated temperature"
                )

            # =================================================
            # RISK LEVEL
            # =================================================

            if risk_score >= 5:

                risk_level = "HIGH"

            elif risk_score >= 2:

                risk_level = "WATCH"

            else:

                risk_level = "LOW"

            # =================================================
            # EARTH SIGNAL
            # =================================================

            st.markdown("---")
            st.markdown("## 📡 EARTH SIGNAL")

            if risk_level == "HIGH":

                st.error("🔴 HIGH SIGNAL")

            elif risk_level == "WATCH":

                st.warning("🟠 WATCH SIGNAL")

            else:

                st.success("🟢 LOW SIGNAL")

            # =================================================
            # DETECTED SIGNALS
            # =================================================

            st.markdown("### 🔎 Detected Signals")

            if signals:

                for signal in signals:

                    st.write(
                        f"• {signal}"
                    )

            else:

                st.write(
                    "• No major environmental signal detected."
                )

            # =================================================
            # SINHALA SMS
            # =================================================

            st.markdown("---")
            st.markdown("## 📱 SINHALA SMS")

            if risk_level == "HIGH":

                sms_message = (
                    f"ටෙරාසිග්නල්: {user['location']} ප්‍රදේශයේ "
                    "අවධානය යොමු කළ යුතු පාරිසරික සංඥාවක් "
                    "හඳුනාගෙන ඇත. කරුණාකර ප්‍රවේශම් වන්න."
                )

            elif risk_level == "WATCH":

                sms_message = (
                    f"ටෙරාසිග්නල්: {user['location']} ප්‍රදේශයේ "
                    "කාලගුණික වෙනසක් පිළිබඳ සංඥාවක් "
                    "හඳුනාගෙන ඇත. කරුණාකර අවධානයෙන් සිටින්න."
                )

            else:

                sms_message = (
                    f"ටෙරාසිග්නල්: {user['location']} සඳහා "
                    "දැනට ප්‍රධාන පාරිසරික අවදානම් සංඥාවක් "
                    "හඳුනාගෙන නැත."
                )

            st.info(sms_message)

            st.caption(
                "📤 SMS status: READY"
            )

            # =================================================
            # SINHALA VOICE
            # =================================================

            st.markdown("## 🗣️ SINHALA VOICE")

            if risk_level == "HIGH":

                voice_message = (
                    f"ආයුබෝවන්. {user['location']} ප්‍රදේශය සඳහා "
                    "අවධානය යොමු කළ යුතු පාරිසරික සංඥාවක් "
                    "ලැබී ඇත. කරුණාකර ප්‍රවේශම් වන්න."
                )

            elif risk_level == "WATCH":

                voice_message = (
                    f"ආයුබෝවන්. {user['location']} ප්‍රදේශයේ "
                    "කාලගුණික වෙනසක් පිළිබඳ සංඥාවක් "
                    "ලැබී ඇත. කරුණාකර අවධානයෙන් සිටින්න."
                )

            else:

                voice_message = (
                    f"ආයුබෝවන්. {user['location']} සඳහා "
                    "දැනට ප්‍රධාන පාරිසරික අවදානම් සංඥාවක් "
                    "හඳුනාගෙන නැත."
                )

            st.info(voice_message)

            st.caption(
                "🔊 Voice status: READY"
            )

            # =================================================
            # NASA EVIDENCE
            # =================================================

            with st.expander(
                "🔬 NASA Data Evidence"
            ):

                st.write(
                    "Data source: NASA POWER"
                )

                st.write(
                    f"Location: {user['location']}"
                )

                st.write(
                    f"Temperature: "
                    f"{latest_temperature:.1f} °C"
                )

                st.write(
                    f"Precipitation: "
                    f"{latest_rainfall:.1f} mm"
                )

                st.write(
                    f"7-day rainfall total: "
                    f"{recent_rainfall:.1f} mm"
                )

                st.write(
                    f"Latest available date: "
                    f"{latest_date}"
                )

            # =================================================
            # PROTOTYPE NOTE
            # =================================================

            st.warning(
                "Prototype note: risk thresholds are experimental "
                "and must be scientifically validated before "
                "real-world warning use."
            )

        except Exception as error:

            st.error(
                "❌ TerraSignal could not retrieve NASA data."
            )

            st.code(
                str(error)
            )


# =========================================================
# ARCHITECTURE
# =========================================================

st.markdown("---")

st.markdown(
    "## 🔗 TerraSignal Flow"
)

st.write(
    "📞 Missed Call"
    " → "
    "👤 User Lookup"
    " → "
    "📍 Location"
    " → "
    "🛰️ NASA Data"
    " → "
    "🧠 Risk Engine"
    " → "
    "📱 SMS / 🗣️ Voice"
)

st.markdown("---")

st.caption("TerraSignal Prototype")
st.caption("NASA POWER environmental data")
st.caption(
    "Built by TharidiDev | NASA Space Apps Colombo 2026"
)                
