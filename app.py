from flask import Flask, jsonify, Response, request, render_template_string, render_template
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests
import os
import mysql.connector
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session handling

# Database configuration
DB_CONFIG = {
    "host": "db",  # This should match the service name for MySQL in docker-compose.yml
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
    "port": 3306,  # Explicitly specify the default MySQL port
}


# Netatmo credentials and endpoints
CLIENT_ID = os.getenv("CLIENT_ID", "")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")
API_URL = os.getenv("API_URL", "https://api.netatmo.com/api/getstationsdata?get_favorites=true")
TOKEN_URL = os.getenv("TOKEN_URL", "https://api.netatmo.com/oauth2/token")

# Tokens
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
TOKEN_EXPIRY = datetime.fromtimestamp(float(os.getenv("TOKEN_EXPIRY", datetime.now().timestamp())))


@app.route("/")
def landing_page():
    """Landing page with links to all routes and connectivity status."""

    # Kontrola nastavenia ID a kľúčov
    connection_status = {
        "CLIENT_ID": CLIENT_ID is not None and CLIENT_ID != "",
        "CLIENT_SECRET": CLIENT_SECRET is not None and CLIENT_SECRET != "",
        "ACCESS_TOKEN": ACCESS_TOKEN is not None and ACCESS_TOKEN != "",
        "TOKEN_EXPIRY": TOKEN_EXPIRY > datetime.now() if TOKEN_EXPIRY else False,
    }
    all_keys_set = all(connection_status.values())

    return render_template("landing_page.html", connection_status=connection_status, all_keys_set=all_keys_set)


def ensure_env_file_exists():
    """Checks if .env file exists, creates it from .env.example if not."""
    env_file_path = ".env"
    example_env_file_path = ".env.example"

    if not os.path.exists(env_file_path):
        if os.path.exists(example_env_file_path):
            with open(example_env_file_path, 'r') as example_file:
                content = example_file.read()
            with open(env_file_path, 'w') as env_file:
                env_file.write(content)
            print(f"Created {env_file_path} from {example_env_file_path}.")
        else:
            # Create an empty .env if no example exists
            with open(env_file_path, 'w') as env_file:
                env_file.write("# Environment variables\n")
            print(f"Created an empty {env_file_path}.")


@app.route("/initialize_tokens", methods=["GET", "POST"])
def initialize_tokens():
    """Webpage to initialize or update access/refresh tokens, client ID, client secret, and API endpoints."""
    global ACCESS_TOKEN, REFRESH_TOKEN, CLIENT_ID, CLIENT_SECRET, TOKEN_EXPIRY, API_URL, TOKEN_URL

    if request.method == "POST":
        # Retrieve tokens, client credentials, and endpoints from form data
        ACCESS_TOKEN = request.form.get("access_token")
        REFRESH_TOKEN = request.form.get("refresh_token")
        CLIENT_ID = request.form.get("client_id")
        CLIENT_SECRET = request.form.get("client_secret")
        new_api_url = request.form.get("api_url")
        new_token_url = request.form.get("token_url")
        TOKEN_EXPIRY = datetime.now() + timedelta(seconds=3600)  # Set token expiry to 1 hour
        
        # Ensure .env exists before initializing tokens
        ensure_env_file_exists()

        # Update environment file with new values, only if provided
        update_env_file("ACCESS_TOKEN", ACCESS_TOKEN)
        update_env_file("REFRESH_TOKEN", REFRESH_TOKEN)
        if CLIENT_ID:
            update_env_file("CLIENT_ID", CLIENT_ID)
        if CLIENT_SECRET:
            update_env_file("CLIENT_SECRET", CLIENT_SECRET)
        if new_api_url:
            API_URL = new_api_url
            update_env_file("API_URL", API_URL)
        if new_token_url:
            TOKEN_URL = new_token_url
            update_env_file("TOKEN_URL", TOKEN_URL)
        update_env_file("TOKEN_EXPIRY", str(TOKEN_EXPIRY.timestamp()))

        return jsonify({"message": "Tokens, client credentials, and endpoints initialized successfully."})

    # Render the HTML form template with existing values for GET requests
    return render_template("initialize_tokens.html", access_token=ACCESS_TOKEN, refresh_token=REFRESH_TOKEN,
                           client_id=CLIENT_ID, client_secret=CLIENT_SECRET, api_url=API_URL, token_url=TOKEN_URL)


def update_env_file(key, value):
    """Updates a key-value pair in the .env file."""
    env_file_path = '.env'
    new_lines = []
    key_found = False
    
    # Read .env file and update the key if it exists
    with open(env_file_path, 'r') as file:
        for line in file:
            if line.startswith(key + "="):
                new_lines.append(f"{key}={value}\n")
                key_found = True
            else:
                new_lines.append(line)
    
    # If key is not found, add it to the end
    if not key_found:
        new_lines.append(f"{key}={value}\n")
    
    # Write the updated content back to the .env file
    with open(env_file_path, 'w') as file:
        file.writelines(new_lines)


def refresh_access_token():
    """Refreshes the access token using the refresh token."""
    global ACCESS_TOKEN, REFRESH_TOKEN, TOKEN_EXPIRY
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(TOKEN_URL, data=data)
    
    if response.status_code == 200:
        tokens = response.json()
        ACCESS_TOKEN = tokens["access_token"]
        REFRESH_TOKEN = tokens.get("refresh_token", REFRESH_TOKEN)
        expires_in = tokens.get("expires_in", 3600)
        TOKEN_EXPIRY = datetime.now() + timedelta(seconds=expires_in)
        
        update_env_file("ACCESS_TOKEN", ACCESS_TOKEN)
        update_env_file("REFRESH_TOKEN", REFRESH_TOKEN)
        update_env_file("TOKEN_EXPIRY", str(TOKEN_EXPIRY.timestamp()))
    else:
        print("Failed to refresh access token:", response.json())


def extract_data(device_data):
    """Extracts station, device-level measurements, and module information from raw API data for a single device."""
    
    # Debug: Check the raw data coming in
    print("Extracting data for device:", device_data.get("_id"))
    print("Raw device dashboard data:", device_data.get("dashboard_data"))

    # Extract information specific to the station
    station_info = {
        "station_id": device_data.get("_id"),
        "station_name": device_data.get("station_name"),
        "date_setup": datetime.utcfromtimestamp(device_data.get("date_setup")).strftime('%Y-%m-%d %H:%M:%S') if device_data.get("date_setup") else None,
        "last_setup": datetime.utcfromtimestamp(device_data.get("last_setup")).strftime('%Y-%m-%d %H:%M:%S') if device_data.get("last_setup") else None,
        "type": device_data.get("type"),
        "module_name": device_data.get("module_name"),
        "firmware": device_data.get("firmware"),
        "last_upgrade": datetime.utcfromtimestamp(device_data.get("last_upgrade")).strftime('%Y-%m-%d %H:%M:%S') if device_data.get("last_upgrade") else None,
        "wifi_status": device_data.get("wifi_status"),
        "reachable": device_data.get("reachable"),
        "co2_calibrating": device_data.get("co2_calibrating"),
        "place": json.dumps(device_data.get("place")),
        "home_id": device_data.get("home_id"),
        "home_name": device_data.get("home_name"),
        "user_mail": device_data.get("user", {}).get("mail"),
        "user_administrative": json.dumps(device_data.get("user", {}).get("administrative"))
    }

    # Device-level measurement data with initialized None values
    device_measurement = {
        "station_id": device_data.get("_id"),
        "pressure": device_data.get("dashboard_data", {}).get("Pressure"),
        "time_utc_pressure": datetime.utcfromtimestamp(device_data.get("dashboard_data", {}).get("time_utc")).strftime('%Y-%m-%d %H:%M:%S') if device_data.get("dashboard_data", {}).get("time_utc") else None,
        "absolute_pressure": device_data.get("dashboard_data", {}).get("AbsolutePressure"),
        "time_utc_absolute_pressure": datetime.utcfromtimestamp(device_data.get("dashboard_data", {}).get("time_utc")).strftime('%Y-%m-%d %H:%M:%S') if device_data.get("dashboard_data", {}).get("time_utc") else None,
        "temperature": None, "time_utc_temperature": None,
        "humidity": None, "time_utc_humidity": None,
        "noise": None, "time_utc_noise": None,
        "min_temp": None, "time_utc_min_temp": None,
        "max_temp": None, "time_utc_max_temp": None,
        "rain": None, "time_utc_rain": None,
        "sum_rain_1": None, "time_utc_sum_rain_1": None,
        "sum_rain_24": None, "time_utc_sum_rain_24": None,
        "wind_strength": None, "time_utc_wind_strength": None,
        "wind_angle": None, "time_utc_wind_angle": None,
        "gust_strength": None, "time_utc_gust_strength": None,
        "gust_angle": None, "time_utc_gust_angle": None
    }

    # Extract module information for each module in the station
    modules_data = []
    for module in device_data.get("modules", []):
        module_info = {
            "module_id": module.get("_id"),
            "station_id": device_data.get("_id"),
            "type": module.get("type"),
            "data_type": json.dumps(module.get("data_type")),
            "reachable": module.get("reachable"),
            "firmware": module.get("firmware"),
            "last_message": module.get("last_message"),
            "last_seen": module.get("last_seen"),
        }
        modules_data.append(module_info)
        
        # Update device_measurement with module-specific data if available
        dashboard_data = module.get("dashboard_data", {})
        
        # Nastavte spoločný čas pre tento modul (ak existuje)
        time_utc = dashboard_data.get("time_utc")
        formatted_time = datetime.utcfromtimestamp(time_utc).strftime('%Y-%m-%d %H:%M:%S') if time_utc else None

        # Skontrolujte dostupnosť jednotlivých dát v module a nastavte ich s príslušným časom
        if "Temperature" in dashboard_data:
            device_measurement["temperature"] = dashboard_data["Temperature"]
            device_measurement["time_utc_temperature"] = formatted_time

        if "Humidity" in dashboard_data:
            device_measurement["humidity"] = dashboard_data["Humidity"]
            device_measurement["time_utc_humidity"] = formatted_time

        if "Noise" in dashboard_data:
            device_measurement["noise"] = dashboard_data["Noise"]
            device_measurement["time_utc_noise"] = formatted_time

        if "min_temp" in dashboard_data:
            device_measurement["min_temp"] = dashboard_data["min_temp"]
            device_measurement["time_utc_min_temp"] = formatted_time

        if "max_temp" in dashboard_data:
            device_measurement["max_temp"] = dashboard_data["max_temp"]
            device_measurement["time_utc_max_temp"] = formatted_time

        if "Rain" in dashboard_data:
            device_measurement["rain"] = dashboard_data["Rain"]
            device_measurement["time_utc_rain"] = formatted_time

        if "sum_rain_1" in dashboard_data:
            device_measurement["sum_rain_1"] = dashboard_data["sum_rain_1"]
            device_measurement["time_utc_sum_rain_1"] = formatted_time

        if "sum_rain_24" in dashboard_data:
            device_measurement["sum_rain_24"] = dashboard_data["sum_rain_24"]
            device_measurement["time_utc_sum_rain_24"] = formatted_time

        if "WindStrength" in dashboard_data:
            device_measurement["wind_strength"] = dashboard_data["WindStrength"]
            device_measurement["time_utc_wind_strength"] = formatted_time

        if "WindAngle" in dashboard_data:
            device_measurement["wind_angle"] = dashboard_data["WindAngle"]
            device_measurement["time_utc_wind_angle"] = formatted_time

        if "GustStrength" in dashboard_data:
            device_measurement["gust_strength"] = dashboard_data["GustStrength"]
            device_measurement["time_utc_gust_strength"] = formatted_time

        if "GustAngle" in dashboard_data:
            device_measurement["gust_angle"] = dashboard_data["GustAngle"]
            device_measurement["time_utc_gust_angle"] = formatted_time

    
    return station_info, device_measurement, modules_data


@app.route("/get_data", methods=["GET"])
def get_data():
    """Fetches weather data from Netatmo API and returns it as JSON."""
    if datetime.now() >= TOKEN_EXPIRY:
        refresh_access_token()

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "accept": "application/json"
    }
    response = requests.get(API_URL, headers=headers)
    
    if response.status_code != 200:
        return jsonify({"error": "API request failed", "details": response.json()}), response.status_code
    
    data = response.json()
    #print("Raw API Response:", json.dumps(data, indent=2))  # Debugging line to inspect the raw data

    # Initialize a dictionary to hold all data organized by station_id
    combined_data = {}

    # Loop through each device and extract data
    for device in data.get("body", {}).get("devices", []):
        station_info, device_measurement, modules_data = extract_data(device)
        station_id = station_info["station_id"]

        # Initialize or update the station entry in combined_data
        if station_id not in combined_data:
            combined_data[station_id] = {
                "station_info": station_info,
                "device_measurements": [],
                "modules_data": []
            }

        # Append device measurement and modules data to the respective station entry
        combined_data[station_id]["device_measurements"].append(device_measurement)
        combined_data[station_id]["modules_data"].extend(modules_data)

    # Return the combined data, organized by station_id
    return Response(json.dumps(combined_data, indent=2), mimetype='application/json')


@app.route("/store_data", methods=["GET"])
def store_data():
    """Fetches, organizes, and stores weather data from Netatmo API into the database."""
    if datetime.now() >= TOKEN_EXPIRY:
        refresh_access_token()

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "accept": "application/json"
    }
    response = requests.get(API_URL, headers=headers)

    if response.status_code != 200:
        return jsonify({"error": "API request failed", "details": response.json()}), response.status_code

    data = response.json()

    for device in data.get("body", {}).get("devices", []):
        station_info, device_measurement, modules_data = extract_data(device)
        
        # Insert into the database
        store_data_in_db(station_info, device_measurement, modules_data)

    return jsonify({"message": "Data successfully stored in the database."})


def store_data_in_db(station_info, measurement_data, modules_data):
    """Stores station data in the weather_station table, module data in weather_station_modules, and measurement data in measurements table."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Insert or update station data
    weather_station_query = """
    INSERT INTO weather_station (station_id, station_name, date_setup, last_setup, type, module_name, firmware,
                                 last_upgrade, wifi_status, reachable, co2_calibrating, place, home_id, home_name,
                                 user_mail, user_administrative)
    VALUES (%(station_id)s, %(station_name)s, %(date_setup)s, %(last_setup)s, %(type)s, %(module_name)s, %(firmware)s,
            %(last_upgrade)s, %(wifi_status)s, %(reachable)s, %(co2_calibrating)s, %(place)s, %(home_id)s,
            %(home_name)s, %(user_mail)s, %(user_administrative)s)
    ON DUPLICATE KEY UPDATE 
        station_name=VALUES(station_name), date_setup=VALUES(date_setup), last_setup=VALUES(last_setup),
        type=VALUES(type), module_name=VALUES(module_name), firmware=VALUES(firmware), last_upgrade=VALUES(last_upgrade),
        wifi_status=VALUES(wifi_status), reachable=VALUES(reachable), co2_calibrating=VALUES(co2_calibrating),
        place=VALUES(place), home_id=VALUES(home_id), home_name=VALUES(home_name),
        user_mail=VALUES(user_mail), user_administrative=VALUES(user_administrative)
    """
    
    cursor.execute(weather_station_query, station_info)
    
    # Insert measurement data
    measurement_query = """
    INSERT INTO measurements (station_id, pressure, time_utc_pressure, absolute_pressure, time_utc_absolute_pressure,
                              temperature, time_utc_temperature, humidity, time_utc_humidity, noise, time_utc_noise,
                              min_temp, time_utc_min_temp, max_temp, time_utc_max_temp, rain, time_utc_rain,
                              sum_rain_1, time_utc_sum_rain_1, sum_rain_24, time_utc_sum_rain_24, wind_strength,
                              time_utc_wind_strength, wind_angle, time_utc_wind_angle, gust_strength, time_utc_gust_strength,
                              gust_angle, time_utc_gust_angle)
    VALUES (%(station_id)s, %(pressure)s, %(time_utc_pressure)s, %(absolute_pressure)s, %(time_utc_absolute_pressure)s,
            %(temperature)s, %(time_utc_temperature)s, %(humidity)s, %(time_utc_humidity)s, %(noise)s, %(time_utc_noise)s,
            %(min_temp)s, %(time_utc_min_temp)s, %(max_temp)s, %(time_utc_max_temp)s, %(rain)s, %(time_utc_rain)s,
            %(sum_rain_1)s, %(time_utc_sum_rain_1)s, %(sum_rain_24)s, %(time_utc_sum_rain_24)s, %(wind_strength)s,
            %(time_utc_wind_strength)s, %(wind_angle)s, %(time_utc_wind_angle)s, %(gust_strength)s, %(time_utc_gust_strength)s,
            %(gust_angle)s, %(time_utc_gust_angle)s)
    """
    
    cursor.execute(measurement_query, measurement_data)

    # Insert module 
    module_query = """
    INSERT INTO weather_station_modules (
        module_id, station_id, type, data_type, reachable, firmware, last_message, last_seen
    ) VALUES (
        %(module_id)s, %(station_id)s, %(type)s, %(data_type)s, %(reachable)s, %(firmware)s, 
        %(last_message)s, %(last_seen)s
    ) ON DUPLICATE KEY UPDATE
        type=VALUES(type), data_type=VALUES(data_type), reachable=VALUES(reachable), firmware=VALUES(firmware),
        last_message=VALUES(last_message), last_seen=VALUES(last_seen)
    """
    for module in modules_data:
        cursor.execute(module_query, module)

    conn.commit()
    cursor.close()
    conn.close()


@app.route("/show_data", methods=["GET"])
def show_data():
    """Fetches all records from the weather_station table with related modules and displays them in structured JSON."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    # Query for main weather station data
    cursor.execute("SELECT * FROM weather_station")
    weather_data = cursor.fetchall()

    # Query for related modules data
    cursor.execute("SELECT * FROM weather_station_modules")
    modules_data = cursor.fetchall()

    # Close connection
    cursor.close()
    conn.close()

    # Organize modules by station_id for easy association
    modules_by_station = {}
    for module in modules_data:
        station_id = module["station_id"]
        if station_id not in modules_by_station:
            modules_by_station[station_id] = []
        modules_by_station[station_id].append(module)

    # Add modules to their respective weather stations
    for station in weather_data:
        station_id = station["station_id"]
        station["modules"] = modules_by_station.get(station_id, [])

    return jsonify(weather_data)


@app.route("/show_data_table", methods=["GET"])
def show_data_table():
    """Fetches all records from the weather_station, weather_station_modules, and measurements tables,
    and displays them in an HTML table."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    # Query for main weather station data
    cursor.execute("SELECT * FROM weather_station")
    weather_data = cursor.fetchall()

    # Query for related modules data, linked by station_id
    cursor.execute("SELECT * FROM weather_station_modules")
    modules_data = cursor.fetchall()

    # Query for measurements data, linked by station_id
    cursor.execute("SELECT * FROM measurements")
    measurements_data = cursor.fetchall()

    cursor.close()
    conn.close()

    # Organize modules and measurements by station_id
    modules_by_station = {}
    measurements_by_station = {}

    for module in modules_data:
        station_id = module["station_id"]
        if station_id not in modules_by_station:
            modules_by_station[station_id] = []
        modules_by_station[station_id].append(module)

    for measurement in measurements_data:
        station_id = measurement["station_id"]
        if station_id not in measurements_by_station:
            measurements_by_station[station_id] = []
        measurements_by_station[station_id].append(measurement)

    return render_template(
        "show_data_table1.html",
        weather_data=weather_data,
        modules_by_station=modules_by_station,
        measurements_by_station=measurements_by_station
    )



@app.route("/show_all_measurements", methods=["GET"])
def show_all_measurements():
    """Fetches all records from the measurements table and displays them in an HTML table."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    # Query for measurements data
    cursor.execute("SELECT * FROM measurements")
    measurements_data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("show_all_measurements.html", measurements_data=measurements_data)


# Scheduler setup for periodic data storage
scheduler = BackgroundScheduler()

def scheduled_store_data():
    with app.app_context():
        store_data()

scheduler.add_job(scheduled_store_data, 'interval', minutes=15)
scheduler.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
