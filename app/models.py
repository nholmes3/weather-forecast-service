from sqlalchemy import Numeric

from app import db


class GeoLocation(db.Model):
    __tablename__ = 'GEO_LOCATION'
    latitude = db.Column(Numeric(precision=10, scale=4), nullable=False, primary_key=True)
    longitude = db.Column(Numeric(precision=10, scale=4), nullable=False, primary_key=True)

    def __repr__(self):
        return f'<GeoLocation {self.latitude}, {self.longitude}>'


class HourlyWeatherForecast(db.Model):
    __tablename__ = 'HOURLY_WEATHER_FORECAST'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String, nullable=False)
    latitude = db.Column(Numeric(precision=10, scale=4), nullable=False)
    longitude = db.Column(Numeric(precision=10, scale=4), nullable=False)
    cloudBase = db.Column(Numeric(precision=10, scale=4))
    cloudCeiling = db.Column(db.String)
    cloudCover = db.Column(Numeric(precision=10, scale=4))
    dewPoint = db.Column(Numeric(precision=10, scale=4))
    evapotranspiration = db.Column(Numeric(precision=10, scale=4))
    freezingRainIntensity = db.Column(Numeric(precision=10, scale=4))
    humidity = db.Column(Numeric(precision=10, scale=4))
    iceAccumulation = db.Column(Numeric(precision=10, scale=4))
    iceAccumulationLwe = db.Column(Numeric(precision=10, scale=4))
    precipitationProbability = db.Column(Numeric(precision=10, scale=4))
    pressureSurfaceLevel = db.Column(Numeric(precision=10, scale=4))
    rainAccumulation = db.Column(Numeric(precision=10, scale=4))
    rainAccumulationLwe = db.Column(Numeric(precision=10, scale=4))
    rainIntensity = db.Column(Numeric(precision=10, scale=4))
    sleetAccumulation = db.Column(Numeric(precision=10, scale=4))
    sleetAccumulationLwe = db.Column(Numeric(precision=10, scale=4))
    sleetIntensity = db.Column(Numeric(precision=10, scale=4))
    snowAccumulation = db.Column(Numeric(precision=10, scale=4))
    snowAccumulationLwe = db.Column(Numeric(precision=10, scale=4))
    snowDepth = db.Column(Numeric(precision=10, scale=4))
    snowIntensity = db.Column(Numeric(precision=10, scale=4))
    temperature = db.Column(Numeric(precision=10, scale=4))
    temperatureApparent = db.Column(Numeric(precision=10, scale=4))
    uvHealthConcern = db.Column(Numeric(precision=10, scale=4))
    uvIndex = db.Column(Numeric(precision=10, scale=4))
    visibility = db.Column(Numeric(precision=10, scale=4))
    weatherCode = db.Column(db.Integer)
    windDirection = db.Column(Numeric(precision=10, scale=4))
    windGust = db.Column(Numeric(precision=10, scale=4))
    windSpeed = db.Column(Numeric(precision=10, scale=4))

    def __repr__(self):
        return f'<WeatherForecastHourly {self.timestamp}, {self.latitude}, {self.longitude}>'
