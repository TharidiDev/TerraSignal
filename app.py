import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta
from twilio.rest import Client


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="TerraSignal",
    page_icon="🌍",
    layout="centered"
)


# =========================================================
# LOCATIONS
# =========================================================

LOCATIONS = {
    "Colombo": (6.9271, 79.8612),
    "Kandy": (7.2906, 80.6337),
    "Galle": (6.0535, 80.2210),
    "Jaffna": (9.6615, 80.0255),
}


# =========================================================
# NASA POWER
# =========================================================

NASA_POWER_URL = (
    "https://power.larc.nasa.gov/api/temporal/daily/point"
)


@st.cache_data(ttl=3600)
def get_nasa_data(lat, lon, start_date, end_date):

    params = {
        "parameters": "PRECTOTCORR,T2M_MAX,RH2M,WS10M",
        "community": "RE",
        "longitude": lon,
        "latitude": lat,
        "start": start_date,
        "end": end_date,
        "format": "JSON",
    }

    try:

        response = requests.get(
            NASA_POWER_URL,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        p = data["properties"]["parameter"]

        rainfall = p.get("PRECTOTCORR", {})
        temperature = p.get("T2M_MAX", {})
        humidity = p.get("RH2M", {})
        wind = p.get("WS10M", {})

        rows = []

        for d in rainfall.keys():

            rows.append({
                "date": pd.to_datetime(d),
                "rainfall": rainfall.get(d, 0),
                "temperature": temperature.get(d, 0),
                "humidity": humidity.get(d, 0),
                "wind": wind.get(d, 0),
            })

        df = pd.DataFrame(rows)

        if df.empty:
            return None, "NASA returned no data."

        return (
            df.sort_values("date")
            .reset_index(drop=True),
            None
        )

    except Exception as e:

        return None, str(e)


# =========================================================
# HAZARD ENGINE
# =========================================================

def detect_hazards(df):

    latest = df.iloc[-1]

    rain_today = float(latest["rainfall"])
    temp_today = float(latest["temperature"])
    humidity_today = float(latest["humidity"])
    wind_today = float(latest["wind"])

    previous = df.iloc[:-1].tail(7)

    if len(previous) > 0:

        avg_rain = float(
            previous["rainfall"].mean()
        )

        total_recent_rain = float(
            previous["rainfall"].sum()
        )

        avg_temp = float(
            previous["temperature"].mean()
        )

    else:

        avg_rain = 0
        total_recent_rain = 0
        avg_temp = temp_today

    hazards = []

    # -----------------------------------------------------
    # FLOOD
    # -----------------------------------------------------

    if rain_today >= 50 or total_recent_rain >= 100:

        hazards.append({
            "name": "FLOOD",
            "emoji": "🌊",
            "level": "HIGH",
            "reason": (
                f"වැසි ප්‍රමාණය වැඩි වී ඇත. "
                f"අද {rain_today:.1f} mm සහ "
                f"පසුගිය දින කිහිපයේ "
                f"{total_recent_rain:.1f} mm පමණ වාර්තා වී ඇත."
            )
        })

    elif rain_today >= 20:

        hazards.append({
            "name": "FLOOD",
            "emoji": "🌊",
            "level": "WATCH",
            "reason": (
                f"අද වැසි ප්‍රමාණය "
                f"{rain_today:.1f} mm පමණ වේ."
            )
        })

    # -----------------------------------------------------
    # EXTREME HEAT
    # -----------------------------------------------------

    if temp_today >= 35:

        hazards.append({
            "name": "EXTREME HEAT",
            "emoji": "☀️",
            "level": "HIGH",
            "reason": (
                f"උපරිම උෂ්ණත්වය "
                f"{temp_today:.1f}°C දක්වා "
                f"ඉහළ ගොස් ඇත."
            )
        })

    elif temp_today >= 33:

        hazards.append({
            "name": "EXTREME HEAT",
            "emoji": "☀️",
            "level": "WATCH",
            "reason": (
                f"උෂ්ණත්වය "
                f"{temp_today:.1f}°C පමණ වේ."
            )
        })

    # -----------------------------------------------------
    # DROUGHT
    # -----------------------------------------------------

    if (
        len(df) >= 7
        and df["rainfall"].tail(7).sum() < 5
        and avg_temp >= 30
    ):

        hazards.append({
            "name": "DROUGHT",
            "emoji": "🌵",
            "level": "WATCH",
            "reason": (
                "පසුගිය දින කිහිපයේ වැසි "
                "ඉතා අඩු මට්ටමක පවතින අතර "
                "උෂ්ණත්වය ඉහළ මට්ටමක පවතී."
            )
        })

    # -----------------------------------------------------
    # LANDSLIDE PROTOTYPE
    # -----------------------------------------------------

    if (
        total_recent_rain >= 80
        and humidity_today >= 80
    ):

        hazards.append({
            "name": "LANDSLIDE",
            "emoji": "🪨",
            "level": "WATCH",
            "reason": (
                "අඛණ්ඩ වැසි සහ ඉහළ ආර්ද්‍රතාවය "
                "නිසා නායයෑමේ අවදානමක් "
                "පිළිබඳ අවධානය යොමු කළ යුතුය."
            )
        })

    # -----------------------------------------------------
    # SEVERE STORM PROTOTYPE
    # -----------------------------------------------------

    if wind_today >= 10 and rain_today >= 20:

        hazards.append({
            "name": "SEVERE STORM",
            "emoji": "🌀",
            "level": "WATCH",
            "reason": (
                f"වැසි සමඟ සුළං වේගය "
                f"{wind_today:.1f} m/s පමණ වේ."
            )
        })

    return hazards


# =========================================================
# MESSAGE GENERATOR
# =========================================================

def create_sinhala_message(
    location,
    hazards
):

    if not hazards:

        return (
            "TerraSignal\n"
            f"{location} ප්‍රදේශයේ "
            "දැනට විශේෂ පාරිසරික අවදානමක් "
            "හඳුනාගෙන නොමැත."
        )

    first = hazards[0]

    if first["name"] == "FLOOD":

        return (
            "TerraSignal\n"
            f"{location} ප්            "ප්‍රදේශයේ වැසි/ගංවතුර "
            "අවදානමක් හඳුනාගෙන ඇත.\n"
            "කරුණාකර ආරක්ෂිත ස්ථානයක සිටින්න."
        )

    if first["name"] == "EXTREME HEAT":

        return (
            "TerraSignal\n"
            f"{location} ප්‍රදේශයේ "
            "අධික උෂ්ණත්ව අවදානමක් ඇත.\n"
            "හැකිතාක් සිසිල් ස්ථානයක සිටින්න."
        )

    if first["name"] == "DROUGHT":

        return (
            "TerraSignal\n"
            f"{location} ප්‍රදේශයේ "
            "වියළි තත්ත්වයක් පවතී.\n"
            "ජලය අරපිරිමැස්මෙන් භාවිතා කරන්න."
        )

    if first["name"] == "LANDSLIDE":

        return (
            "TerraSignal\n"
            f"{location} ප්‍රදේශයේ "
            "නායයෑමේ අවදානමක් පිළිබඳ "
            "අවධානයෙන් සිටින්න.\n"
            "කඳු බෑවුම් ආසන්නයෙන් ඉවත් වන්න."
        )

    if first["name"] == "SEVERE STORM":

        return (
            "TerraSignal\n"
            f"{location} ප්‍රදේශයේ "
            "ප්‍රබල වැසි/සුළං තත්ත්වයක් ඇත.\n"
            "ආරක්ෂිත ස්ථානයක සිටින්න."
        )

    return (
        "TerraSignal\n"
        f"{location} ප්‍රදේශයේ "
        "අවදානම් තත්ත්වයක් හඳුනාගෙන ඇත."
    )


# =========================================================
# TWILIO SMS
# =========================================================

def send_sms(phone_number, message):

    account_sid = st.secrets["TWILIO_ACCOUNT_SID"]
    auth_token = st.secrets["TWILIO_AUTH_TOKEN"]
    from_number = st.secrets["TWILIO_FROM_NUMBER"]

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

st.title("🌍 TerraSignal")

st.subheader(
    "NASA Earth Data → Multi-Hazard Warning → Nokia"
)

st.write(
    "Smartphone app එකක් භාවිතා නොකරන "
    "වැඩිහිටියන් වෙත පාරිසරික අවදානම් "
    "සරල පණිවිඩයක් ලෙස ලබාදීම සඳහා "
    "නිර්මාණය කළ prototype එකකි."
)

st.divider()


# =========================================================
# PERSON
# =========================================================

st.subheader("👵 Alert Recipient")

person = st.selectbox(
    "Person",
    [
        "Grandmother",
        "Grandfather",
        "Family Member"
    ]
)


# =========================================================
# LOCATION
# =========================================================

st.subheader("📍 Location")

location = st.selectbox(
    "Location",
    list(LOCATIONS.keys())
)

lat, lon = LOCATIONS[location]


# =========================================================
# NASA DATA
# =========================================================

observation_date = date.today() - timedelta(days=2)

start_date = (
    observation_date - timedelta(days=14)
)

with st.spinner(
    "🌍 NASA Earth observations ලබාගනිමින්..."
):

    df, error = get_nasa_data(
        lat,
        lon,
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
# DETECT HAZARDS
# =========================================================

hazards = detect_hazards(df)


# =========================================================
# STATUS
# =========================================================

st.divider()

if hazards:

    st.subheader(
        "🚨 TerraSignal Alert"
    )

    st.error(
        f"{len(hazards)} hazard signal(s) detected."
    )

else:

    st.subheader(
        "🟢 TerraSignal Status"
    )

    st.success(
        "දැනට විශේෂ අවදානම් signal එකක් "
        "හඳුනාගෙන නොමැත."
    )


# =========================================================
# HAZARDS
# =========================================================

if hazards:

    for hazard in hazards:

        st.markdown(
            f"### {hazard['emoji']} "
            f"{hazard['name']}"
        )

        if hazard["level"] == "HIGH":

            st.error(
                f"🔴 HIGH — {hazard['reason']}"
            )

        else:

            st.warning(
                f"🟠 WATCH — {hazard['reason']}"
            )


# =========================================================
# SIMPLE NASA DATA
# =========================================================

latest = df.iloc[-1]

st.divider()

st.subheader(
    "🌍 What NASA is seeing"
)

c1, c2, c3 = st.columns(3)

c1.metric(
    "🌧️ Rain",
    f"{float(latest['rainfall']):.1f} mm"
)

c2.metric(
    "🌡️ Temperature",
    f"{float(latest['temperature']):.1f} °C"
)

c3.metric(
    "💨 Wind",
    f"{float(latest['wind']):.1f} m/s"
)


# =========================================================
# WHY
# =========================================================

st.divider()

st.subheader(
    "❓ WHY did TerraSignal alert?"
)

if hazards:

    for hazard in hazards:

        st.write(
            f"{hazard['emoji']} "
            f"**{hazard['name']}** — "
            f"{hazard['reason']}"
        )

else:

    st.write(
        "NASA environmental observations වලින් "
        "prototype thresholds ඉක්මවූ signal එකක් "
        "හඳුනාගෙන නොමැත."
    )


# =========================================================
# NOKIA SMS
# =========================================================

st.divider()

st.header(
    "📱 Send Warning to Nokia"
)

phone_number = st.text_input(
    "Nokia phone number",
    placeholder="+947XXXXXXXX"
)


sinhala_message = create_sinhala_message(
    location,
    hazards
)


st.subheader(
    "💬 Message that the Nokia will receive"
)

st.code(
    sinhala_message,
    language="text"
)


if st.button(
    "📲 SEND SMS TO NOKIA",
    type="primary",
    use_container_width=True
):

    if not phone_number:

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
                "📡 TerraSignal warning යවමින්..."
            ):

                message_id = send_sms(
                    phone_number,
                    sinhala_message
                )

            st.success(
                "✅ Warning එක Nokia phone එකට යැව්වා!"
            )

            st.caption(
                f"Message ID: {message_id}"
            )

        except Exception as e:

            st.error(
                "❌ SMS එක යැවීමට නොහැකි විය."
            )

            st.code(str(e))


# =========================================================
# MISSED CALL DEMO
# =========================================================

st.divider()

st.header(
    "📞 Missed Call Alert"
)

st.write(
    "Risk එකක් detect වුණාම recipientට "
    "missed-call notification එකක් ලබාදෙන "
    "communication concept එක."
)

if hazards:

    if st.button(
        "📞 SIMULATE MISSED CALL"
    ):

        st.success(
            f"📞 Demo missed call created "
            f"for {person}."
        )

        st.info(
            "මෙය prototype simulation එකකි. "
            "Real telephony connection එකක් "
            "වෙනම integrate කළ යුතුය."
        )

else:

    st.info(
        "Risk signal එකක් නැති නිසා "
        "missed call අවශ්‍ය නැත."
    )


# =========================================================
# DATA
# =========================================================

with st.expander(
    "🔬 NASA data / technical details"
):

    st.write(
        """
        Primary data source:
        NASA POWER daily environmental observations.

        Prototype signals:
        • Flood / heavy rainfall
        • Extreme heat
        • Drought
        • Rainfall-based landslide indicator
        • Rain + wind storm indicator

        Important:
        These thresholds are experimental.
        They are NOT official disaster warnings.
        Dedicated NASA hazard products and
        historical validation should be added
        before operational use.
        """
    )

    st.dataframe(
        df,
        use_container_width=True
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "🌍 TerraSignal — Earth Intelligence. Human Reach."
)
