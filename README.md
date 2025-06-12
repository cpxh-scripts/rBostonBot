# rBostonBot


A Reddit bot that posts current MBTA delay alerts and Boston weather forecasts to the Weekly Discussion Thread on r/boston. This bot combines MBTA API data, WeatherAPI forecasts, and Reddit comment management to deliver timely, updated information every 5 minutes.

---

## Features

- **Live MBTA Delay Reporting**
  - Pulls real-time MBTA alerts and filters by severity.
- **Weather Forecast for Boston**
  - Uses WeatherAPI to provide current, next-hour, and daily weather data including AQI.
- **Smart Reddit Posting**
  - Finds the Weekly Discussion Thread sticky post and edits its own comment if it already exists, otherwise posts a new one.
- **Automatic Retry Handling**
  - Retries failed API or Reddit calls up to 100 times with delay.
- **Detailed Logging**
  - Logs events and errors to `reddit_bot.log`.

---

## Requirements

- Python 3.8+
- Reddit API credentials (via PRAW)
- MBTA API key
- WeatherAPI key
- PIP dependencies: `praw`, `requests`, `pytz`

## Setup
Create a .env or set the following values directly in your script :

client_id = "your_client_id"
client_secret = "your_client_secret"
user_agent = "you_user_agent"
username = "your_username"
password = "your_password"
api_key = "your_mbta_api_key"
weather_api_key = "your_weatherapi_key"

