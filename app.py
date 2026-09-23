import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta
from twilio.rest import Client


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="TerraSignal Sri Lanka",
    page_icon="🌍",
    layout="centered"
)


# =========================================================
# SRI LANKA DISTRICTS
# =========================================================

DISTRICTS = {
    "Ampara": (7.2914, 81.6720),
    "Anuradhapura": (8.3114, 80.4037),
    "Badulla": (6.9934, 81.0550),
    "Batticaloa": (7.7170, 81.7000),
    "Colombo": (6.9271, 79.8612),
    "Galle": (6.0535, 80.2210),
    "Gampaha": (7.0873, 80.0144),
    "Hambantota": (6.1429, 81.1212),
    "Jaffna": (9.6615, 80.0255),
    "Kalutara": (6.5854, 79.9607),
    "Kandy": (7.2906, 80.6337),
    "Kegalle": (7.2513, 80.3464),
    "Kilinochchi": (9.3803, 80.3770),
    "Kurunegala": (7.4863, 80.3623),
    "Mannar": (8.9810, 79.9044),
    "Matale": (7.4675, 80.6234),
    "Matara": (5.9549, 80.5550),
    "Monaragala": (6.8728, 81.3507),
    "Mullaitivu": (9.2671, 80.8142),
    "Nuwara Eliya": (6.9497, 80.7891),
    "Polonnaruwa": (7.9403, 81.0188),
    "Puttalam": (8.0362, 79.8283),
    "Ratnapura": (6.6828, 80.3992),
    "Trincomalee": (8.5874, 81.2152),
    "Vavuniya": (8.7514, 80.4971)
}


# =========================================================
# NASA POWER
# =========================================================

NASA_POWER_URL = (
    "https://power.larc.nasa.gov/api/temporal/daily/point"
)


@st.cache_data(ttl=3600)
def get_nasa_data(
    latitude,
    longitude,
    start_date,
    end_date
):

    parameters = (
        "PRECTOTCORR,"
        "T2M_MAX,"
        "RH2M,"
        "WS10M"
    )

    params = {
        "parameters": parameters,
        "community": "RE",
        "longitude": longitude,
        "latitude": latitude,
        "start": start_date,
        "end": end_date,
        "format": "JSON"
    }

    try:

        response = requests.get(
            NASA_POWER_URL,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        parameter_data = (
            data["properties"]["parameter"]
        )

        rainfall = parameter_data.get(
            "PRECTOTCORR", {}
        )

        temperature = parameter_data.get(
            "T2M_MAX", {}
        )

        humidity = parameter_data.get(
            "RH2M", {}
        )

        wind = parameter_data.get(
            "WS10M", {}
        )

        rows = []

        for d in rainfall.keys():

            rows.append({
                "date": pd.to_datetime(d),
                "rainfall": rainfall.get(d, 0),
                "temperature": temperature.get(d, 0),
                "humidity": humidity.get(d, 0),
                "wind": wind.get(d, 0)
            })

        df = pd.DataFrame(rows)

        if df.empty:
            return None, "NASA POWER returned no data."

        df = (
            df.sort_values("date")
            .reset_index(drop=True)
        )

        return df, None

    except Exception as error:

        return None, str(error)


# =========================================================
# HAZARD ENGINE
# =========================================================

def detect_hazards(df):

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

        recent_rain = 0

    hazards = []

    # -----------------------------------------------------
    # FLOOD / HEAVY RAIN
    # -----------------------------------------------------

    if rain >= 50 or recent_rain >= 100:

        hazards.append({
            "name": "Flood / Heavy Rain",
            "emoji": "🌊",
            "level": "HIGH",
            "reason": (
                f"වැසි ප්‍රමාණය ඉහළයි. "
                f"අද {rain:.1f} mm සහ "
                f"පසුගිය දිනවල එකතුව "
                f"{recent_rain:.1f} mm පමණයි."
            )
        )

    elif rain >= 20:

        hazards.append({
            "name": "Heavy Rain",
            "emoji": "🌧️",
            "level": "WATCH",
            "reason": (
                f"අද වැසි ප්‍රමාණය "
                f"{rain:.1f} mm පමණයි."
            )
        })

    # -----------------------------------------------------
    # EXTREME HEAT
    # -----------------------------------------------------

    if temperature >= 35:

        hazards.append({
            "name": "Extreme Heat",
            "emoji": "☀️",
            "level": "HIGH",
            "reason": (
                f"උපරිම උෂ්ණත්වය "
                f"{temperature:.1f}°C පමණයි."
            )
        )

    elif temperature >= 33:

        hazards.append({
            "name": "High Heat",
            "emoji": "☀️",
            "level": "WATCH",
            "reason": (
                f"උෂ්ණත්වය "
                f"{temperature:.1f}°C පමණ ඉහළයි."
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
            "emoji": "🌵",
            "level": "WATCH",
            "reason": (
                "පසුගිය දින 7 තුළ වැසි ඉතා අඩු "
                "මට්ටමක පවතින අතර උෂ්ණත්වය ඉහළයි."
            )
        })

    # -----------------------------------------------------
    # LANDSLIDE INDICATOR
    # -----------------------------------------------------

    if recent_rain >= 80 and humidity >= 80:

        hazards.append({
            "name": "Landslide Indicator",
            "emoji": "🪨",
            "level": "WATCH",
            "reason": (
                "අඛණ්ඩ වැසි සහ ඉහළ ආර්ද්‍රතාවය "
                "නිසා නායයෑම් සඳහා අවදානම් "
                "පාරිසරික තත්ත්වයක් පෙන්වයි."
            )
        })

    # -----------------------------------------------------
    # STORM INDICATOR
    # -----------------------------------------------------

    if wind >= 10 and rain >= 20:

        hazards.append({
            "name": "Severe Storm Indicator",
            "emoji": "🌀",
            "level": "WATCH",
            "reason": (
                f"වැසි සමඟ සුළං වේගය "
                f"{wind:.1f} m/s පමණයි."
            )
        })

    return hazards


# =========================================================
# SINHALA MESSAGE
# =========================================================

def create_sinhala_message(
    district,
    hazards
):

    if not hazards:

        return (
            "TerraSignal\n"
            f"{district} ප්‍රදේශයේ දැනට "
            "විශේෂ අවදානම් signal එකක් "
            "හඳුනාගෙන නොමැත."
        )

    names = []

    for hazard in hazards:
        names.append(hazard["name"])

    hazard_text = ", ".join(names)

    first = hazards[0]

    if "Flood" in first["name"] or "Rain" in first["name"]:

        action = (
            "වැසි/ගංවතුර තත්ත්වය පිළිබඳ "
            "අවධානයෙන් සිටින්න."
        )

    elif "Heat" in first["name"]:

        action = (
            "හැකිතාක් සිසිල් ස්ථානයක සිටින්න "
            "සහ ජලය පානය කරන්න."
        )

    elif "Drought" in first["name"]:

        action = (
            "ජලය අරපිරිමැස්මෙන් භාවිතා කරන්න."
        )

    elif "Landslide" in first["name"]:

        action = (
            "කඳු බෑවුම් ආසන්නයෙන් "
            "ඉවත් වී ආරක්ෂිත ස්ථානයක සිටින්න."
        )

    elif "Storm" in first["name"]:

        action = (
            "ආරක්ෂිත ස්ථානයක සිටින්න."
        )

    else:

        action = (
            "කරුණාකර ආරක්ෂිත ස්ථානයක සිටින්න."
        )

    return (
        "TerraSignal\n"
        f"{district} ප්‍රදේශයේ {hazard_text} "
        "පිළිබඳ අවදානම් signal එකක් ඇත.\n"
        f"{action}"
    )


# =========================================================
# TWILIO
# =========================================================

def send_sms(phone_number, message):

    account_sid = st.secrets[
        "TWILIO_ACCOUNT_SID"
    ]

    auth_token = st.secrets[
        "TWILIO_AUTH_TOKEN"
    ]

    from_number = st.secrets[
        "TWILIO_FROM_NUMBER"
    ]

    client = Client(
        account_sid,
        auth_token
    )

    result = client.messages.create(
        body=message,
        from_=from_number,
        to=phone_number
    )

    return result.sid


# =========================================================
# HEADER
# =========================================================

st.title("🌍 TerraSignal Sri Lanka")

st.subheader(
    "Multi-Hazard Early Warning for Basic Phones"
)

st.write(
    "NASA Earth observations භාවිතා කරමින් "
    "පාරිසරික අවදානම් හඳුනාගෙන, "
    "smartphone එකක් අවශ්‍ය නොවන ලෙස "
    "සරල warning එකක් phone එකකට ලබාදීම."
)

st.divider()


# =========================================================
# RECIPIENT
# =========================================================

st.header("👤 Alert Recipient")

recipient_name = st.text_input(
    "Name",
    placeholder="ඔබේ නම"
)

phone_number = st.text_input(
    "Nokia / Basic Phone Number",
    placeholder="+947XXXXXXXX"
)


# =========================================================
# DISTRICT
# =========================================================

st.header("📍 Your District")

district = st.selectbox(
    "District",
    list(DISTRICTS.keys())
)

latitude, longitude = DISTRICTS[district]


# =========================================================
# LANGUAGE
# =========================================================

language = st.selectbox(
    "Alert Language",
    [
        "Sinhala",
        "English"
    ]
)


# =========================================================
# HAZARD INFORMATION
# =========================================================

st.divider()

st.header("🚨 Hazards TerraSignal Monitors")

st.write(
    """
    🌊 Flood / Heavy Rain  
    🪨 Landslide indicators  
    🌀 Severe storm indicators  
    ☀️ Extreme heat  
    🌵 Drought indicators  
    🔥 Wildfire — future dedicated NASA data integration
    """
)


# =========================================================
# GET NASA DATA
# =========================================================

observation_date = (
    date.today() - timedelta(days=2)
)

start_date = (
    observation_date - timedelta(days=14)
)

with st.spinner(
    "🌍 NASA Earth data ලබාගනිමින්..."
):

    df, error = get_nasa_data(
        latitude,
        longitude,
        start_date.strftime("%Y%m%d"),
        observation_date.strftime("%Y%m%d")
    )


if error:

    st.error(
        "NASA data ලබාගැනීමට නොහැකි විය."
    )

    st.code(error)

    st.stop()


# =========================================================
# DETECT
# =========================================================

hazards = detect_hazards(df)


# =========================================================
# STATUS
# =========================================================

st.divider()

st.header("🌍 Current TerraSignal Status")

if hazards:

    st.error(
        f"🚨 {len(hazards)} hazard signal(s) detected "
        f"for {district}."
    )

    for hazard in hazards:

        if hazard["level"] == "HIGH":

            st.error(
                f"{hazard['emoji']} "
                f"{hazard['name']} — HIGH"
            )

        else:

            st.warning(
                f"{hazard['emoji']} "
                f"{hazard['name']} — WATCH"
            )

else:

    st.success(
        f"🟢 No elevated hazard indicator "
        f"detected for {district}."
    )


# =========================================================
# WHY
# =========================================================

st.header("❓ Why?")

if hazards:

    for hazard in hazards:

        st.write(
            f"{hazard['emoji']} "
            f"**{hazard['name']}**"
        )

        st.write(
            hazard["reason"]
        )

else:

    st.write(
        "Current prototype thresholds වලට අනුව "
        "elevated environmental signal එකක් "
        "හඳුනාගෙන නොමැත."
    )


# =========================================================
# SIMPLE DATA
# =========================================================

latest = df.iloc[-1]

st.divider()

st.header("🌎 NASA Environmental Signal")

c1, c2, c3 = st.columns(3)

c1.metric(
    "Rain",
    f"{float(latest['rainfall']):.1f} mm"
)

c2.metric(
    "Temperature",
    f"{float(latest['temperature']):.1f} °C"
)

c3.metric(
    "Wind",
    f"{float(latest['wind']):.1f} m/s"
)


# =========================================================
# SMS
# =========================================================

st.divider()

st.header("📱 Nokia Alert")

sinhala_message = create_sinhala_message(
    district,
    hazards
)

if language == "Sinhala":

    message_to_send = sinhala_message

else:

    if hazards:

        message_to_send = (
            "TerraSignal\n"
            f"Alert for {district}.\n"
            "Please monitor official safety "
            "instructions and remain alert."
        )

    else:

        message_to_send = (
            "TerraSignal\n"
            f"No elevated hazard indicator "
            f"detected for {district}."
        )


st.subheader(
    "📩 Message Preview"
)

st.code(
    message_to_send,
    language="text"
)


# =========================================================
# SEND SMS
# =========================================================

if st.button(
    "📲 SEND ALERT TO NOKIA",
    type="primary",
    use_container_width=True
):

    if not recipient_name:

        st.warning(
            "Recipient name එක ඇතුළත් කරන්න."
        )

    elif not phone_number:

        st.warning(
            "Nokia phone number එක ඇතුළත් කරන්න."
        )

    elif not phone_number.startswith("+94"):

        st.warning(
            "Sri Lankan number එක "
            "+94 format එකෙන් දාන්න."
        )

    else:

        try:

            with st.spinner(
                "📡 Nokia phone එකට warning එක යවමින්..."
            ):

                message_id = send_sms(
                    phone_number,
                    message_to_send
                )

            st.success(
                f"✅ Alert sent to {recipient_name}!"
            )

            st.write(
                "📱 Nokia phone එකේ SMS එක check කරන්න."
            )

            st.caption(
                f"Message ID: {message_id}"
            )

        except Exception as error:

            st.error(
                "❌ SMS යැවීමට නොහැකි විය."
            )

            st.code(str(error))


# =========================================================
# MISSED CALL CONCEPT
# =========================================================

st.divider()

st.header("📞 Missed-Call Alert Concept")

if hazards:

    st.warning(
        "🚨 Hazard signal detected"
    )

    st.write(
        f"{recipient_name or 'Registered user'} "
        f"({district}) වෙත missed-call alert එකක් "
        "trigger කළ හැක."
    )

    if st.button(
        "📞 SIMULATE MISSED CALL"
    ):

        st.success(
            "✅ Missed-call event simulated."
        )

        st.caption(
            "Prototype simulation only. "
            "Real telephony integration "
            "is required for an actual missed call."
        )

else:

    st.info(
        "Risk signal එකක් නැති නිසා "
        "missed-call alert එකක් අවශ්‍ය නැත."
    )


# =========================================================
# DATA
# =========================================================

with st.expander(
    "🔬 NASA Data / Technical Details"
):

    st.write(
        f"District: {district}"
    )

    st.write(
        f"Coordinates: "
        f"{latitude:.4f}, {longitude:.4f}"
    )

    st.write(
        "Primary data source: NASA POWER"
    )

    st.dataframe(
        df,
        use_container_width=True
    )

    st.warning(
        "Prototype note: hazard thresholds are "
        "experimental and must be scientifically "
        "validated before real-world warning use."
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "🌍 TerraSignal — Earth Intelligence. Human Reach."
)
