import os
import socket
import requests as r


async def get_usa_weather(lat: float, lon: float, unit_type: str) -> tuple[str, str, list]:

    # Get second url and city/state
    try:
        response = r.get(url=f'https://api.weather.gov/points/{lat},{lon}')
        if response.status_code == 404: raise r.HTTPError(f'Invalid Points: {lat}, {lon}')
        elif response.status_code == 500: raise r.HTTPError('Unexpected Error')
        content = response.json()
    
        city = content['properties']['relativeLocation']['properties']['city']
        state = content['properties']['relativeLocation']['properties']['state']

        # Forecast Info
        response = r.get(url=f"{content['properties']['forecast']}?units={unit_type}")
        if response.status_code == 404: raise r.HTTPError('Invalid Points')
        elif response.status_code == 500: raise r.HTTPError('Unexpected Error')
        content = response.json()

    except r.HTTPError as e:
        return f'{e}'
    except Exception as e:
        return 'API Error'

    # Return a list of dictionaries containing only the forecast info
    return (city, state, content['properties']['periods'])

async def get_astronomy_picture(start_date: str = None, end_date: str = None) -> tuple[list[str], list[str], list[str], list[str]]:

    api_key = os.getenv('NASA_API_KEY')

    params = dict()
    if start_date and not end_date:
        params['start_date'] = start_date
    elif start_date and end_date:
        params['start_date'] = start_date
        params['end_date'] = end_date
    params['api_key'] = api_key

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }
    
    try:
        response = r.get(url=f'https://api.nasa.gov/planetary/apod', params=params, headers=headers)
        if response.status_code == 400: raise r.HTTPError('Bad Request')
        elif response.status_code == 403: raise r.HTTPError('No API Key Passed')
        content = response.json()

        # API is weird and returns an empty list for a few hours if asked for the following day
        if len(content) == 0:
            response = r.get(url=f'https://api.nasa.gov/planetary/apod', params={'api_key':api_key}, headers=headers)
            if response.status_code == 400: raise r.HTTPError('Bad Request')
            elif response.status_code == 403: raise r.HTTPError('No API Key Passed')
            content = response.json()

    except ConnectionError as e:
        print(f'Connection Error {e}')
        return None
    except socket.gaierror as e:
        print(f'Connection Error {e}')
        return None
    except r.HTTPError as e:
        print(e)
        return None
    except Exception as e:
        print(f'{e}')
        return None

    # Make sure data is a list
    if type(content) == dict:
        data: list[dict] = list()
        data.append(content)
    else:
        data = content

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