def get_current_weather(city, format='celsius'):
    """
    A simplified dummy function to return weather data for a city.

    Parameters:
    - city (str): The city, e.g., 'San Francisco'.
    - format (str): The temperature unit to use ('celsius' or 'fahrenheit').

    Returns:
    - dict: A dictionary containing weather data for specific cities or a no data message.
    """
    # Weather data for specific cities
    weather_data = {
        "London": {
            "celsius": {"temperature": "15 C", "condition": "Cloudy"},
            "fahrenheit": {"temperature": "59 F", "condition": "Cloudy"}
        },
        "Dublin": {
            "celsius": {"temperature": "18 C", "condition": "Partly Cloudy"},
            "fahrenheit": {"temperature": "64 F", "condition": "Partly Cloudy"}
        }
    }

    # Check if weather data exists for the given city and format
    if city in weather_data and format in weather_data[city]:
        return weather_data[city][format]
    else:
        return {"message": "No data available for the specified city."}

# # Example usage
# print(get_current_weather("London", "celsius"))
# print(get_current_weather("Paris", "fahrenheit"))
# print(get_current_weather("New York", "celsius"))
