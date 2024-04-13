from flask import abort, Blueprint, jsonify, request, Response

from app.schemas import GeoLocationSchema, HourlyWeatherForecastSchema
from app.services import GeoLocationService, WeatherService

"""
Create a blueprint for endpoints. This allows us to break endpoints out into other files and not rely on app.route.
For now, we will just include all endpoints in a single file, but this pattern sets us up for better code scalability
"""
endpoints_bp = Blueprint('endpoints', __name__)

geolocation_schema = GeoLocationSchema(many=True)
geolocation_service = GeoLocationService()


@endpoints_bp.route('/geolocations')
def get_geolocations():
    geolocations = geolocation_service.get_all_geolocations()
    result = geolocation_schema.dump(geolocations)
    return jsonify(result)


hourly_weather_forecast_schema = HourlyWeatherForecastSchema()
weather_service = WeatherService()


@endpoints_bp.route('/hourly_weather')
def get_hourly_weather():
    # Parse request parameters
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    metric = request.args.get('metric', 'temperature')  # Default to temperature

    latitude_float, longitude_float = validate_lat_lon(latitude, longitude)

    result = weather_service.get_hourly_timeseries_metric_for_location(latitude_float, longitude_float, metric)
    return jsonify(result)


@endpoints_bp.route('/latest_weather')
def get_recent_metric_for_location():
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    metric = request.args.get('metric')

    available_metrics = weather_service.get_available_metrics()

    if metric not in available_metrics:
        abort(400, 'Bad Request')

    latitude_float, longitude_float = validate_lat_lon(latitude, longitude)

    result = weather_service.get_most_recent_metric_for_location(latitude_float, longitude_float, metric)
    return jsonify({metric: result})


@endpoints_bp.route('/metrics')
def get_available_metrics():
    result = weather_service.get_available_metrics()
    return result


# provides a way to manually trigger the scrape
@endpoints_bp.route('/load')
def get_available_metrics():
    weather_service.load_hourly_forecast_data()
    return Response(status=204)


def validate_lat_lon(latitude_str: str, longitude_str: str):
    # Convert latitude and longitude strings to floats
    try:
        latitude_float = float("{:.4f}".format(float(latitude_str)))
        longitude_float = float("{:.4f}".format(float(longitude_str)))
    except ValueError:
        abort(400, 'Invalid latitude or longitude')

    return latitude_float, longitude_float
