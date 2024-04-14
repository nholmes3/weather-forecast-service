# weather-forecast-service
A very lightweight service that provides queryable weather forecast data for given geolocations

## Requirements

Make sure you have the following prerequisites installed:

- [Docker](https://docs.docker.com/get-docker/)
- Python (3.9)

## How to Run
The application can be run by simply bringing up docker compose. Include the `--build` parameter if you ever need to rebuild the image
```sh
cd weather-forecast-service
docker compose up --build
```

## Jupyter Notebook
This project includes a jupyter notebook that can be used to visualize different weather metrics for the geolocations
```bash
cd weather-forecast-service/notebook
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-notebook.txt
jupyter notebook
```
Once you have launched the jupyter notebook, you should be able to just run all the cells sequentially to visualize results

## Accessing the API
When you bring up the docker compose services, the flask app will make the API available at `http://localhost:8000`
## Endpoints

### 1. Get Geolocations

Retrieves all geolocations stored in the system.

**Endpoint:** `GET /geolocations`

**cURL Command:**
```bash
curl http://localhost:8000/geolocations
```

### 2. Get Hourly Weather Forecast

Retrieves hourly timeseries weather forecast data for a specific location and metric.

**Endpoint:** `GET /hourly_weather`

**Parameters:**
- `latitude`: Latitude of the location
- `longitude`: Longitude of the location
- `metric` (optional): Desired weather metric (default: temperature)

**cURL Command:**
```bash
curl http://localhost:8000/hourly_weather?latitude=<latitude>&longitude=<longitude>&metric=<metric>
```

### 3. Get Latest Weather Metric for Location

Retrieves the most recent value of a specific weather metric for a given location.

**Endpoint:** `GET /latest_weather`

**Parameters:**
- `latitude`: Latitude of the location
- `longitude`: Longitude of the location
- `metric`: Desired weather metric

**cURL Command:**
```bash
curl http://localhost:8000/latest_weather?latitude=<latitude>&longitude=<longitude>&metric=<metric>
```

### 4. Get Available Metrics

Retrieves the list of available weather metrics.

**Endpoint:** `GET /metrics`

**cURL Command:**
```bash
curl http://localhost:8000/metrics
```

### 5. Load Weather Data

Manually triggers the scraping of weather data.

**Endpoint:** `POST /load`

**cURL Command:**
```bash
curl -X POST http://localhost:8000/load
```

# Tech Stack
### Application Layer
I chose to use Flask as my python framework as this project is very lightweight. I didn't want to get bogged down in additional weight and complexity that comes with Django for such a simple project. 
Django might be more suitable for a larger scale, production ready application

### Data Layer
I chose to use MySQL for the database because it is simple to work with and met all the project requirements for a SQL Database

### Tasks
I chose to use Flask-APScheduler to runs tasks within the same flask process because this is a lightweight application that doesn't require overly intensive data processing or CPU requirements.

If the task required more resources, we could break out and use a more advanced distributed task queue framework like Celery. Or simply define scheduled serverless processes in the cloud to handle our needs

### Code Organization
I chose to break up my code based on functionality. I put all models in models.py, all tasks in tasks.py etc. However, as the project scales we would probably break code out into more packages to create more organization of functionality

# Areas of Improvement
### MultiProcessing
During the data load, I tried to create a pool so that we could get forecast data for geolocations in parallel, but I got rate limited by the API while doing this. However, I just wanted to point out that this was possible and should improve overall performance for the data load job

### Typing
If I had more time, and especially if this were a larger project, I would have paid more attention to adding typing throughout the code to improve readability and development experience

### Caching
I did not implement a caching layer. As the system scales, we might introduce caching to improve API performance

### Data Load
I tried to describe this in comments throughout the code as well, but basically the data load process creates a lot of duplicate records for the same timestamp/lat/lon combination when we fetch new
hourly forecast data. I tried to implement a sql query that would simply update any conflicting records instead of having to add new ones.
I couldn't get the SQL queries to work as expected in the time I had to dedicate to this project, so instead of tinkering with it more I simply
added a step in the data load process to clean up any stale records. In this way, we can ensure that our data volume doesn't grow for no reason,
and we can optimize db storage cost and performance
