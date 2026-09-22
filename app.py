import streamlit as st
import requests
import matplotlib.pyplot as plt
from datetime import datetime

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="TerraSignal V2",
    page_icon="🌍",
    layout="wide"
)

# ==========================================
# 1. DATA FETCHING LAYER (NASA POWER API)
# ==========================================
@st.cache_data(ttl=3600)
def get_nasa_power_data(lat, lon, date_str):
    url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR,T2M_MAX,RH2M,WS10M,WD10M,PS,ALLSKY_SFC_SW_DWN&community=RE&longitude={lon}&latitude={lat}&start={date_str}&end={date_str}&format=JSON"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        params = data['properties']['parameter']
        
        return {
            "status": "success",
            "source": "NASA POWER",
            "date": date_str,
            "rainfall": params['PRECTOTCORR'].get(date_str, 0.0),
            "temp_max": params['T2M_MAX'].get(date_str, 0.0),
            "humidity": params['RH2M'].get(date_str, 0.0),
            "wind_speed": params['WS10M'].get(date_str, 0.0),
            "pressure": params['PS'].get(date_str, 0.0),
            "solar_rad": params['ALLSKY_SFC_SW_DWN'].get(date_str, 0.0)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==========================================
# 2. SATELLITE LAYER (GPM/IMERG FALLBACK)
# ==========================================
def get_gpm_satellite_rainfall(satellite_active):
    if satellite_active:
        return 28.5  # Simulated GPM IMERG Rainfall Signal
    return None

# ==========================================
# 3. ANOMALY & MULTI-FACTOR RISK ENGINE
# ==========================================
def evaluate_risk(power_data, satellite_rain, baseline_mm):
    if satellite_rain is not None:
        effective_rain = (power_data['rainfall'] + satellite_rain) / 2
        data_mode = "NASA POWER + GPM/IMERG (Corroborated)"
    else:
        effective_rain = power_data['rainfall']
        data_mode = "NASA POWER Ground Data (Fallback Active)"

    # Anomaly Multiplier
    anomaly_ratio = round(effective_rain / baseline_mm, 2) if baseline_mm > 0 else 1.0

    risk_score = 0
    reasons = []

    if anomaly_ratio >= 3.0:
        risk_score += 3
        reasons.append(f"Rainfall is {anomaly_ratio}x above the historical baseline.")
    elif anomaly_ratio >= 1.5:
        risk_score += 1
        reasons.append(f"Rainfall is moderately elevated ({anomaly_ratio}x baseline).")

    if power_data['humidity'] >= 80:
        risk_score += 1
        reasons.append(f"High atmospheric humidity ({power_data['humidity']}%).")

    if power_data['wind_speed'] >= 5.0:
        risk_score += 2
        reasons.append(f"Elevated wind speeds detected ({power_data['wind_speed']} m/s).")

    # Risk Level Determination
    if risk_score >= 5:
        level, color = "HIGH RISK", "red"
    elif risk_score >= 3:
        level, color = "WATCH", "orange"
    else:
        level, color = "LOW RISK", "green"

    return {
        "level": level,
        "color": color,
        "score": risk_score,
        "effective_rain": round(effective_rain, 2),
        "anomaly_ratio": anomaly_ratio,
        "mode": data_mode,
        "reasons": reasons
    }

# ==========================================
# STREAMLIT UI LAYOUT
# ==========================================
st.title("🌍 TerraSignal V2")
st.caption("Explainable NASA Earth-Observation Risk Prototype | *Earth Intelligence. Human Reach.*")

# Sidebar Controls
st.sidebar.header("⚙️ Simulation Controls")
selected_location = st.sidebar.selectbox("Location", ["Colombo", "Kandy", "Galle", "Jaffna"])
lat_lon_map = {
    "Colombo": (6.9271, 79.8612),
    "Kandy": (7.2906, 80.6337),
    "Galle": (6.0535, 80.2210),
    "Jaffna": (9.6615, 80.0255)
}
lat, lon = lat_lon_map[selected_location]

# Historical Baseline Control
baseline = st.sidebar.slider("Historical Baseline Rain (mm)", min_value=5.0, max_value=50.0, value=10.0)

# Toggle GPM Satellite API Simulation
enable_satellite = st.sidebar.checkbox("Enable GPM Satellite Layer", value=True)

# NASA Data Date Selection
test_date = st.sidebar.date_input("Observation Date", datetime(2025, 9, 21)).strftime("%Y%m%d")

# Fetch Data
with st.spinner("Fetching NASA Earth Observation Data..."):
    power_data = get_nasa_power_data(lat, lon, test_date)

if power_data.get("status") == "success":
    sat_rain = get_gpm_satellite_rainfall(enable_satellite)
    risk_res = evaluate_risk(power_data, sat_rain, baseline)

    # --- TOP METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Selected Location", selected_location)
    col2.metric("Effective Rainfall", f"{risk_res['effective_rain']} mm")
    col3.metric("Baseline Anomaly", f"{risk_res['anomaly_ratio']}x Baseline")
    col4.metric("Risk Status", risk_res['level'])

    st.divider()

    # --- MAIN CONTENT LAYOUT ---
    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.subheader("🧠 Multi-factor Risk Engine")
        
        # Risk Badge
        if risk_res['color'] == "red":
            st.error(f"🚨 **STATUS: {risk_res['level']}** (Score: {risk_res['score']})")
        elif risk_res['color'] == "orange":
            st.warning(f"⚠️ **STATUS: {risk_res['level']}** (Score: {risk_res['score']})")
        else:
            st.success(f"✅ **STATUS: {risk_res['level']}** (Score: {risk_res['score']})")

        st.markdown(f"**Data Source Mode:** `{risk_res['mode']}`")

        # WHY Section
        st.subheader("❓ WHY?")
        if risk_res['reasons']:
            for reason in risk_res['reasons']:
                st.write(f"• {reason}")
        else:
            st.write("• All environmental indicators remain within normal parameters.")

        st.divider()

        # Warnings Output
        st.subheader("🇱🇰 Local Warnings")
        st.info(f"**Sinhala:** {selected_location} ප්‍රදේශයේ පාරිසරික සංඥා ඉහළ මට්ටමක පවතී. { ' '.join(risk_res['reasons'])}")

        st.subheader("📱 Basic Phone SMS Payload (Demo)")
        st.code(
            f"TERRASIGNAL ALERT\n"
            f"Level: {risk_res['level']}\n"
            f"Location: {selected_location}\n"
            f"Key Factor: Rain {risk_res['anomaly_ratio']}x Baseline.\n"
            f"Monitor safety updates.",
            language="text"
        )

    with right_col:
        st.subheader("📊 NASA Evidence Panel")
        
        # Raw Data Display
        st.json({
            "POWER Rainfall (mm)": power_data['rainfall'],
            "GPM Satellite Rainfall (mm)": sat_rain if sat_rain else "Unavailable (Fallback Used)",
            "Temperature (°C)": power_data['temp_max'],
            "Humidity (%)": power_data['humidity'],
            "Wind Speed (m/s)": power_data['wind_speed'],
            "Surface Pressure (kPa)": power_data['pressure']
        })

        # Visual Chart (Rain vs Baseline)
        st.subheader("📈 Rain vs Historical Baseline")
        fig, ax = plt.subplots(figsize=(6, 3))
        categories = ['Historical Baseline', 'NASA POWER', 'GPM Satellite', 'Effective Signal']
        values = [baseline, power_data['rainfall'], sat_rain if sat_rain else 0, risk_res['effective_rain']]
        
        ax.bar(categories, values, color=['#7f8c8d', '#3498db', '#9b59b6', '#e74c3c' if risk_res['color']=='red' else '#2ecc71'])
        ax.set_ylabel("Rainfall (mm)")
        plt.xticks(rotation=20)
        st.pyplot(fig)

else:
    st.error("Error fetching NASA POWER data. Please check your internet connection or try another date.")
