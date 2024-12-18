import os
import socket
import requests as r

async def get_usa_weather(lat: float, lon: float, unit_type: str) -> tuple[str, str, list]:

    # Get second url and city/state
    try:
        response = r.get(url=f'https://api.weather.gov/points/{lat},{lon}').json()
        if not response: raise Exception('API Returned None')
    except Exception as e:
        print(f'Exception getting weather {e}')
        return None
    
    city = response['properties']['relativeLocation']['properties']['city']
    state = response['properties']['relativeLocation']['properties']['state']

    # Forecast Info
    try:
        response = r.get(url=f"{response['properties']['forecast']}?units={unit_type}").json()
        if not response: raise Exception('API Returned None')
    except Exception as e:
        print(f'Exception getting weather {e}')
        return None

    # Return a list of dictionaries containing only the forecast info
    return (city, state, response['properties']['periods'])

async def get_astronomy_picture(start_date: str = None, end_date: str = None) -> tuple[list[str], list[str], list[str], list[str]]:

    api_key = os.getenv('NASA_API_KEY')

    params = dict()
    if start_date and not end_date:
        params['start_date'] = start_date
    elif start_date and end_date: # API defaults end to today but if an end is specified, it needs a start
        params['start_date'] = start_date
        params['end_date'] = end_date
    params['api_key'] = api_key

    # Header seems to stop it from thinking I'm a bot, won't return otherwise
    try:
        response = r.get(url=f'https://api.nasa.gov/planetary/apod', params=params, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}).json()
    except ConnectionError as e:
        print(f'Connection Error {e}')
        return None
    except socket.gaierror as e:
        print(f'Connection Error {e}')
        return None
    except Exception:
        return None

    # Make sure it's a list
    if type(response) == dict:
        data: list[dict] = list()
        data.append(response)
    else:
        data = response

    urls: list[str] = list()
    dates: list[str] = list()
    titles: list[str] = list()
    explanations: list[str] = list()

    for point in data:
        if point['media_type'] != 'image': continue
        if not point['hdurl']: continue
        urls.append(point['hdurl'])
        dates.append(point['date'])
        titles.append(point['title'])
        explanations.append(point['explanation'])

    return (urls, dates, titles, explanations)