from datetime import datetime

from app import scheduler
from app.services import WeatherService


# this doesn't trigger the job on startup. Only sets trigger for 3600s in future
@scheduler.task('interval', id='hourly_weather_scrape', seconds=3600)
def weather_scrape_hourly():
    with scheduler.app.app_context():
        print("Executing weather scrape...")
        weather_service = WeatherService()
        weather_service.load_hourly_forecast_data()
        weather_service.cleanup_stale_records()


# Define task to run at startup also
@scheduler.task('date', id='startup_weather_scrape', run_date=datetime.now())
def weather_scrape_on_startup():
    with scheduler.app.app_context():
        print("Executing weather scrape...")
        weather_service = WeatherService()
        weather_service.load_hourly_forecast_data()
        weather_service.cleanup_stale_records()
