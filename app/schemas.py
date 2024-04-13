from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from app.models import GeoLocation, HourlyWeatherForecast


class GeoLocationSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = GeoLocation


class HourlyWeatherForecastSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = HourlyWeatherForecast
