def detect_hazards(df):

    latest = df.iloc[-1]

    rain = float(latest["rainfall"])
    temperature = float(latest["temperature"])
    humidity = float(latest["humidity"])
    wind = float(latest["wind"])

    previous = df.iloc[:-1].tail(7)

    if len(previous) > 0:
        recent_rain = float(previous["rainfall"].sum())
    else:
        recent_rain = 0.0

    hazards = []

    # FLOOD / HEAVY RAIN
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
        })

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

    # EXTREME HEAT
    if temperature >= 35:

        hazards.append({
            "name": "Extreme Heat",
            "emoji": "☀️",
            "level": "HIGH",
            "reason": (
                f"උපරිම උෂ්ණත්වය "
                f"{temperature:.1f}°C පමණයි."
            )
        })

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

    # DROUGHT
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

    # LANDSLIDE INDICATOR
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

    # STORM INDICATOR
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
