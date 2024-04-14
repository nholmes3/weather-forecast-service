-- Create GEO_LOCATION table
CREATE TABLE IF NOT EXISTS GEO_LOCATION (
    latitude DECIMAL(10,4) NOT NULL,
    longitude DECIMAL(10,4) NOT NULL,

    PRIMARY KEY (latitude, longitude),

    INDEX idx_lat_lon (latitude, longitude)
);

-- Insert relevant data into db
INSERT INTO GEO_LOCATION (latitude, longitude)
VALUES
    (25.8600, -97.4200),
    (25.9000, -97.5200),
    (25.9000, -97.4800),
    (25.9000, -97.4400),
    (25.9000, -97.4000),
    (25.9200, -97.3800),
    (25.9400, -97.5400),
    (25.9400, -97.5200),
    (25.9400, -97.4800),
    (25.9400, -97.4400)
ON DUPLICATE KEY UPDATE
    latitude = VALUES(latitude),
    longitude = VALUES(longitude);

-- Create HOURLY_WEATHER_FORECAST table
CREATE TABLE IF NOT EXISTS HOURLY_WEATHER_FORECAST (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp VARCHAR(255) NOT NULL,
    latitude DECIMAL(10,4) NOT NULL,
    longitude DECIMAL(10,4) NOT NULL,
    cloudBase FLOAT,
    cloudCeiling FLOAT,
    cloudCover FLOAT,
    dewPoint FLOAT,
    evapotranspiration FLOAT,
    freezingRainIntensity FLOAT,
    humidity FLOAT,
    iceAccumulation FLOAT,
    iceAccumulationLwe FLOAT,
    precipitationProbability FLOAT,
    pressureSurfaceLevel FLOAT,
    rainAccumulation FLOAT,
    rainAccumulationLwe FLOAT,
    rainIntensity FLOAT,
    sleetAccumulation FLOAT,
    sleetAccumulationLwe FLOAT,
    sleetIntensity FLOAT,
    snowAccumulation FLOAT,
    snowAccumulationLwe FLOAT,
    snowDepth FLOAT,
    snowIntensity FLOAT,
    temperature FLOAT,
    temperatureApparent FLOAT,
    uvHealthConcern FLOAT,
    uvIndex FLOAT,
    visibility FLOAT,
    weatherCode INT,
    windDirection FLOAT,
    windGust FLOAT,
    windSpeed FLOAT,

    -- I was using this primary key to try to not create extra copies of forecast data in the table
    -- I had trouble getting the queries to work correctly in the time I had so I am acknowledging that there
    -- is optimization work that can be done to reduce data in the database, but I don't have time
    -- PRIMARY KEY (timestamp, latitude, longitude),

    -- Add composite index on timestamp, latitude, and longitude
    INDEX idx_lat_lon_timestamp (latitude, longitude, timestamp),

    -- Add separate indexes on latitude and longitude to improve query performance
    INDEX idx_latitude (latitude),
    INDEX idx_longitude (longitude)
);
