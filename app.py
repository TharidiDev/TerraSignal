import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="TerraSignal V2",
    page_icon="🌍",
    layout="wide"
)

# ============================================================
# CONSTANTS
# ============================================================

LOCATIONS = {
    "Colombo": (6.9271, 79.8612),
    "Kandy": (7.2906, 80.6337),
    "Galle": (6.0535, 80.2210),
    "Jaffna": (9.6615, 80.0255)
}

NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# ============================================================
# NASA POWER DATA
# ============================================================

@st.cache_data(ttl=3600)
def get_nasa_power_data(lat, lon, start_date, end_date):

    parameters = (
        "PRECTOTCORR,"
        "T2M_MAX,"
        "RH2M,"
        "WS10M,"
        "WD10M,"
        "PS,"
        "ALLSKY_SFC_SW_DWN"
    )

    params = {
        "parameters": parameters,
        "community": "RE",
        "longitude": lon,
        "latitude": lat,
        "start": start_date,
        "end": end_date,
        "format": "JSON"
    }

    try:
        response = requests.get(
            NASA_POWER_URL,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        parameters_data = data["properties"]["parameter"]

        rainfall = parameters_data.get("PRECTOTCORR", {})
        temperature = parameters_data.get("T2M_MAX", {})
        humidity = parameters_data.get("RH2M", {})
        wind_speed = parameters_data.get("WS10M", {})
        wind_direction = parameters_data.get("WD10M", {})
        pressure = parameters_data.get("PS", {})
        solar = parameters_data.get("ALLSKY_SFC_SW_DWN", {})

        rows = []

        for date_key in rainfall.keys():

            rows.append({
                "date": pd.to_datetime(date_key),
                "rainfall": rainfall.get(date_key, 0),
                "temperature": temperature.get(date_key, 0),
                "humidity": humidity.get(date_key, 0),
                "wind_speed": wind_speed.get(date_key, 0),
                "wind_direction": wind_direction.get(date_key, 0),
                "pressure": pressure.get(date_key, 0),
                "solar_radiation": solar.get(date_key, 0)
            })

        df = pd.DataFrame(rows)

        if df.empty:
            return None, "NASA POWER returned no data."

        return df.sort_values("date").reset_index(drop=True), None

    except requests.exceptions.RequestException as e:

        return None, f"NASA POWER connection error: {e}"

    except Exception as e:

        return None, f"Data processing error: {e}"


# ============================================================
# HISTORICAL BASELINE
# ============================================================

def calculate_baseline(df):

    if df is None or df.empty:
        return 0.0

    rainfall_values = pd.to_numeric(
        df["rainfall"],
        errors="coerce"
    ).dropna()

    if rainfall_values.empty:
        return 0.0

    return float(rainfall_values.mean())


# ============================================================
# RECENT RAINFALL
# ============================================================

def calculate_recent_rainfall(df, days=3):

    if df is None or df.empty:
        return 0.0

    recent = df.tail(days)

    return float(recent["rainfall"].sum())


# ============================================================
# ANOMALY DETECTION
# ============================================================

def calculate_anomaly(current_rainfall, baseline):

    if baseline <= 0:
        return 1.0

    return current_rainfall / baseline


# ============================================================
# GPM / IMERG DEMO LAYER
# ============================================================

def get_satellite_signal(enabled):

    if not enabled:
        return None

    # IMPORTANT:
    # This is a DEMONSTRATION value.
    # It is NOT real-time GPM/IMERG data.

    return 28.5


# ============================================================
# MULTI-FACTOR RISK ENGINE
# ============================================================

def evaluate_risk(
    current_rainfall,
    baseline,
    recent_rainfall,
    humidity,
    wind_speed,
    satellite_rain
):

    score = 0
    reasons = []

    # --------------------------------------------------------
    # Rainfall anomaly
    # --------------------------------------------------------

    anomaly_ratio = calculate_anomaly(
        current_rainfall,
        baseline
    )

    if anomaly_ratio >= 3:

        score += 3

        reasons.append(
            f"Rainfall is approximately "
            f"{anomaly_ratio:.1f}× the historical baseline."
        )

    elif anomaly_ratio >= 1.5:

        score += 1

        reasons.append(
            f"Rainfall is elevated at "
            f"{anomaly_ratio:.1f}× the historical baseline."
        )

    # --------------------------------------------------------
    # Recent rainfall
    # --------------------------------------------------------

    if recent_rainfall >= 60:

        score += 2

        reasons.append(
            f"Recent rainfall accumulation is elevated "
            f"({recent_rainfall:.1f} mm over the analysis window)."
        )

    elif recent_rainfall >= 30:

        score += 1

        reasons.append(
            f"Recent rainfall accumulation is moderate "
            f"({recent_rainfall:.1f} mm)."
        )

    # --------------------------------------------------------
    # Humidity
    # --------------------------------------------------------

    if humidity >= 85:

        score += 1

        reasons.append(
            f"High atmospheric humidity detected "
            f"({humidity:.1f}%)."
        )

    # --------------------------------------------------------
    # Wind
    # --------------------------------------------------------

    if wind_speed >= 5:

        score += 2

        reasons.append(
            f"Elevated wind speed detected "
            f"({wind_speed:.1f} m/s)."
        )

    # --------------------------------------------------------
    # Satellite corroboration
    # --------------------------------------------------------

    if satellite_rain is not None:

        difference = abs(
            satellite_rain - current_rainfall
        )

        if difference <= max(5, current_rainfall * 0.30):

            score += 1

            reasons.append(
                "Satellite rainfall signal broadly "
                "corroborates the location-based observation."
            )

    # --------------------------------------------------------
    # Risk level
    # --------------------------------------------------------

    if score >= 7:

        level = "VERY HIGH"

    elif score >= 5:

        level = "HIGH"

    elif score >= 3:

        level = "WATCH"

    else:

        level = "LOW"

    return {
        "score": score,
        "level": level,
        "anomaly_ratio": anomaly_ratio,
        "reasons": reasons
    }


# ============================================================
# HEADER
# ============================================================

st.title("🌍 TerraSignal V2")

st.caption(
    "NASA Earth observations → anomaly detection → "
    "explainable environmental risk assessment"
)

st.info(
    "Prototype only: risk thresholds and weights are experimental "
    "and require historical validation before real-world warning use."
)

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("⚙️ TerraSignal Controls")

selected_location = st.sidebar.selectbox(
    "Location",
    list(LOCATIONS.keys())
)

lat, lon = LOCATIONS[selected_location]

st.sidebar.write(
    f"**Coordinates:** {lat:.4f}, {lon:.4f}"
)

observation_date = st.sidebar.date_input(
    "Observation Date",
    datetime(2025, 9, 21)
)

analysis_days = st.sidebar.slider(
    "Historical baseline period (days)",
    min_value=7,
    max_value=60,
    value=30
)

enable_satellite = st.sidebar.checkbox(
    "Enable satellite rainfall demo layer",
    value=True
)

# ============================================================
# DATE RANGE
# ============================================================

end_date = observation_date

baseline_start = observation_date - timedelta(
    days=analysis_days
)

# We request the baseline period + observation day.

start_str = baseline_start.strftime("%Y%m%d")
end_str = end_date.strftime("%Y%m%d")

# ============================================================
# DATA FETCH
# ============================================================

with st.spinner("Fetching NASA POWER observations..."):

    df, error = get_nasa_power_data(
        lat,
        lon,
        start_str,
        end_str
    )

# ============================================================
# ERROR HANDLING
# ============================================================

if error:

    st.error("Unable to retrieve NASA POWER data.")

    st.code(error)

    st.warning(
        "Try another observation date or check the network connection."
    )

    st.stop()

# ============================================================
# FIND OBSERVATION DAY
# ============================================================

target_row = df[
    df["date"] == pd.to_datetime(observation_date)
]

if target_row.empty:

    st.warning(
        "NASA POWER does not currently contain an observation "
        "for the selected date."
    )

    st.write(
        "Available dates:"
    )

    st.write(
        f"{df['date'].min().date()} → "
        f"{df['date'].max().date()}"
    )

    st.stop()

current = target_row.iloc[0]

# ============================================================
# HISTORICAL BASELINE
# ============================================================

# Exclude today's observation when calculating the baseline.

historical_df = df[
    df["date"] < pd.to_datetime(observation_date)
]

baseline = calculate_baseline(historical_df)

recent_rainfall = calculate_recent_rainfall(
    historical_df,
    days=min(3, len(historical_df))
)

# ============================================================
# CURRENT DATA
# ============================================================

current_rainfall = float(current["rainfall"])
current_temperature = float(current["temperature"])
current_humidity = float(current["humidity"])
current_wind = float(current["wind_speed"])
current_wind_direction = float(current["wind_direction"])
current_pressure = float(current["pressure"])
current_solar = float(current["solar_radiation"])

# ============================================================
# SATELLITE SIGNAL
# ============================================================

satellite_rain = get_satellite_signal(
    enable_satellite
)

# ============================================================
# RISK ENGINE
# ============================================================

risk = evaluate_risk(
    current_rainfall=current_rainfall,
    baseline=baseline,
    recent_rainfall=recent_rainfall,
    humidity=current_humidity,
    wind_speed=current_wind,
    satellite_rain=satellite_rain
)

# ============================================================
# TOP METRICS
# ============================================================

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "📍 Location",
    selected_location
)

col2.metric(
    "🌧️ Rainfall",
    f"{current_rainfall:.2f} mm"
)

col3.metric(
    "📚 Historical Baseline",
    f"{baseline:.2f} mm"
)

col4.metric(
    "📊 Anomaly",
    f"{risk['anomaly_ratio']:.2f}×"
)

st.divider()

# ============================================================
# RISK + WHY
# ============================================================

left, right = st.columns([1, 1])

with left:

    st.subheader("🧠 Explainable Risk Engine")

    if risk["level"] == "VERY HIGH":

        st.error(
            f"🚨 VERY HIGH RISK — Score {risk['score']}"
        )

    elif risk["level"] == "HIGH":

        st.error(
            f"🔴 HIGH RISK — Score {risk['score']}"
        )

    elif risk["level"] == "WATCH":

        st.warning(
            f"🟠 WATCH — Score {risk['score']}"
        )

    else:

        st.success(
            f"🟢 LOW RISK — Score {risk['score']}"
        )

    st.subheader("❓ WHY?")

    if risk["reasons"]:

        for reason in risk["reasons"]:

            st.write(
                f"• {reason}"
            )

    else:

        st.write(
            "• No elevated indicators were detected "
            "by the prototype rules."
        )

    st.caption(
        "Risk score is an experimental prototype metric, "
        "not an official warning."
    )

# ============================================================
# LOCAL WARNING
# ============================================================

with right:

    st.subheader("🇱🇰 Local Warning")

    sinhala_message = (
        f"{selected_location} ප්‍රදේශයේ පාරිසරික "
        f"සංඥා පිළිබඳ අවධානය යොමු කරන්න. "
        f"වර්ෂාපතනය ඓතිහාසික සාමාන්‍යයට "
        f"{risk['anomaly_ratio']:.1f} ගුණයක් පමණ වේ."
    )

    english_message = (
        f"Environmental conditions in {selected_location} "
        f"should be monitored. Rainfall is approximately "
        f"{risk['anomaly_ratio']:.1f}× the historical baseline."
    )

    st.info(
        f"**Sinhala**\n\n{sinhala_message}"
    )

    st.info(
        f"**English**\n\n{english_message}"
    )

# ============================================================
# NASA EVIDENCE PANEL
# ============================================================

st.divider()

st.subheader("🛰️ NASA Evidence Panel")

evidence_col1, evidence_col2 = st.columns(2)

with evidence_col1:

    st.markdown("### NASA POWER Observation")

    st.json({
        "Observation Date": observation_date.strftime("%Y-%m-%d"),
        "Latitude": lat,
        "Longitude": lon,
        "Rainfall (mm)": round(current_rainfall, 2),
        "Maximum Temperature (°C)": round(current_temperature, 2),
        "Relative Humidity (%)": round(current_humidity, 2),
        "Wind Speed (m/s)": round(current_wind, 2),
        "Wind Direction (°)": round(current_wind_direction, 2),
        "Surface Pressure (kPa)": round(current_pressure, 2),
        "Solar Radiation": round(current_solar, 2)
    })

with evidence_col2:

    st.markdown("### 🌧️ Satellite Layer")

    if satellite_rain is not None:

        st.success(
            "Satellite rainfall demonstration signal available."
        )

        st.metric(
            "Satellite Rainfall",
            f"{satellite_rain:.2f} mm"
        )

        st.caption(
            "⚠️ Current V2 demo uses a simulated satellite "
            "signal. This is not live GPM/IMERG data."
        )

    else:

        st.warning(
            "Satellite layer unavailable. "
            "NASA POWER continues as the primary data source."
        )

# ============================================================
# RAINFALL GRAPH
# ============================================================

st.divider()

st.subheader("📈 Rainfall vs Historical Baseline")

chart_df = df[
    ["date", "rainfall"]
].copy()

chart_df = chart_df.rename(
    columns={
        "rainfall": "Rainfall (mm)"
    }
)

st.line_chart(
    chart_df.set_index("date")
)

st.caption(
    "NASA POWER rainfall observations for the selected "
    "historical analysis window."
)

# ============================================================
# BASELINE COMPARISON
# ============================================================

st.subheader("📊 Current Observation vs Baseline")

comparison = pd.DataFrame(
    {
        "Rainfall (mm)": [
            baseline,
            current_rainfall
        ]
    },
    index=[
        "Historical Baseline",
        "Observation"
    ]
)

st.bar_chart(comparison)

# ============================================================
# SMS DEMO
# ============================================================

st.divider()

st.subheader("📱 Basic Phone / SMS Demo")

sms_message = (
    "TERRASIGNAL\n"
    f"{risk['level']} - {selected_location}\n"
    f"Rainfall: {current_rainfall:.1f} mm\n"
    f"Baseline anomaly: {risk['anomaly_ratio']:.1f}x\n"
    "Monitor official safety instructions."
)

st.code(
    sms_message,
    language="text"
)

st.caption(
    "Communication pathway demonstration only. "
    "This prototype does not send real SMS messages."
)

# ============================================================
# TECHNICAL TRANSPARENCY
# ============================================================

with st.expander("🔬 Technical Method"):

    st.markdown(
        """
        **TerraSignal V2 prototype pipeline**

        1. NASA POWER environmental observations
        2. Historical rainfall baseline calculation
        3. Rainfall anomaly calculation
        4. Recent rainfall accumulation
        5. Multi-factor experimental risk scoring
        6. Explainable WHY output
        7. Sinhala + English warning generation
        8. Basic-phone SMS payload demonstration

        **Important:** The risk weights and thresholds are experimental.
        Historical validation is required before any operational use.
        """
    )

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "TerraSignal V2 — Earth Intelligence. Human Reach."
)
