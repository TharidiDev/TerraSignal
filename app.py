import streamlit as st
import urllib.request
import json
from datetime import datetime, timedelta

# ---------------------------------------------------------
# TERRASIGNAL
# Basic-phone environmental signal prototype
# ---------------------------------------------------------

st.set_page_config(
    page_title="TerraSignal",
    page_icon="🌍",
    layout="centered"
)

# -----------------------------
# Simple visual design
# -----------------------------

st.markdown("""
<style>
    .big-title {
        font-size: 42px;
        font-weight: 800;
        text-align: center;
    }

    .subtitle {
        font-size: 20px;
        text-align: center;
        margin-bottom: 25px;
    }

    .signal-box {
        padding: 20px;
        border-radius: 15px;
        background: #f5f5f5;
        margin-top: 15px;
    }

    .phone-box {
        padding: 15px;
        border-radius: 12px;
        background: #eeeeee;
        font-size: 18px;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------
# Header
# -----------------------------

st.markdown(
    '<div class="big-title">🌍 TerraSignal</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Earth intelligence. Human reach.</div>',
    unsafe_allow_html=True
)

st.markdown("---")


# -----------------------------
# Demo registered users
# -----------------------------
# This is only a prototype database.
# Later this will be replaced with a real database.

registered_users = {
    "0771234567": {
        "name": "Grandmother",
        "city": "Colombo",
        "lat": 6.9271,
        "lon": 79.8612
    },

    "0777654321": {
        "name": "Grandfather",
        "city": "Kandy",
        "lat": 7.2906,
        "lon": 80.6337
    },

    "0714567890": {
        "name": "Family Member",
        "city": "Galle",
        "lat": 6.0329,
        "lon": 80.2168
    }
}


# -----------------------------
# Basic phone interface
# -----------------------------

st.markdown("### 📞 Basic Phone Interface")

phone_number = st.text_input(
    "Enter registered phone number:",
    value="0771234567"
)

st.caption(
    "Demo mode: the button below simulates one missed call."
)

st.markdown("---")


# -----------------------------
# Missed call simulation
# -----------------------------

if st.button(
    "📞 Simulate 1 Missed Call",
    use_container_width=True
):

    # ---------------------------------
    # Check phone number
    # ---------------------------------

    if phone_number not in registered_users:

        st.error(
            "❌ This phone number is not registered with TerraSignal."
        )

    else:

        user = registered_users[phone_number]

        # ---------------------------------
        # Incoming call status
        # ---------------------------------

        st.success("📞 MISSED CALL RECEIVED")

        st.markdown("### 👤 Registered User")
        st.write(user["name"])

        st.markdown("### 📍 Registered Location")
        st.write(user["city"])

        st.markdown("---")

        # ---------------------------------
        # NASA data retrieval
        # ---------------------------------

        st.markdown("### 🛰️ Checking Earth data...")

        today = datetime.utcnow().date()

        start_date = today - timedelta(days=7)

        start = start_date.strftime("%Y%m%d")
        end = today.strftime("%Y%m%d")

        nasa_url = (
            "https://power.larc.nasa.gov/api/temporal/daily/point"
            "?parameters=T2M_MAX,PRECTOTCORR"
            "&community=AG"
            f"&longitude={user['lon']}"
            f"&latitude={user['lat']}"
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

            temp_data = (
                data["properties"]
                ["parameter"]
                ["T2M_MAX"]
            )

            rain_data = (
                data["properties"]
                ["parameter"]
                ["PRECTOTCORR"]
            )

            dates = sorted(temp_data.keys())

            if not dates:
                raise ValueError(
                    "NASA returned no data for this period."
                )

            latest_date = dates[-1]

            latest_temp = temp_data[latest_date]
            latest_rain = rain_data[latest_date]

            # -----------------------------
            # Recent rainfall
            # -----------------------------

            recent_rainfall = sum(
                max(0, rain_data[d])
                for d in dates
            )

            # -----------------------------
            # Risk engine
            # -----------------------------

            risk_score = 0
            detected_signals = []

            # Rain signal
            if latest_rain >= 20:

                risk_score += 3

                detected_signals.append(
                    "High daily rainfall signal"
                )

            elif latest_rain >= 5:

                risk_score += 1

                detected_signals.append(
                    "Rainfall signal"
                )

            # Recent rainfall trend
            if recent_rainfall >= 40:

                risk_score += 2

                detected_signals.append(
                    "High recent rainfall accumulation"
                )

            elif recent_rainfall >= 15:

                risk_score += 1

                detected_signals.append(
                    "Recent rainfall accumulation"
                )

            # Heat signal
            if latest_temp >= 35:

                risk_score += 2

                detected_signals.append(
                    "High temperature signal"
                )

            elif latest_temp >= 32:

                risk_score += 1

                detected_signals.append(
                    "Elevated temperature"
                )

            # -----------------------------
            # Risk classification
            # -----------------------------

            if risk_score >= 5:

                risk_level = "HIGH"

            elif risk_score >= 2:

                risk_level = "WATCH"

            else:

                risk_level = "LOW"

            # -----------------------------
            # Earth Signal
            # -----------------------------

            st.markdown("---")

            st.markdown("## 📡 EARTH SIGNAL")

            if risk_level == "HIGH":

                st.error(
                    "🔴 HIGH SIGNAL"
                )

            elif risk_level == "WATCH":

                st.warning(
                    "🟠 WATCH SIGNAL"
                )

            else:

                st.success(
                    "🟢 LOW SIGNAL"
                )

            # -----------------------------
            # Explain signal
            # -----------------------------

            st.markdown(
                '<div class="signal-box">',
                unsafe_allow_html=True
            )

            st.write(
                f"📍 Location: {user['city']}"
            )

            st.write(
                f"🌡️ Latest temperature: "
                f"{latest_temp:.1f} °C"
            )

            st.write(
                f"🌧️ Latest precipitation: "
                f"{latest_rain:.1f} mm"
            )

            st.write(
                f"🌧️ Recent rainfall total: "
                f"{recent_rainfall:.1f} mm"
            )

            st.write(
                f"📅 Data date: {latest_date}"
            )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )

            # -----------------------------
            # Detected signals
            # -----------------------------

            st.markdown("### 🔎 Detected Environmental Signals")

            if detected_signals:

                for signal in detected_signals:

                    st.write(
                        f"• {signal}"
                    )

            else:

                st.write(
                    "• No major environmental signal detected."
                )

            # -----------------------------
            # Sinhala SMS
            # -----------------------------

            st.markdown("---")

            st.markdown("## 📱 SINHALA SMS")

            if risk_level == "HIGH":

                sms_message = (
                    f"ටෙරාසිග්නල්: "
                    f"{user['city']} ප්‍රදේශයේ "
                    "අවධානය යොමු කළ යුතු පාරිසරික "
                    "සංඥා හඳුනාගෙන ඇත. "
                    "කරුණාකර ප්‍රවේශම් වන්න."
                )

            elif risk_level == "WATCH":

                sms_message = (
                    f"ටෙරාසිග්නල්: "
                    f"{user['city']} ප්‍රදේශයේ "
                    "කාලගුණික වෙනසක් පිළිබඳ "
                    "සංඥාවක් හඳුනාගෙන ඇත. "
                    "කරුණාකර අවධානයෙන් සිටින්න."
                )

            else:

                sms_message = (
                    f"ටෙරාසිග්නල්: "
                    f"{user['city']} සඳහා "
                    "දැනට ප්‍රධාන පාරිසරික "
                    "අවදානම් සංඥාවක් හඳුනාගෙන නැත."
                )

            st.info(sms_message)

            st.caption("📤 SMS status: READY")


            # -----------------------------
            # Sinhala Voice message
            # -----------------------------

            st.markdown("## 🗣️ SINHALA VOICE MESSAGE")

            if risk_level == "HIGH":

                voice_message = (
                    f"ආයුබෝවන්. "
                    f"{user['city']} ප්‍රදේශය සඳහා "
                    "අවධානය යොමු කළ යුතු "
                    "පාරිසරික සංඥාවක් ලැබී ඇත. "
                    "කරුණාකර ප්‍රවේශම් වන්න."
                )

            elif risk_level == "WATCH":

                voice_message = (
                    f"ආයුබෝවන්. "
                    f"{user['city']} ප්‍රදේශයේ "
                    "කාලගුණික වෙනසක් "
                    "පිළිබඳ සංඥාවක් ලැබී ඇත. "
                    "කරුණාකර අවධානයෙන් සිටින්න."
                )

            else:

                voice_message = (
                    f"ආයුබෝවන්. "
                    f"{user['city']} සඳහා "
                    "දැනට ප්‍රධාන පාරිසරික "
                    "අවදානම් සංඥාවක් හඳුනාගෙන නැත."
                )

            st.info(voice_message)

            st.caption(
                "🔊 Voice call status: READY"
            )

            # -----------------------------
            # NASA evidence
            # -----------------------------

            with st.expander(
                "🔬 NASA Data Evidence"
            ):

                st.write(
                    "NASA POWER Daily Point API"
                )

                st.write(
                    f"Latitude: {user['lat']}"
                )

                st.write(
                    f"Longitude: {user['lon']}"
                )

                st.write(
                    f"Temperature: {latest_temp:.1f} °C"
                )

                st.write(
                    f"Precipitation: {latest_rain:.1f} mm"
                )

                st.write(
                    f"Recent rainfall: "
                    f"{recent_rainfall:.1f} mm"
                )

        except Exception as error:

            st.error(
                "❌ Could not retrieve NASA data."
            )

            st.code(str(error))


# -----------------------------
# Demo numbers
# -----------------------------

with st.expander("📋 Demo registered numbers"):

    st.write(
        "0771234567 → Grandmother → Colombo"
    )

    st.write(
        "0777654321 → Grandfather → Kandy"
    )

    st.write(
        "0714567890 → Family Member → Galle"
    )


# -----------------------------
# Footer
# -----------------------------

st.markdown("---")

st.caption(
    "TerraSignal Prototype"
)

st.caption(
    "NASA POWER environmental data"
)

st.caption(
    "Built by TharidiDev | NASA Space Apps Colombo 2026"
)        
       

        
        
        




