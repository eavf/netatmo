-- Tabuľka pre základné údaje o staniciach
CREATE TABLE IF NOT EXISTS weather_station (
    station_id VARCHAR(50) PRIMARY KEY,       -- Unikátne ID stanice
    station_name VARCHAR(255),
    date_setup DATETIME,
    last_setup DATETIME,
    type VARCHAR(50),
    module_name VARCHAR(255),
    firmware INT,
    last_upgrade DATETIME,
    wifi_status INT,
    reachable BOOLEAN,
    co2_calibrating BOOLEAN,
    place JSON,
    home_id VARCHAR(50),
    home_name VARCHAR(255),
    user_mail VARCHAR(255),
    user_administrative JSON,
    INDEX (station_id)                        -- Index na zrýchlenie vyhľadávania podľa ID stanice
);

-- Tabuľka pre údaje o moduloch pre každú stanicu (stále platné údaje)
CREATE TABLE IF NOT EXISTS weather_station_modules (
    module_id VARCHAR(50) PRIMARY KEY,       -- Unikátne ID pre každý modul
    station_id VARCHAR(50) NOT NULL,         -- Prepojenie na tabuľku staníc pomocou station_id
    type VARCHAR(50),
    data_type JSON,
    reachable BOOLEAN,
    firmware VARCHAR(50),
    last_message VARCHAR(255),
    last_seen VARCHAR(255),
    FOREIGN KEY (station_id) REFERENCES weather_station(station_id) ON DELETE CASCADE
);

-- Tabuľka pre merania z úrovne stanice aj modulov, s vlastnými časovými pečiatkami pre každú hodnotu
CREATE TABLE IF NOT EXISTS measurements (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,   -- Primárny kľúč pre každý záznam merania
    station_id VARCHAR(50) NOT NULL,                 -- Prepojenie na stanicu
    pressure FLOAT,
    time_utc_pressure DATETIME,                           -- Unix čas pre meranie tlaku
    absolute_pressure FLOAT,
    time_utc_absolute_pressure DATETIME,                  -- Unix čas pre absolútny tlak
    temperature FLOAT,
    time_utc_temperature DATETIME,                        -- Unix čas pre teplotu
    humidity INT,
    time_utc_humidity DATETIME,                           -- Unix čas pre vlhkosť
    noise INT,
    time_utc_noise DATETIME,                              -- Unix čas pre hluk
    min_temp FLOAT,
    time_utc_min_temp DATETIME,                           -- Unix čas pre minimálnu teplotu
    max_temp FLOAT,
    time_utc_max_temp DATETIME,                           -- Unix čas pre maximálnu teplotu
    rain FLOAT,
    time_utc_rain DATETIME,                               -- Unix čas pre dážď
    sum_rain_1 FLOAT,
    time_utc_sum_rain_1 DATETIME,                         -- Unix čas pre dážď za poslednú hodinu
    sum_rain_24 FLOAT,
    time_utc_sum_rain_24 DATETIME,                        -- Unix čas pre dážď za posledných 24 hodín
    wind_strength INT,
    time_utc_wind_strength DATETIME,                      -- Unix čas pre silu vetra
    wind_angle INT,
    time_utc_wind_angle DATETIME,                         -- Unix čas pre smer vetra
    gust_strength INT,
    time_utc_gust_strength DATETIME,                      -- Unix čas pre silu nárazu vetra
    gust_angle INT,                                  -- Unix čas pre smer nárazu vetra
    time_utc_gust_angle DATETIME,
    FOREIGN KEY (station_id) REFERENCES weather_station(station_id) ON DELETE CASCADE
);
