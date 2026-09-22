import streamlit as st
import urllib.request
import urllib.parse
import json
from datetime import date, timedelta


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="TerraSignal",
    page_icon="🌍",
    layout="wide"
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    "<h1 style='text-align:center;'>🌍 TerraSignal</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<h3 style='text-align:center;'>Earth Intelligence. Human Reach.</h3>",
    unsafe_allow_html=True
)

st.write(
    "NASA Earth data → Risk detection → Simple human warning"
)

st.info(
    "📞 One missed call. No smartphone. No app."
)


# ============================================================
# SESSION STATE
# ============================================================

if "users" not in st.session_state:
    st.session_state.users = {}


# ============================================================
# LOCATION DATABASE
# ============================================================

locations = {
    "Colombo": {
        "lat": 6.9271,
        "lon": 79.8612
    },
    "Kandy": {
        "lat": 7.2906,
        "lon": 80.6337
    },
    "Galle": {
        "lat": 6.0329,
        "lon": 80.2168
    }
}


# ============================================================
# USER REGISTRATION
# ============================================================

st.header("👤 User Registration")

with st.form("registration_form"):

    name = st.text_input(
        "Name"
    )

    caller_id = st.text_input(
        "Phone number / Caller ID"
    )

    location_name = st.selectbox(
        "Location",
        list(locations.keys())
    )

    register_button = st.form_submit_button(
        "Register"
    )

    if register_button:

        if name and caller_id:

            st.session_state.users[caller_id] = {
                "name": name,
                "location": location_name
            }

            st.success(
                f"Registered {name} in {location_name}."
            )

        else:

            st.warning(
                "Please enter both name and phone number."
            )


# ============================================================
# MISSED CALL SIMULATION
# ============================================================

st.header("📞 Missed Call Simulation")

incoming_caller = st.text_input(
    "Enter registered caller ID"
)

simulate_call = st.button(
    "📞 Simulate Missed Call"
)


if simulate_call:

    if incoming_caller in st.session_state.users:

        user = st.session_state.users[incoming_caller]

        st.success(
            f"Missed call detected from {user['name']}."
        )

    else:

        st.warning(
            "Caller ID is not registered."
        )


# ============================================================
# SELECT ACTIVE USER
# ============================================================

active_user = None

if incoming_caller in st.session_state.users:

    active_user = st.session_state.users[incoming_caller]

elif len(st.session_state.users) > 0:

    first_caller = list(st.session_state.users.keys())[0]

    active_user = st.session_state.users[first_caller]


# ============================================================
# MAIN TERRASIGNAL SYSTEM
# ============================================================

if active_user:

    location_name = active_user["location"]

    latitude = locations[location_name]["lat"]
    longitude = locations[location_name]["lon"]

    st.header("📡 TerraSignal Earth Intelligence")

    st.write(
        f"Monitoring location: **{location_name}**"
    )

    st.write(
        f"Coordinates: {latitude:.4f}, {longitude:.4f}"
    )


    # ========================================================
    # NASA POWER DATA
    # ========================================================

    try:

        today = date.today()

        start_date = today - timedelta(days=7)

        end_date = today - timedelta(days=1)

        parameters = (
            "T2M_MAX,"
            "PRECTOTCORR,"
            "RH2M,"
            "WS2M,"
            "WD2M,"
            "PS,"
            "ALLSKY_SFC_SW_DWN"
        )

        query_params = {
            "parameters": parameters,
            "community": "AG",
            "longitude": longitude,
            "latitude": latitude,
            "start": start_date.strftime("%Y%m%d"),
            "end": end_date.strftime("%Y%m%d"),
            "format": "JSON"
        }

        url = (
            "https://power.larc.nasa.gov/api/temporal/daily/point?"
            + urllib.parse.urlencode(query_params)
        )

        with st.spinner("🛰️ Connecting to NASA POWER..."):

            with urllib.request.urlopen(
                url,
                timeout=20
            ) as response:

                data = json.loads(
                    response.read().decode("utf-8")
                )


        # ====================================================
        # NASA DATA EXTRACTION
        # ====================================================

        properties = data["properties"]

        parameter_data = properties["parameter"]

        temperature_data = parameter_data["T2M_MAX"]

        rainfall_data = parameter_data["PRECTOTCORR"]

        humidity_data = parameter_data["RH2M"]

        wind_speed_data = parameter_data["WS2M"]

        wind_direction_data = parameter_data["WD2M"]

        pressure_data = parameter_data["PS"]

        solar_data = parameter_data["ALLSKY_SFC_SW_DWN"]


        # ====================================================
        # VALID DATES
        # ====================================================

        valid_dates = sorted(
            temperature_data.keys()
        )

        latest_date = valid_dates[-1]


        # ====================================================
        # LATEST VALUES
        # ====================================================

        latest_temperature = float(
            temperature_data[latest_date]
        )

        latest_rainfall = float(
            rainfall_data[latest_date]
        )

        latest_humidity = float(
            humidity_data[latest_date]
        )

        latest_wind_speed = float(
            wind_speed_data[latest_date]
        )

        latest_wind_direction = float(
            wind_direction_data[latest_date]
        )

        latest_pressure = float(
            pressure_data[latest_date]
        )

        latest_solar = float(
            solar_data[latest_date]
        )


        # ====================================================
        # RECENT RAINFALL
        # ====================================================

        rainfall_values = []

        for d in valid_dates:

            value = rainfall_data.get(d)

            if value is not None:

                try:

                    rainfall_values.append(
                        float(value)
                    )

                except:

                    pass


        recent_rainfall = sum(
            rainfall_values
        )


        # ====================================================
        # EARTH SIGNAL
        # ====================================================

        st.success(
            "🛰️ NASA Earth data received successfully."
        )

        st.subheader("🌍 Earth Signal")


        # ====================================================
        # METRICS
        # ====================================================

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "🌧️ Rainfall",
                f"{latest_rainfall:.1f} mm"
            )

            st.metric(
                "🌡️ Temperature",
                f"{latest_temperature:.1f} °C"
            )


        with col2:

            st.metric(
                "💧 Humidity",
                f"{latest_humidity:.1f}%"
            )

            st.metric(
                "💨 Wind Speed",
                f"{latest_wind_speed:.1f} m/s"
            )


        with col3:

            st.metric(
                "🧭 Wind Direction",
                f"{latest_wind_direction:.0f}°"
            )

            st.metric(
                "🛰️ Pressure",
                f"{latest_pressure:.1f} kPa"
            )


        st.metric(
            "☀️ Solar Radiation",
            f"{latest_solar:.1f} MJ/m²/day"
        )


        # ====================================================
        # RISK ENGINE
        # ====================================================

        risk_score = 0

        signals = []


        # ----------------------------------------------------
        # Daily rainfall
        # ----------------------------------------------------

        if latest_rainfall >= 20:

            risk_score += 3

            signals.append(
                "High daily rainfall detected"
            )

        elif latest_rainfall >= 5:

            risk_score += 1

            signals.append(
                "Moderate daily rainfall detected"
            )


        # ----------------------------------------------------
        # Recent rainfall
        # ----------------------------------------------------

        if recent_rainfall >= 40:

            risk_score += 2

            signals.append(
                "High rainfall accumulated over recent days"
            )

        elif recent_rainfall >= 15:

            risk_score += 1

            signals.append(
                "Moderate recent rainfall accumulation"
            )


        # ----------------------------------------------------
        # Temperature
        # ----------------------------------------------------

        if latest_temperature >= 35:

            risk_score += 2

            signals.append(
                "Very high temperature"
            )

        elif latest_temperature >= 32:

            risk_score += 1

            signals.append(
                "High temperature"
            )


        # ----------------------------------------------------
        # Humidity
        # ----------------------------------------------------

        if latest_humidity >= 85:

            risk_score += 1

            signals.append(
                "Very high atmospheric humidity"
            )


        # ----------------------------------------------------
        # Wind
        # ----------------------------------------------------

        if latest_wind_speed >= 12:

            risk_score += 2

            signals.append(
                "Strong wind conditions"
            )

        elif latest_wind_speed >= 8:

            risk_score += 1

            signals.append(
                "Elevated wind speed"
            )


        # ====================================================
        # RISK LEVEL
        # ====================================================

        if risk_score >= 7:

            risk_level = "VERY HIGH"

        elif risk_score >= 5:

            risk_level = "HIGH"

        elif risk_score >= 2:

            risk_level = "WATCH"

        else:

            risk_level = "LOW"


        # ====================================================
        # RISK DISPLAY
        # ====================================================

        st.divider()

        st.subheader("⚠️ TerraSignal Risk Assessment")

        st.write(
            f"### Risk Level: **{risk_level}**"
        )

        st.write(
            f"Risk score: **{risk_score}**"
        )


        # ====================================================
        # DETECTED SIGNALS
        # ====================================================

        st.subheader("🔎 Detected Signals")

        if signals:

            for signal in signals:

                st.write(
                    f"• {signal}"
                )

        else:

            st.write(
                "• No major environmental signals detected."
            )


        # ====================================================
        # HUMAN EXPLANATION
        # ====================================================

        st.subheader("❓ WHY?")


        if risk_level == "VERY HIGH":

            explanation = (
                "Several environmental indicators are currently "
                "showing elevated values. The system therefore "
                "classifies the location as VERY HIGH risk."
            )

        elif risk_level == "HIGH":

            explanation = (
                "Recent environmental conditions show multiple "
                "elevated signals. The system therefore classifies "
                "the location as HIGH risk."
            )

        elif risk_level == "WATCH":

            explanation = (
                "Some environmental indicators are elevated. "
                "The system recommends monitoring conditions."
            )

        else:

            explanation = (
                "Current environmental indicators do not show "
                "major elevated signals in this prototype."
            )


        st.info(
            explanation
        )


        # ====================================================
        # SINHALA WARNING
        # ====================================================

        st.subheader("🇱🇰 Sinhala Warning")


        if risk_level == "VERY HIGH":

            sinhala_message = (
                f"⚠️ TERRASIGNAL: {location_name} ප්‍රදේශයේ "
                "පාරිසරික අවදානම් සංඥා කිහිපයක් ඉහළ මට්ටමක පවතී. "
                "අවශ්‍ය නම් ආරක්ෂිත ස්ථානයකට යාමට සූදානම් වන්න."
            )

        elif risk_level == "HIGH":

            sinhala_message = (
                f"⚠️ TERRASIGNAL: {location_name} ප්‍රදේශයේ "
                "වැසි සහ පාරිසරික තත්ත්වයන් සැලකිලිමත් විය යුතු "
                "මට්ටමක පවතී. අවශ්‍ය ආරක්ෂක පියවර ගන්න."
            )

        elif risk_level == "WATCH":

            sinhala_message = (
                f"🟡 TERRASIGNAL: {location_name} ප්‍රදේශයේ "
                "පාරිසරික තත්ත්වයන් නිරීක්ෂණය කරන්න."
            )

        else:

            sinhala_message = (
                f"🟢 TERRASIGNAL: {location_name} ප්‍රදේශයේ "
                "දැනට විශාල පාරිසරික අවදානම් සංඥාවක් "
                "හඳුනාගෙන නොමැත."
            )


        st.success(
            sinhala_message
        )


        # ====================================================
        # VOICE MESSAGE CONCEPT
        # ====================================================

        st.subheader("🔊 Voice Warning")

        voice_message = (
            f"TerraSignal warning for {location_name}. "
            f"Current risk level is {risk_level}. "
            f"Recent rainfall is {recent_rainfall:.1f} millimeters."
        )

        st.write(
            voice_message
        )


        # ====================================================
        # NASA EVIDENCE
        # ====================================================

        st.markdown("---")

        st.subheader("🛰️ NASA Evidence")

        st.write(
            f"NASA POWER observation date: **{latest_date}**"
        )

        st.write(
            "NASA POWER variables used in this prototype:"
        )

        st.write(
            "• Precipitation"
        )

        st.write(
            "• Maximum temperature"
        )

        st.write(
            "• Relative humidity"
        )

        st.write(
            "• Wind speed"
        )

        st.write(
            "• Wind direction"
        )

        st.write(
            "• Surface pressure"
        )

        st.write(
            "• Solar radiation"
        )


        # ====================================================
        # RECENT RAINFALL
        # ====================================================

        st.subheader("🌧️ Recent Rainfall")

        st.write(
            f"Total rainfall across the available "
            f"7-day NASA POWER period: "
            f"**{recent_rainfall:.1f} mm**"
        )


        # ====================================================
        # DATA TABLE
        # ====================================================

        st.subheader("📊 NASA Data Snapshot")

        table_data = []

        for d in valid_dates:

            table_data.append(
                {
                    "Date": d,
                    "Rainfall (mm)": rainfall_data.get(d),
                    "Temperature (°C)": temperature_data.get(d),
                    "Humidity (%)": humidity_data.get(d),
                    "Wind (m/s)": wind_speed_data.get(d),
                    "Pressure (kPa)": pressure_data.get(d)
                }
            )


        st.dataframe(
            table_data,
            use_container_width=True
        )


        # ====================================================
        # ARCHITECTURE
        # ====================================================

        st.markdown("---")

        st.subheader("🧠 TerraSignal Architecture")

        st.code(
            """
NASA POWER
     ↓
Earth Observation Data
     ↓
Environmental Signals
     ↓
TerraSignal Risk Engine
     ↓
Risk Level + WHY
     ↓
Sinhala / English Message
     ↓
Web → SMS → Voice → Basic Phone
            """,
            language="text"
        )


        # ====================================================
        # ACCESSIBILITY
        # ====================================================

        st.subheader("📞 Accessibility Concept")

        st.write(
            "TerraSignal is designed so that the complex NASA "
            "data processing happens on the server side."
        )

        st.write(
            "A basic phone does not need to process NASA data. "
            "The final warning can be delivered through SMS or "
            "voice communication."
        )


        # ====================================================
        # PROTOTYPE NOTE
        # ====================================================

        st.warning(
            "Prototype note: risk thresholds are experimental "
            "and must be scientifically validated before "
            "real-world warning use."
        )


        # ====================================================
        # FUTURE NASA DATA
        # ====================================================

        st.subheader("🚀 Next Development Stage")

        st.write(
            "Future versions can integrate additional NASA "
            "Earth-observation datasets such as satellite "
            "precipitation products and historical baselines."
        )

        st.write(
            "The next scientific step is to validate the risk "
            "engine against historical environmental events "
            "before making operational warning claims."
        )

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as error:

        st.error(
            "⚠️ TerraSignal could not retrieve NASA data."
        )

        st.code(
            str(error)
        )

        st.info(
            "Please check the internet connection and NASA "
            "POWER API availability."
        )


# ============================================================
# NO USER REGISTERED
# ============================================================

else:

    st.info(
        "👤 Register a user first, then simulate a missed call "
        "to activate TerraSignal."
    )
