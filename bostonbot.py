# Import necessary libraries
import praw  # Python Reddit API Wrapper
import time  # For sleep/delay functionality
import requests  # To make API calls
from datetime import datetime, timedelta  # For date and time handling
import pytz  # For timezone conversions
import logging  # For logging info, warnings, and errors
import os  # For environment variable access
from dotenv import load_dotenv  # Load .env files

# Load environment variables from .env file
load_dotenv()

# Configure logging output to a file with timestamps and severity level
logging.basicConfig(
    filename="reddit_bot.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Define the max number of retries for retryable operations
max_retries = 100

# Retry wrapper for retrying operations that may intermittently fail
def retry_operation(operation, max_retries):
    for _ in range(max_retries):
        try:
            result = operation()
            return result
        except Exception as e:
            print(f"Error occurred: {e}")
            print("Retrying...")
            time.sleep(60)
    else:
        print("Max retries reached. Exiting program.")
        exit()

# Get current MBTA (Boston Transit) delay alerts
def get_mbta_delays(api_key, min_severity=1):
    base_url = "https://api-v3.mbta.com/alerts"
    params = {
        "api_key": api_key,
        "filter[route_type]": "0,1",  # Subway and Light Rail routes
        "sort": "created_at",
        "page[limit]": 10,
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data["data"]:
            mbta_delays_text = "# Current delays on the MBTA:\n\n"
            for alert in data["data"]:
                attributes = alert["attributes"]
                header = attributes.get("header")
                service_effect = attributes.get("service_effect")
                severity = attributes.get("severity")
                timeframe = attributes.get("timeframe")

                # Filter out low severity or non-impacting alerts
                if severity >= min_severity and "change" not in service_effect.lower():
                    mbta_delays_text += f"**{service_effect}** - {timeframe}\n\nCause: {header}\n\n"
            return mbta_delays_text
        else:
            return "No current delays on the MBTA."
    else:
        return "Failed to fetch data. Please try again later."

# Create a Reddit bot instance using PRAW
def create_reddit_bot(client_id, client_secret, user_agent, username, password):
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        username=username,
        password=password
    )
    return reddit

# Post the comment to the Weekly Discussion sticky thread
def post_comment_in_daily_discussion(reddit, subreddit_name, comment_text):
    try:
        subreddit = reddit.subreddit(subreddit_name)
        hot_posts = subreddit.hot(limit=10)
        suitable_sticky_found = False

        for post in hot_posts:
            if post.stickied and "Weekly Discussion Thread" in post.title:
                post.reply(comment_text)
                print(f"Comment posted successfully in {subreddit_name}: {post.title}")
                suitable_sticky_found = True
                break

        if not suitable_sticky_found:
            print(f"No suitable sticky post found in {subreddit_name}. Comment not posted.")

    except Exception as e:
        print(f"Error occurred: {e}")

# Check if the comment with a unique marker already exists in the sticky thread
def check_comment_in_stickied_thread(reddit, subreddit_name, marker):
    subreddit = reddit.subreddit(subreddit_name)
    for post in subreddit.hot(limit=None):
        if post.stickied and "Weekly Discussion Thread" in post.title:
            post.comments.replace_more(limit=None)
            for comment in post.comments.list():
                if marker in comment.body:
                    return comment
    return None

# Get daily weather forecast for Boston
def get_weather(api_key):
    base_url = "https://api.weatherapi.com/v1/forecast.json"
    current_hour = datetime.now().hour
    next_hour_time = current_hour - 3 if current_hour > 4 else current_hour

    params = {
        "key": api_key,
        "q": "Boston",
        "days": 1,
        "hour": next_hour_time,
        "unit": "imperial",
        "aqi": "yes"
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        forecast = data["forecast"]["forecastday"][0]
        
        # Extract daily forecast and air quality info
        max_temp_f = forecast["day"]["maxtemp_f"]
        min_temp_f = forecast["day"]["mintemp_f"]
        avg_temp_f = forecast["day"]["avgtemp_f"]
        condition = forecast["day"]["condition"]["text"]
        chance_of_rain = forecast["day"]["daily_chance_of_rain"]
        sunrise_time = forecast["astro"]["sunrise"]
        sunset_time = forecast["astro"]["sunset"]
        current_temp_f = data["current"]["temp_f"]
        current_feels = data["current"]["feelslike_f"]
        next_hour = forecast["hour"][0]
        next_hour_temp_f = next_hour["temp_f"]
        next_hour_condition = next_hour["condition"]["text"].strip()

        air_quality = data["current"]["air_quality"]
        aqi_us = air_quality["us-epa-index"]
        pm2_5 = air_quality["pm2_5"]
        pm10 = air_quality["pm10"]
        ozone = air_quality["o3"]
        co = air_quality["co"]
        no2 = air_quality["no2"]
        so2 = air_quality["so2"]

        aqi_categories = {
            1: "Good",
            2: "Moderate",
            3: "Unhealthy for Sensitive Groups",
            4: "Unhealthy",
            5: "Very Unhealthy",
        }
        aqi_category = aqi_categories.get(aqi_us, "Hazardous")

        # Format all weather information as Markdown text
        weather_text = "### Daily Weather Forecast for Today in Boston ###\n\n"
        weather_text += f"Current Temperature is **{current_temp_f}°F** but it feels like **{current_feels}°F**\n\n"
        weather_text += f"The next hour will be **{next_hour_temp_f}°F** and **{next_hour_condition}**\n\n"
        weather_text += f"**Daily Forecast**\n\n"
        weather_text += f"* Max Temperature: {max_temp_f}°F\n\n"
        weather_text += f"* Min Temperature: {min_temp_f}°F\n\n"
        weather_text += f"* Avg Temperature: {avg_temp_f}°F\n\n"
        weather_text += f"* Condition: {condition}\n\n"
        weather_text += f"* Chance of Rain: {chance_of_rain}%\n\n"
        weather_text += f"* Sunrise Time: {sunrise_time}\n\n"
        weather_text += f"* Sunset Time: {sunset_time}\n\n"
        weather_text += "\n### Air Quality Index (AQI) ###\n\n"
        weather_text += f"* **AQI Level:** {aqi_category} ({aqi_us}/5)\n\n"
        weather_text += f"* **PM2.5:** {pm2_5} µg/m³\n\n"
        weather_text += f"* **PM10:** {pm10} µg/m³\n\n"
        weather_text += f"* **Ozone (O3):** {ozone} µg/m³\n\n"
        weather_text += f"* **Carbon Monoxide (CO):** {co} µg/m³\n\n"
        weather_text += f"* **Nitrogen Dioxide (NO2):** {no2} µg/m³\n\n"
        weather_text += f"* **Sulfur Dioxide (SO2):** {so2} µg/m³\n\n"

        return weather_text
    else:
        return "Failed to fetch weather data. Please try again later."

# Check if a comment was removed by Reddit's Crowd Control system
def is_probably_crowd_control(item, bot_username):
    try:
        modlog = list(item.subreddit.mod.log(limit=10, action="removecomment"))
        for log_entry in modlog:
            if log_entry.target_fullname == item.fullname and log_entry.mod.name == "reddit":
                return True
    except Exception as e:
        logger.warning(f"Error checking modlog for item {item.id}: {e}")
    return False

# Monitor the moderation queue for comments affected by Crowd Control and remove them
def monitor_modqueue_for_crowd_control(reddit, subreddit_name, bot_username):
    subreddit = reddit.subreddit(subreddit_name)
    flagged_count = 0
    for item in subreddit.mod.modqueue(limit=25):
        if isinstance(item, praw.models.Comment) and is_probably_crowd_control(item, bot_username):
            logger.info(f"Marking comment {item.id} as spam due to Reddit Crowd Control.")
            item.mod.remove(spam=True)
            flagged_count += 1
    logger.info(f"Total comments flagged as spam this cycle: {flagged_count}")

# Main execution block
if __name__ == "__main__":
    # Load secrets from environment variables
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")
    username = os.getenv("REDDIT_USERNAME")
    password = os.getenv("REDDIT_PASSWORD")
    subreddit_name = os.getenv("SUBREDDIT_NAME")
    api_key = os.getenv("MBTA_API_KEY")
    weather_api_key = os.getenv("WEATHER_API_KEY")
    min_severity = 1
    marker = "### Boston Status Update ###"
    est_timezone = pytz.timezone('US/Eastern')

    # Initialize the Reddit bot
    reddit_bot = create_reddit_bot(client_id, client_secret, user_agent, username, password)

    # Run the main logic loop every 5 minutes
    while True:
        def main_logic():
            try:
                logger.info("Fetching MBTA delays...")
                mbta_delays_text = get_mbta_delays(api_key, min_severity)

                logger.info("Fetching weather forecast...")
                weather_text = get_weather(weather_api_key)

                current_time_utc = datetime.now()
                current_time_est = current_time_utc.astimezone(est_timezone)
                current_time_est_str = current_time_est.strftime("%Y-%m-%d %H:%M:%S EST")

                # Compose the full comment to be posted or updated
                comment_text = f"{marker}\n\nLast Update: {current_time_est_str}\n\n________________\n\n{weather_text}\n\n________________\n\n{mbta_delays_text}\n\n________________\n\n This comment was made by a bot. If the bot is broken please [message the mods](https://www.reddit.com/message/compose/?to=/r/boston) . "

                logger.info("Checking for existing comment...")
                existing_comment = check_comment_in_stickied_thread(reddit_bot, subreddit_name, marker)

                # Post or update comment based on existence
                if existing_comment is None:
                    logger.info("No existing comment found. Posting new comment...")
                    post_comment_in_daily_discussion(reddit_bot, subreddit_name, comment_text)
                    logger.info("Comment posted successfully.")
                else:
                    try:
                        logger.info("Editing existing comment...")
                        existing_comment.edit(comment_text)
                        logger.info("Comment edited successfully.")
                    except praw.exceptions.PRAWException as e:
                        logger.error(f"Error posting/editing comment: {e}")

                # Clean up comments removed by Reddit Crowd Control
                logger.info("Checking modqueue for Crowd Control removals...")
                monitor_modqueue_for_crowd_control(reddit_bot, subreddit_name, username)

            except Exception as e:
                logger.error(f"Unexpected error in main_logic: {e}")

        try:
            # Retry the main logic up to max_retries on failure
            retry_operation(main_logic, max_retries)
        except Exception as e:
            logger.error(f"Fatal error in bot operation: {e}")

        # Wait 5 minutes before running again
        time.sleep(300)
