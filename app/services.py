import logging

from datetime import datetime, timedelta
from multiprocessing import Pool
from sqlalchemy import inspect, func, null
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import sessionmaker

from app import db
from app.adapters import TomorrowAdapter
from app.models import GeoLocation, HourlyWeatherForecast


class GeoLocationService:
    def get_all_geolocations(self):
        return GeoLocation.query.all()


class WeatherService:
    def get_available_metrics(self):
        inspector = inspect(db.engine)
        columns = inspector.get_columns(HourlyWeatherForecast.__tablename__)
        return [column['name'] for column in columns]

    def get_most_recent_metric_for_location(self, latitude, longitude, metric):
        logging.debug(f'Getting most recent {metric} for ({latitude},{longitude})')
        current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        logging.debug(f'Current timestamp: {current_timestamp}')

        # Query the database to find the record with the closest timestamp to the current timestamp
        # for the given latitude and longitude, without exceeding the current time
        most_recent_record = HourlyWeatherForecast.query \
            .with_entities(getattr(HourlyWeatherForecast, metric)) \
            .filter_by(latitude=latitude, longitude=longitude) \
            .filter(HourlyWeatherForecast.timestamp <= current_timestamp) \
            .order_by(HourlyWeatherForecast.timestamp.desc(), HourlyWeatherForecast.id.desc()) \
            .first()

        if most_recent_record:
            logging.debug(f'Found record')
            metric_value = most_recent_record[0]  # Access the first column value
            logging.debug(f'{metric} value: {metric_value}')
            return metric_value
        else:
            logging.debug(f'Could not find record that matches')
            return None

    def get_hourly_timeseries_metric_for_location(self, latitude, longitude, metric):
        # Calculate start and end timestamps
        current_time = datetime.utcnow()
        start_time = (current_time - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")  # From a day ago
        end_time = (current_time + timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")  # 5 days in the future

        # Query the database
        hourly_weather_data = HourlyWeatherForecast.query \
            .filter_by(latitude=latitude, longitude=longitude) \
            .filter(HourlyWeatherForecast.timestamp >= start_time) \
            .filter(HourlyWeatherForecast.timestamp <= end_time) \
            .order_by(HourlyWeatherForecast.timestamp) \
            .group_by(HourlyWeatherForecast.timestamp) \
            .having(HourlyWeatherForecast.id == db.func.max(HourlyWeatherForecast.id)) \
            .with_entities(HourlyWeatherForecast.timestamp, getattr(HourlyWeatherForecast, metric)) \
            .all()

        # Format the response
        response_data = [{'timestamp': row[0], 'value': row[1]} for row in hourly_weather_data]
        return response_data

    def load_hourly_forecast_data(self):
        geolocation_service = GeoLocationService()
        geolocations = geolocation_service.get_all_geolocations()
        logging.debug(f'geolocations: {geolocations}')

        # TODO: I am getting rate limited when trying to make all these calls at once
        # Use multiprocessing pool to parallelize processing
        # with Pool() as pool:
        #     pool.map(self.write_forecast_data_for_geolocation, geolocations)

        # Falling back to non-optimized approach to avoid rate limit
        for geolocation in geolocations:
            self.write_forecast_data_for_geolocation(geolocation)

    def write_forecast_data_for_geolocation(self, geolocation):
        tomorrow_adapter = TomorrowAdapter()
        hourly_forecast_data = tomorrow_adapter.get_hourly_weather(geolocation.latitude, geolocation.longitude)

        Session = sessionmaker(bind=db.engine)
        session = Session()

        try:
            hourly_weather_forecasts = []
            for hourly_forecast in hourly_forecast_data:
                timestamp = hourly_forecast.get('time')
                data = hourly_forecast.get('values')

                # Build hourly weather forecast object
                hourly_weather_forecast = {
                    'timestamp': timestamp,
                    'latitude': geolocation.latitude,
                    'longitude': geolocation.longitude,
                    **data
                }
                hourly_weather_forecasts.append(HourlyWeatherForecast(**hourly_weather_forecast))

            # Bulk insert
            session.bulk_save_objects(hourly_weather_forecasts)
            session.commit()
            logging.info("Data inserted successfully.")
        except Exception as e:
            session.rollback()
            logging.error(f"An error occurred while inserting data: {e}")
        finally:
            session.close()

        """
        I was trying to get this code to work to avoid loading unnecessary data into the database.
        Right now, we are duplicating or making a lot of data stale when we fetch the hourly forecast
        for a geolocation. We only get one hours worth of new data for each scrape plus updates for any stale data.
        
        The idea would be that we insert all records all at once, and if we find a record with the same
        lat/lon/timestamp primary key, we simply update it with new values. I kept running into data truncation
        issues with the columns when trying to use this code so I abandoned it due to time constraints
        """
        # Construct the insert statement
        # stmt = insert(HourlyWeatherForecast).values(hourly_weather_forecasts)
        # stmt = stmt.prefix_with('IGNORE')  # Ignore duplicate key errors
        # stmt = stmt.on_duplicate_key_update(
        #     timestamp=stmt.inserted.timestamp,
        #     latitude=stmt.inserted.latitude,
        #     longitude=stmt.inserted.longitude,
        #     cloudBase=stmt.inserted.cloudBase,
        #     cloudCeiling=stmt.inserted.cloudCeiling,
        #     cloudCover=stmt.inserted.cloudCover,
        #     dewPoint=stmt.inserted.dewPoint,
        #     evapotranspiration=stmt.inserted.evapotranspiration,
        #     freezingRainIntensity=stmt.inserted.freezingRainIntensity,
        #     humidity=stmt.inserted.humidity,
        #     iceAccumulation=stmt.inserted.iceAccumulation,
        #     iceAccumulationLwe=stmt.inserted.iceAccumulationLwe,
        #     precipitationProbability=stmt.inserted.precipitationProbability,
        #     pressureSurfaceLevel=stmt.inserted.pressureSurfaceLevel,
        #     rainAccumulation=stmt.inserted.rainAccumulation,
        #     rainAccumulationLwe=stmt.inserted.rainAccumulationLwe,
        #     rainIntensity=stmt.inserted.rainIntensity,
        #     sleetAccumulation=stmt.inserted.sleetAccumulation,
        #     sleetAccumulationLwe=stmt.inserted.sleetAccumulationLwe,
        #     sleetIntensity=stmt.inserted.sleetIntensity,
        #     snowAccumulation=stmt.inserted.snowAccumulation,
        #     snowAccumulationLwe=stmt.inserted.snowAccumulationLwe,
        #     snowDepth=stmt.inserted.snowDepth,
        #     snowIntensity=stmt.inserted.snowIntensity,
        #     temperature=stmt.inserted.temperature,
        #     temperatureApparent=stmt.inserted.temperatureApparent,
        #     uvHealthConcern=stmt.inserted.uvHealthConcern,
        #     uvIndex=stmt.inserted.uvIndex,
        #     visibility=stmt.inserted.visibility,
        #     weatherCode=stmt.inserted.weatherCode,
        #     windDirection=stmt.inserted.windDirection,
        #     windGust=stmt.inserted.windGust,
        #     windSpeed=stmt.inserted.windSpeed,
        # )
