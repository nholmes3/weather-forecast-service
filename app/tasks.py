from app import scheduler
from app.services import WeatherService


@scheduler.task('interval', id='hourly_weather_scrape', seconds=3600)
def weather_scrape():
    with scheduler.app.app_context():
        print("Executing weather scrape...")
        weather_service = WeatherService()
        weather_service.load_hourly_forecast_data()
