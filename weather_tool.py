import requests
from datetime import datetime, timedelta

def get_bouldering_weather(lat: float, lng: float, date_str: str = None):
    """
    Evaluates climbing conditions by checking 48h rain history and future forecasts.
    
    This tool is essential for bouldering safety and quality. It specifically checks for:
    1. Seepage: Heavy rain in the last 48h makes many rock types (sandstone/limestone) 
       fragile and unclimbable even if the sun is out.
    2. Hazards: Identifies snow, hail, and thunderstorms which are dangerous for outdoor climbing.
    3. Daylight: Filters weather data to only show conditions during actual climbing hours.

    Args:
        lat (float): The latitude of the specific crag or rock.
        lng (float): The longitude of the specific crag or rock.
        date_str (str, optional): Target trip date in 'YYYY-MM-DD' format. Defaults to today.

    Returns:
        dict: A status report including 'status' (Green/Yellow/Red), 'reason', and local metrics.
    """
    
    # Calculate the 48-hour 'Lookback' period to check if the rock is currently soaked.
    now = datetime.now()
    target_date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else now
    history_end = now.date()
    history_start = history_end - timedelta(days=2)

    # Most bouldering areas require at least 24-48 hours to dry after > 0.1" of rain.
    archive_url = "https://archive-api.open-meteo.com/v1/archive"
    archive_params = {
        "latitude": lat, "longitude": lng,
        "start_date": history_start.strftime('%Y-%m-%d'),
        "end_date": history_end.strftime('%Y-%m-%d'),
        "daily": "precipitation_sum",
        "precipitation_unit": "inch",
        "timezone": "auto"
    }
    archive_res = requests.get(archive_url, params=archive_params).json()
    past_rain = sum(archive_res.get('daily', {}).get('precipitation_sum', []))

    # We fetch hourly data but filter by sunrise/sunset to ignore night-time rain.
    forecast_url = "https://api.open-meteo.com/v1/forecast"
    forecast_params = {
        "latitude": lat, "longitude": lng,
        "start_date": target_date.strftime('%Y-%m-%d'),
        "end_date": target_date.strftime('%Y-%m-%d'),
        "hourly": ["temperature_2m", "precipitation", "weather_code", "relative_humidity_2m"],
        "daily": ["sunrise", "sunset"],
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch",
        "timezone": "auto"
    }
    f_res = requests.get(forecast_url, params=forecast_params).json()
    
    # Extract daylight hours
    sunrise = datetime.fromisoformat(f_res['daily']['sunrise'][0])
    sunset = datetime.fromisoformat(f_res['daily']['sunset'][0])
    
    hourly = f_res.get('hourly', {})
    # Slice arrays to only look at hours between sunrise and sunset
    day_temps = hourly.get('temperature_2m', [])[sunrise.hour:sunset.hour]
    day_precip = sum(hourly.get('precipitation', [])[sunrise.hour:sunset.hour])
    day_codes = hourly.get('weather_code', [])[sunrise.hour:sunset.hour]
    day_humidity = hourly.get('relative_humidity_2m', [])[sunrise.hour:sunset.hour]

    max_day_temp = max(day_temps) if day_temps else 0
    min_day_temp = min(day_temps) if day_temps else 0
    max_humidity = max(day_humidity) if day_humidity else 0

    # WMO Codes 71-77: Snow | 85-86: Snow showers | 96-99: Hail/Thunderstorms
    hazard_codes = [71, 73, 75, 77, 85, 86, 96, 99]
    has_hazard = any(code in hazard_codes for code in day_codes)

    # The agent will use this 'status' to provide a quick 'Go' or 'No-Go' to the user.
    status = "Green"
    reasons = []

    if past_rain > 0.15:
        status = "Red"
        reasons.append(f"Recent Rain: {past_rain:.2f}\" in the last 48h likely caused seepage.")
    if day_precip > 0.02:
        status = "Red"
        reasons.append(f"Forecasted Precip: {day_precip:.2f}\" expected during climbing hours.")
    if has_hazard:
        status = "Red"
        reasons.append("Severe Hazard: Snow, Hail, or Storms forecasted.")
    if max_humidity > 60:
        status = "Yellow"
        reasons.append(f"High Humidity: Humidity of {max_humidity} may impact friction.")
    if max_day_temp > 80:
        status = "Yellow"
        reasons.append(f"Sub-optimal Temps: High of {max_day_temp}°F is a bit warm/greasy.")
    if min_day_temp < 32:
        status = "Yellow"
        reasons.append(f"Sub-optimal Temps: Low of {min_day_temp}°F is quite cold.")

    return {
        "status": status,
        "verdict": " | ".join(reasons) if reasons else "Prime bouldering conditions.",
        "metrics": {
            "temp_f": f"{min(day_temps)}° to {max(day_temps)}°",
            "daylight_window": f"{sunrise.strftime('%I:%M %p')} - {sunset.strftime('%I:%M %p')}",
            "historical_rain_in": round(past_rain, 2)
        }
    }