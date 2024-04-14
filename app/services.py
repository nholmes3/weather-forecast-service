import logging

from datetime import datetime, timedelta
from multiprocessing import Pool
from sqlalchemy import inspect, func, null, text
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app import db
from app.adapters import TomorrowAdapter
from app.models import GeoLocation, HourlyWeatherForecast


class GeoLocationService:
    def get_all_geolocations(self):
        return GeoLocation.query.all()


class WeatherService:
    def get_available_metrics(self):
        excluded_columns = {'timestamp', 'latitude', 'longitude', 'id'}
        inspector = inspect(db.engine)
        columns = inspector.get_columns(HourlyWeatherForecast.__tablename__)
        return [column['name'] for column in columns if column['name'] not in excluded_columns]

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
        logging.debug(f'Getting hourly {metric} data for ({latitude},{longitude})')
        # Calculate start and end timestamps
        current_time = datetime.utcnow()
        start_time = (current_time - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")  # From a day ago
        end_time = (current_time + timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")  # 5 days in the future

        # Query the database
        """
        This is not an ideal solution for querying the database. Essentially, because our data load process
        adds new forecasts data for the same timestamp,lat,lon during the scrape, we need to figure out a way to
        grab the most recent data. Since our ID increments, we know the latest data is the one with the highest id.
        We need to group records by these columns and only grab the record with the latest id.
        """
        try:
            latest_records_subquery = db.session.query(
                func.max(HourlyWeatherForecast.id).label('max_id')
            ).filter(
                HourlyWeatherForecast.latitude == latitude,
                HourlyWeatherForecast.longitude == longitude,
                HourlyWeatherForecast.timestamp >= start_time,
                HourlyWeatherForecast.timestamp <= end_time
            ).group_by(
                HourlyWeatherForecast.latitude,
                HourlyWeatherForecast.longitude,
                HourlyWeatherForecast.timestamp
            ).subquery()

            hourly_weather_data = db.session.query(
                HourlyWeatherForecast.timestamp,
                getattr(HourlyWeatherForecast, metric)
            ).filter(
                HourlyWeatherForecast.id == latest_records_subquery.c.max_id
            ).order_by(
                HourlyWeatherForecast.timestamp
            ).all()

            response_data = [{'timestamp': row[0], 'value': row[1]} for row in hourly_weather_data]
            # logging.debug(f'Hourly timeseries response data: {response_data}')
            return response_data
        except Exception as e:
            logging.error(f'An error occurred: {e}')

    def cleanup_stale_records(self):
        """
        This function cleans up stale records in the DB by identifying records that don't have the max id
        for unique combinations of timestamp, latitude, and longitude. This helps alleviate the problem that we have
        in the data load process where we create stale records
        :return:
        """
        logging.debug(f'Cleaning up stale records')
        try:
            # Subquery to get the maximum id for each unique combination of latitude, longitude, and timestamp
            max_id_subquery = db.session.query(
                func.max(HourlyWeatherForecast.id).label('max_id')
            ).group_by(
                HourlyWeatherForecast.latitude,
                HourlyWeatherForecast.longitude,
                HourlyWeatherForecast.timestamp
            ).subquery()

            # Query to delete records that do not have the highest ID
            stale_records_query = db.session.query(HourlyWeatherForecast).filter(
                ~HourlyWeatherForecast.id.in_(
                    db.session.query(max_id_subquery.c.max_id)
                )
            )

            # Execute the delete query
            num_deleted = stale_records_query.delete()
            db.session.commit()
            logging.debug(f'Successfully deleted {num_deleted} stale records.')
        except Exception as e:
            db.session.rollback()
            logging.debug(f'An error occurred while cleaning up stale records: {e}')

    def load_hourly_forecast_data(self):
        logging.debug(f'Loading weather data for all geolocations')
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

        # couldn't get this code to work in time
        # self.insert_weather_forecasts(hourly_weather_forecasts)

    """
    I was trying to get this code to work to avoid loading unnecessary data into the database.
    Right now, we are duplicating or making a lot of data stale when we fetch the hourly forecast
    for a geolocation. We only get one hours worth of new data for each scrape plus updates for any stale data.
    
    The idea would be that we insert all records all at once, and if we find a record with the same
    lat/lon/timestamp primary key, we simply update it with new values. I played with trying to do this using native
    SqlAlchemy functions, but I couldn't get it working. Tried to create the raw sql myself as well, but didn't want to
    spend more time on it.
    """
    def insert_weather_forecasts(self, hourly_weather_forecasts):
        logging.debug('Inserting weather forecasts')
        try:
            # Construct the base SQL query
            sql_query = """
                INSERT INTO HOURLY_WEATHER_FORECAST 
                    (timestamp, latitude, longitude, cloudBase, cloudCeiling, cloudCover, dewPoint, evapotranspiration,
                    freezingRainIntensity, humidity, iceAccumulation, iceAccumulationLwe, precipitationProbability,
                    pressureSurfaceLevel, rainAccumulation, rainAccumulationLwe, rainIntensity, sleetAccumulation,
                    sleetAccumulationLwe, sleetIntensity, snowAccumulation, snowAccumulationLwe, snowDepth, snowIntensity,
                    temperature, temperatureApparent, uvHealthConcern, uvIndex, visibility, weatherCode, windDirection,
                    windGust, windSpeed)
                VALUES 
            """

            # List to store parameter values
            params_values = []

            # Construct the parameterized values for each forecast
            for forecast in hourly_weather_forecasts:
                params_values.append({
                    "timestamp": forecast.timestamp,
                    "latitude": forecast.latitude,
                    "longitude": forecast.longitude,
                    "cloudBase": forecast.cloudBase,
                    "cloudCeiling": forecast.cloudCeiling,
                    "cloudCover": forecast.cloudCover,
                    "dewPoint": forecast.dewPoint,
                    "evapotranspiration": forecast.evapotranspiration,
                    "freezingRainIntensity": forecast.freezingRainIntensity,
                    "humidity": forecast.humidity,
                    "iceAccumulation": forecast.iceAccumulation,
                    "iceAccumulationLwe": forecast.iceAccumulationLwe,
                    "precipitationProbability": forecast.precipitationProbability,
                    "pressureSurfaceLevel": forecast.pressureSurfaceLevel,
                    "rainAccumulation": forecast.rainAccumulation,
                    "rainAccumulationLwe": forecast.rainAccumulationLwe,
                    "rainIntensity": forecast.rainIntensity,
                    "sleetAccumulation": forecast.sleetAccumulation,
                    "sleetAccumulationLwe": forecast.sleetAccumulationLwe,
                    "sleetIntensity": forecast.sleetIntensity,
                    "snowAccumulation": forecast.snowAccumulation,
                    "snowAccumulationLwe": forecast.snowAccumulationLwe,
                    "snowDepth": forecast.snowDepth,
                    "snowIntensity": forecast.snowIntensity,
                    "temperature": forecast.temperature,
                    "temperatureApparent": forecast.temperatureApparent,
                    "uvHealthConcern": forecast.uvHealthConcern,
                    "uvIndex": forecast.uvIndex,
                    "visibility": forecast.visibility,
                    "weatherCode": forecast.weatherCode,
                    "windDirection": forecast.windDirection,
                    "windGust": forecast.windGust,
                    "windSpeed": forecast.windSpeed
                })

            # Add placeholders for parameterized values
            placeholders = ','.join(
                ['(:timestamp{}, :latitude{}, :longitude{}, :cloudBase{}, :cloudCeiling{}, :cloudCover{}, '
                 ':dewPoint{}, :evapotranspiration{}, :freezingRainIntensity{}, :humidity{}, '
                 ':iceAccumulation{}, :iceAccumulationLwe{}, :precipitationProbability{}, '
                 ':pressureSurfaceLevel{}, :rainAccumulation{}, :rainAccumulationLwe{}, '
                 ':rainIntensity{}, :sleetAccumulation{}, :sleetAccumulationLwe{}, :sleetIntensity{}, '
                 ':snowAccumulation{}, :snowAccumulationLwe{}, :snowDepth{}, :snowIntensity{}, '
                 ':temperature{}, :temperatureApparent{}, :uvHealthConcern{}, :uvIndex{}, :visibility{}, '
                 ':weatherCode{}, :windDirection{}, :windGust{}, :windSpeed{})'.format(*[i] * 33) for i in range(len(params_values))])

            # Concatenate the base query with placeholders
            sql_query += placeholders

            # Append ON DUPLICATE KEY UPDATE clause
            sql_query += """
                ON DUPLICATE KEY UPDATE
                    cloudBase = VALUES(cloudBase),
                    cloudCeiling = VALUES(cloudCeiling),
                    cloudCover = VALUES(cloudCover),
                    dewPoint = VALUES(dewPoint),
                    evapotranspiration = VALUES(evapotranspiration),
                    freezingRainIntensity = VALUES(freezingRainIntensity),
                    humidity = VALUES(humidity),
                    iceAccumulation = VALUES(iceAccumulation),
                    iceAccumulationLwe = VALUES(iceAccumulationLwe),
                    precipitationProbability = VALUES(precipitationProbability),
                    pressureSurfaceLevel = VALUES(pressureSurfaceLevel),
                    rainAccumulation = VALUES(rainAccumulation),
                    rainAccumulationLwe = VALUES(rainAccumulationLwe),
                    rainIntensity = VALUES(rainIntensity),
                    sleetAccumulation = VALUES(sleetAccumulation),
                    sleetAccumulationLwe = VALUES(sleetAccumulationLwe),
                    sleetIntensity = VALUES(sleetIntensity),
                    snowAccumulation = VALUES(snowAccumulation),
                    snowAccumulationLwe = VALUES(snowAccumulationLwe),
                    snowDepth = VALUES(snowDepth),
                    snowIntensity = VALUES(snowIntensity),
                    temperature = VALUES(temperature),
                    temperatureApparent = VALUES(temperatureApparent),
                    uvHealthConcern = VALUES(uvHealthConcern),
                    uvIndex = VALUES(uvIndex),
                    visibility = VALUES(visibility),
                    weatherCode = VALUES(weatherCode),
                    windDirection = VALUES(windDirection),
                    windGust = VALUES(windGust),
                    windSpeed = VALUES(windSpeed)
            """

            # Execute the SQL query with parameterized values
            db.session.execute(sql_query, params_values)

            # Commit the changes to the database
            db.session.commit()

        except SQLAlchemyError as e:
            # Rollback changes in case of an error
            db.session.rollback()
            print(f"An error occurred: {e}")