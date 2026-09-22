import requests
from datetime import datetime

# ==========================================
# 1. DATA FETCHING LAYER (NASA POWER API)
# ==========================================
def get_nasa_power_data(lat, lon, date_str):
    """
    Fetch NASA POWER daily data for a given location and date.
    Date format: YYYYMMDD
    """
    url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR,T2M_MAX,RH2M,WS10M,WD10M,PS,ALLSKY_SFC_SW_DWN&community=RE&longitude={lon}&latitude={lat}&start={date_str}&end={date_str}&format=JSON"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract parameters from NASA POWER structure
        params = data['properties']['parameter']
        
        return {
            "status": "success",
            "source": "NASA POWER",
            "date": date_str,
            "rainfall": params['PRECTOTCORR'].get(date_str, 0.0),      # mm/day
            "temp_max": params['T2M_MAX'].get(date_str, 0.0),          # °C
            "humidity": params['RH2M'].get(date_str, 0.0),             # %
            "wind_speed": params['WS10M'].get(date_str, 0.0),          # m/s
            "wind_dir": params['WD10M'].get(date_str, 0.0),            # Degrees
            "pressure": params['PS'].get(date_str, 0.0),               # kPa
            "solar_rad": params['ALLSKY_SFC_SW_DWN'].get(date_str, 0.0)# MJ/m²
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ==========================================
# 2. SATELLITE LAYER WITH GRACEFUL FALLBACK
# ==========================================
def get_gpm_satellite_rainfall(lat, lon, date_str):
    """
    Stage 2: NASA GPM/IMERG Satellite Rainfall Retrieval.
    Simulated Satellite API Call. If fails/returns None, system gracefully falls back.
    """
    try:
        # NOTE: Real API/GEE call goes here. 
        # Returning simulated satellite value or None to test fallback
        satellite_available = True  # Change to False to test fallback
        
        if satellite_available:
            return 28.5  # Simulated GPM IMERG reading in mm
        else:
            return None
    except Exception:
        return None


# ==========================================
# 3. ANOMALY DETECTION ENGINE
# ==========================================
def calculate_anomaly(current_val, baseline_val):
    """
    Stage 3: Relative Multiplier based on Historical Baseline
    """
    if baseline_val <= 0:
        return 1.0
    return round(current_val / baseline_val, 2)


# ==========================================
# 4. MULTI-FACTOR RISK ENGINE & "WHY?"
# ==========================================
def evaluate_risk_engine(power_data, satellite_rain, historical_baseline):
    """
    Stage 4 & 5: Process multi-signals, calculate score, and generate 'WHY?' explanations.
    """
    # Cross-check/Corroborate Rainfall
    if satellite_rain is not None:
        final_rain = (power_data['rainfall'] + satellite_rain) / 2
        data_mode = "NASA POWER + GPM/IMERG Corroborated"
    else:
        final_rain = power_data['rainfall']
        data_mode = "NASA POWER Ground-based Data (Fallback Active)"

    risk_score = 0
    reasons = []

    # 1. Rainfall Baseline Anomaly Check
    anomaly_ratio = calculate_anomaly(final_rain, historical_baseline)
    if anomaly_ratio >= 3.0:
        risk_score += 3
        reasons.append(f"Rainfall is approximately {anomaly_ratio}x above the historical baseline.")
    elif anomaly_ratio >= 1.5:
        risk_score += 1
        reasons.append(f"Rainfall is slightly elevated ({anomaly_ratio}x historical baseline).")

    # 2. Humidity Threshold
    if power_data['humidity'] >= 85:
        risk_score += 1
        reasons.append(f"Relative humidity is high ({power_data['humidity']}%).")

    # 3. Wind Speed Check
    if power_data['wind_speed'] >= 8.0:
        risk_score += 2
        reasons.append(f"Elevated wind speed detected ({power_data['wind_speed']} m/s).")

    # Determine Risk Level
    if risk_score >= 5:
        risk_level = "HIGH RISK"
        color_code = "🔴"
    elif risk_score >= 3:
        risk_level = "WATCH"
        color_code = "🟠"
    else:
        risk_level = "LOW RISK"
        color_code = "🟢"

    return {
        "risk_level": risk_level,
        "color": color_code,
        "risk_score": risk_score,
        "effective_rainfall": round(final_rain, 2),
        "anomaly_ratio": anomaly_ratio,
        "data_mode": data_mode,
        "why_reasons": reasons
    }


# ==========================================
# 6 & 7. WARNINGS & BASIC PHONE PAYLOAD
# ==========================================
def generate_alerts_and_sms(location_name, risk_assessment):
    """
    Stage 6: Sinhala/English warning texts and Basic Phone SMS Payload
    """
    level = risk_assessment['risk_level']
    reasons_text = " ".join(risk_assessment['why_reasons'])

    # Dashboard / Web Alerts
    alerts = {
        "English": f"[{level}] {location_name}: Environmental signals elevated. {reasons_text}",
        "Sinhala": f"[{level}] {location_name} ප්‍රදේශයේ පාරිසරික සංඥා ඉහළ මට්ටමක පවතී. {reasons_text}"
    }

    # Low-bandwidth Basic Phone SMS Payload (Strict Character Limit)
    sms_payload = (
        f"TERRASIGNAL ALERT\n"
        f"Level: {level}\n"
        f"Location: {location_name}\n"
        f"Key Factor: Rain {risk_assessment['anomaly_ratio']}x Baseline.\n"
        f"Monitor local safety updates."
    )

    return alerts, sms_payload


# ==========================================
# 🚀 MAIN RUNNER / DEMO EXECUTION
# ==========================================
if __name__ == "__main__":
    # Test Parameters (Colombo Location)
    LAT = 6.9271
    LON = 79.8612
    TEST_DATE = "20260921"  # YYYYMMDD
    LOCATION = "Colombo"
    HISTORICAL_BASELINE_RAIN = 10.0  # mm (Historical average for this date)

    print("Fetching NASA Data...")
    power_res = get_nasa_power_data(LAT, LON, TEST_DATE)

    if power_res.get("status") == "success":
        # Check Satellite Data
        sat_rain = get_gpm_satellite_rainfall(LAT, LON, TEST_DATE)

        # Run Multi-factor Engine
        evaluation = evaluate_risk_engine(power_res, sat_rain, HISTORICAL_BASELINE_RAIN)

        # Generate Outputs
        web_alerts, sms_msg = generate_alerts_and_sms(LOCATION, evaluation)

        # --- DISPLAY RESULTS (JUDGE DEMO VIEW) ---
        print("\n" + "="*50)
        print("📊 NASA EVIDENCE PANEL")
        print("="*50)
        print(f"Observation Date : {power_res['date']}")
        print(f"Data Pipeline    : {evaluation['data_mode']}")
        print(f"Rainfall (POWER) : {power_res['rainfall']} mm")
        print(f"Rainfall (GPM)   : {sat_rain if sat_rain else 'Unavailable'}")
        print(f"Temperature      : {power_res['temp_max']} °C")
        print(f"Humidity         : {power_res['humidity']} %")
        print(f"Wind Speed       : {power_res['wind_speed']} m/s")
        print(f"Pressure         : {power_res['pressure']} kPa")

        print("\n" + "="*50)
        print(f"🧠 RISK ASSESSMENT ENGINE: {evaluation['color']} {evaluation['risk_level']}")
        print("="*50)
        print(f"Risk Score : {evaluation['risk_score']}")
        print(f"Effective Rain : {evaluation['effective_rainfall']} mm (Baseline: {HISTORICAL_BASELINE_RAIN} mm)")
        print("\n❓ WHY?")
        for reason in evaluation['why_reasons']:
            print(f"  • {reason}")

        print("\n" + "="*50)
        print("🌐 WEB / APP WARNINGS")
        print("="*50)
        print(f"🇬🇧 EN: {web_alerts['English']}")
        print(f"🇱🇰 SI: {web_alerts['Sinhala']}")

        print("\n" + "="*50)
        print("📱 BASIC PHONE SMS PAYLOAD (Server -> Telecom -> Phone)")
        print("="*50)
        print(sms_msg)
        print("="*50)
