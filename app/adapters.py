import logging
import json
import requests
from config import Config


"""If we had more adapters, I would create a base class to provide an abstraction for common functionality. 
BaseAdapter would contain logic for preparing headers, making the request, and error handling, while subclasses would 
provide functions to handle the unique behavior and calls for that Adapter. """


class TomorrowAdapter:
    api_key = Config.TOMORROW_API_KEY
    base_url = Config.TOMORROW_API_BASE_URL

    def get_hourly_weather(self, latitude, longitude):
        endpoint = 'weather/forecast'
        url = f'{self.base_url}/{endpoint}'
        params = {
            'location': f'{latitude},{longitude}',
            'timesteps': '1h',
            'apikey': self.api_key
        }

        # TODO: using mock response for testing so don't hit rate limit
        with open('/opt/app/app/response.json', 'r') as file:
            # Read the contents of the file
            json_data = file.read()

            # Parse the JSON data into a Python object
            data = json.loads(json_data)
        return data.get('timelines', {}).get('hourly', [])

        # TODO: uncomment real code when finished
        # response = requests.get(url, params=params)
        # logging.debug(f'Weather Forecast: {response}')
        # if response.status_code == 200:
        #     data = response.json()
        #     return data.get('timelines', {}).get('hourly', [])
        # else:
        #     # Handle error
        #     return None
