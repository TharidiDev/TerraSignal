import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta


# =========================================================
# TERRASIGNAL
# NASA SPACE APPS 2026
# Sri Lanka-wide accessible multi-hazard warning prototype
# =========================================================

st.set_page_config(
    page_title="TerraSignal",
    page_icon="🌍",
    layout="wide"
)


# =========================================================
# SRI LANKA DISTRICTS
# =========================================================

DISTRICTS = {
    "Ampara": (7.2917, 81.6722),
    "Anuradhapura": (8.3114, 80.4037),
    "Badulla": (6.9934, 81.0550),
    "Batticaloa": (7.7310, 81.6747),
    "Colombo": (6.9271, 79.8612),
    "Galle": (6.0329, 80.2168),
    "Gampaha": (7.0840, 80.0098),
    "Hambantota": (6.1429, 81.1212),
    "Jaffna": (9.6615, 80.0255),
    "Kalutara": (6.5854, 79.9607),
    "Kandy": (7.2906, 80.6337),
    "Kegalle": (7.2513, 80.3464),
    "Kilinochchi": (9.3803, 80.3770),
    "Kurunegala": (7.4863, 80.3647),
    "Mannar": (8.9810, 79.9044),
    "Matale": (7.4675, 80.6234),
    "Matara": (5.9549, 80.5550),
    "Monaragala": (6.8728, 81.3507),
    "Mullaitivu": (9.2671, 80.8128),
    "Nuwara Eliya": (6.9497, 80.7891),
    "Polonnaruwa": (7.9403, 81.0188),
    "Puttalam": (8.0362, 79.8283),
    "Ratnapura": (6.6828, 80.3992),
    "Trincomalee": (8.5874, 81.2152),
    "Vavuniya": (8.7542, 80.4982),
}


# =========================================================
# NASA POWER DATA
# =========================================================

@st.cache_data(ttl=1800)
def get_nasa_data(latitude, longitude):

    end_date = date.today() - timedelta(days=2)
    start_date = end_date - timedelta(days=14)

    url = "https://power.larc.nasa.gov/api/temporal/daily/point"

    params = {
        "parameters": "PRECTOTCORR,T2M_MAX,RH2M,WS10M",
        "community": "AG",
        "longitude": longitude,
        "latitude": latitude,
        "start": start_date.strftime("%Y%m%d"),
        "end": end_date.strftime("%Y%m%d"),
        "format": "JSON"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        values = data["properties"]["parameter"]

        dates = sorted(values["PRECTOTCORR"].keys())

        rows = []

        for d in dates:
            rows.append({
                "date": pd.to_datetime(d),
                "rainfall": float(
                    values["PRECTOTCORR"].get(d, 0)
                ),
                "temperature": float(
                    values["T2M_MAX"].get(d, 0)
                ),
                "humidity": float(
                    values["RH2M"].get(d, 0)
                ),
                "wind": float(
                    values["WS10M"].get(d, 0)
                )
            })

        return pd.DataFrame(rows)

    except Exception as e:
        st.error("NASA data could not be loaded.")
        st.code(str(e))
        return pd.DataFrame()


# =========================================================
# HAZARD DETECTION
# =========================================================

def detect_hazards(df):

    if df.empty:
        return []

    latest = df.iloc[-1]

    rain = float(latest["rainfall"])
    temperature = float(latest["temperature"])
    humidity = float(latest["humidity"])
    wind = float(latest["wind"])

    previous = df.iloc[:-1].tail(7)

    if len(previous) > 0:
        recent_rain = float(
            previous["rainfall"].sum()
        )
    else:
        recent_rain = 0.0

    hazards = []

    # -----------------------------------------------------
    # FLOOD / HEAVY RAIN
    # -----------------------------------------------------

    if rain >= 50 or recent_rain >= 100:

        hazards.append({
            "name": "Flood / Heavy Rain",
            "level": "HIGH",
            "emoji": "🌊",
            "reason": (
                f"Recent rainfall is high. "
                f"Latest rainfall: {rain:.1f} mm. "
                f"Previous rainfall: {recent_rain:.1f} mm."
            )
        })

    elif rain >= 20:

        hazards.append({
            "name": "Heavy Rain",
            "level": "WATCH",
            "emoji": "🌧️",
            "reason": (
                f"Latest rainfall is "
                f"{rain:.1f} mm."
            )
        })

    # -----------------------------------------------------
    # EXTREME HEAT
    # -----------------------------------------------------

    if temperature >= 35:

        hazards.append({
            "name": "Extreme Heat",
            "level": "HIGH",
            "emoji": "☀️",
            "reason": (
                f"Maximum temperature is "
                f"{temperature:.1f} °C."
            )
        })

    elif temperature >= 33:

        hazards.append({
            "name": "High Heat",
            "level": "WATCH",
            "emoji": "☀️",
            "reason": (
                f"Temperature is "
                f"{temperature:.1f} °C."
            )
        })

    # -----------------------------------------------------
    # DROUGHT INDICATOR
    # -----------------------------------------------------

    last_7_days = df.tail(7)

    seven_day_rain = float(
        last_7_days["rainfall"].sum()
    )

    if (
        len(last_7_days) >= 7
        and seven_day_rain < 5
        and temperature >= 30
    ):

        hazards.append({
            "name": "Drought Indicator",
            "level": "WATCH",
            "emoji": "🌵",
            "reason": (
                "Rainfall has been very low "
                "during the last 7 days while "
                "temperature remains high."
            )
        })

    # -----------------------------------------------------
    # LANDSLIDE INDICATOR
    # -----------------------------------------------------

    if recent_rain >= 80 and humidity >= 80:

        hazards.append({
            "name": "Landslide Indicator",
            "level": "WATCH",
            "emoji": "🪨",
            "reason": (
                "Recent rainfall and humidity "
                "indicate potentially unstable "
                "environmental conditions."
            )
        })

    # -----------------------------------------------------
    # STORM INDICATOR
    # -----------------------------------------------------

    if wind >= 10 and rain >= 20:

        hazards.append({
            "name": "Severe Storm Indicator",
            "level": "WATCH",
            "emoji": "🌀",
            "reason": (
                f"Rainfall is occurring with "
                f"wind speed around {wind:.1f} m/s."
            )
        })

    return hazards


# =========================================================
# WARNING MESSAGE
# =========================================================

def create_warning(district, hazards, language):

    if not hazards:

        if language == "සිංහල":

            return (
                f"TerraSignal\n"
                f"{district}\n\n"
                f"දැනට විශේෂ පාරිසරික අවදානමක් "
                f"හඳුනාගෙන නොමැත.\n\n"
                f"යාවත්කාලීන තොරතුරු සඳහා "
                f"අවධානයෙන් සිටින්න."
            )

        elif language == "தமிழ்":

            return (
                f"TerraSignal\n"
                f"{district}\n\n"
                f"தற்போது குறிப்பிடத்தக்க "
                f"சுற்றுச்சூழல் அபாயம் "
                f"கண்டறியப்படவில்லை."
            )

        else:

            return (
                f"TerraSignal\n"
                f"{district}\n\n"
                f"No significant environmental "
                f"risk indicator detected at "
                f"this time."
            )

    main_hazard = hazards[0]

    hazard_name = main_hazard["name"]
    level = main_hazard["level"]

    if language == "සිංහල":

        return (
            f"TerraSignal ⚠️\n"
            f"{district}\n\n"
            f"අවදානම: {hazard_name}\n"
            f"මට්ටම: {level}\n\n"
            f"පාරිසරික තත්ත්වයන් පිළිබඳ "
            f"අවධානයෙන් සිටින්න.\n"
            f"අවශ්‍ය නම් ආරක්ෂිත ස්ථානයකට "
            f"යන්න.\n\n"
            f"මෙය TerraSignal prototype "
            f"indicator එකකි."
        )

    elif language == "தமிழ்":

        return (
            f"TerraSignal ⚠️\n"
            f"{district}\n\n"
            f"அபாயம்: {hazard_name}\n"
            f"நிலை: {level}\n\n"
            f"சுற்றுச்சூழல் நிலைமைகளை "
            f"கவனமாக கண்காணிக்கவும்."
        )

    else:

        return (
            f"TerraSignal ⚠️\n"
            f"{district}\n\n"
            f"Hazard: {hazard_name}\n"
            f"Level: {level}\n\n"
            f"Please monitor local conditions "
            f"and follow official safety advice."
        )


# =========================================================
# PAGE HEADER
# =========================================================

st.title("🌍 TerraSignal")

st.subheader(
    "Decoding Earth's signals for the 60s–70s generation"
)

st.write(
    "A Sri Lanka-wide accessible multi-hazard "
    "environmental warning prototype using NASA Earth data."
)

st.divider()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("📍 Your Location")

district = st.sidebar.selectbox(
    "Select your district",
    list(DISTRICTS.keys())
)

language = st.sidebar.selectbox(
    "Warning language",
    [
        "සිංහල",
        "தமிழ்",
        "English"
    ]
)

st.sidebar.divider()

st.sidebar.info(
    "TerraSignal is designed to deliver "
    "simple warnings to people using "
    "basic phones, including Nokia phones."
)


# =========================================================
# USER REGISTRATION
# =========================================================

st.header("📱 Register a Basic Phone")

col1, col2 = st.columns(2)

with col1:

    name = st.text_input(
        "Name",
        placeholder="Enter your name"
    )

    phone = st.text_input(
        "Nokia / Basic phone number",
        placeholder="+947XXXXXXXX"
    )

with col2:

    registered_district = st.selectbox(
        "Registered district",
        list(DISTRICTS.keys()),
        key="registered_district"
    )

    registered_language = st.selectbox(
        "Preferred warning language",
        [
            "සිංහල",
            "தமிழ்",
            "English"
        ],
        key="registered_language"
    )

if st.button(
    "💾 Register Phone",
    key="register_phone"
):

    if name and phone:

        st.session_state["registered"] = True
        st.session_state["user_name"] = name
        st.session_state["user_phone"] = phone
        st.session_state["user_district"] = registered_district
        st.session_state["user_language"] = registered_language

        st.success(
            f"{name} registered successfully."
        )

    else:

        st.warning(
            "Please enter both name and phone number."
        )


# =========================================================
# NASA DATA
# =========================================================

st.divider()

st.header("🛰️ NASA Earth Signal")

latitude, longitude = DISTRICTS[district]

st.write(
    f"Monitoring: **{district}, Sri Lanka**"
)

with st.spinner(
    "Connecting to NASA POWER..."
):

    df = get_nasa_data(
        latitude,
        longitude
    )


# =========================================================
# DISPLAY NASA DATA
# =========================================================

if not df.empty:

    hazards = detect_hazards(df)

    latest = df.iloc[-1]

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "🌧️ Rainfall",
            f"{latest['rainfall']:.1f} mm"
        )

    with col2:

        st.metric(
            "🌡️ Temperature",
            f"{latest['temperature']:.1f} °C"
        )

    with col3:

        st.metric(
            "💧 Humidity",
            f"{latest['humidity']:.1f} %"
        )

    with col4:

        st.metric(
            "💨 Wind",
            f"{latest['wind']:.1f} m/s"
        )


    # =====================================================
    # HAZARD STATUS
    # =====================================================

    st.divider()

    st.header("⚠️ TerraSignal Risk Engine")

    if hazards:

        for hazard in hazards:

            if hazard["level"] == "HIGH":

                st.error(
                    f"{hazard['emoji']} "
                    f"{hazard['name']} — "
                    f"{hazard['level']}"
                )

            else:

                st.warning(
                    f"{hazard['emoji']} "
                    f"{hazard['name']} — "
                    f"{hazard['level']}"
                )

            st.write(
                f"**WHY:** {hazard['reason']}"
            )

    else:

        st.success(
            "✅ No major prototype hazard "
            "indicator detected."
        )


    # =====================================================
    # RAINFALL CHART
    # =====================================================

    st.divider()

    st.header("📊 NASA Rainfall Signal")

    chart_data = df[
        ["date", "rainfall"]
    ].set_index("date")

    st.line_chart(
        chart_data
    )


    # =====================================================
    # NOKIA WARNING
    # =====================================================

    st.divider()

    st.header("📱 Nokia Warning")

    warning = create_warning(
        district,
        hazards,
        language
    )

    st.code(
        warning,
        language=None
    )


    # =====================================================
    # SEND ALERT
    # =====================================================

    if "registered" in st.session_state:

        user_district = st.session_state.get(
            "user_district",
            district
        )

        user_phone = st.session_state.get(
            "user_phone",
            ""
        )

        user_language = st.session_state.get(
            "user_language",
            "සිංහල"
        )

        st.write(
            f"Registered phone: "
            f"**{user_phone}**"
        )

        st.write(
            f"Registered district: "
            f"**{user_district}**"
        )

        registered_hazards = hazards

        registered_warning = create_warning(
            user_district,
            registered_hazards,
            user_language
        )

        if st.button(
            "📨 SEND ALERT TO NOKIA",
            key="send_nokia_alert"
        ):

            st.success(
                "📨 Prototype alert generated."
            )

            st.code(
                registered_warning,
                language=None
            )

            st.info(
                "In this prototype the alert is "
                "simulated. Real SMS requires a "
                "telecom/SMS gateway such as Twilio."
            )

    else:

        st.info(
            "Register a phone above to activate "
            "the Nokia alert demonstration."
        )


    # =====================================================
    # MISSED CALL CONCEPT
    # =====================================================

    st.divider()

    st.header("📞 Missed-Call Alert Concept")

    st.write(
        "For users with very basic phones, "
        "TerraSignal can use a missed-call "
        "signal as an attention mechanism."
    )

    if st.button(
        "📞 SIMULATE MISSED CALL",
        key="missed_call"
    ):

        st.success(
            f"📞 Simulated missed call sent "
            f"to {phone if phone else 'registered phone'}"
        )

        st.write(
            "Concept: user sees a missed call "
            "→ opens/reads SMS → receives a "
            "simple environmental warning."
        )


    # =====================================================
    # TECHNICAL DETAILS
    # =====================================================

    st.divider()

    with st.expander(
        "🛰️ Technical Details"
    ):

        st.write(
            "**NASA Data Source:** NASA POWER"
        )

        st.write(
            "**Current environmental variables:**"
        )

        st.write(
            "- Precipitation"
        )

        st.write(
            "- Maximum temperature"
        )

        st.write(
            "- Relative humidity"
        )

        st.write(
            "- Wind speed"
        )

        st.write(
            "**Processing:**"
        )

        st.write(
            "NASA environmental signals → "
            "TerraSignal rule-based prototype "
            "risk engine → hazard indicator → "
            "simple warning."
        )

        st.write(
            "**Future NASA integrations:**"
        )

        st.write(
            "- NASA GPM / IMERG rainfall"
        )

        st.write(
            "- NASA FIRMS wildfire data"
        )

        st.write(
            "- NASA LHASA landslide model"
        )

        st.write(
            "- Satellite-based drought indicators"
        )

        st.write(
            "- Additional Earth-observation datasets"
        )


# =========================================================
# PROTOTYPE DISCLAIMER
# =========================================================

st.divider()

st.caption(
    "Prototype note: TerraSignal risk thresholds "
    "are experimental and must be scientifically "
    "validated before real-world warning use. "
    "This prototype does not replace official "
    "emergency warnings."
)

st.caption(
    "TerraSignal — NASA Space Apps 2026"
)
