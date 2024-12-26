import os
import socket
import logging
import requests as r
from requests.exceptions import HTTPError, ConnectionError


# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
file_handler = logging.FileHandler('api.log', encoding='utf-8')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.WARNING)
logger.addHandler(stream_handler)


async def get_usa_weather(
        lat: float, lon: float, unit_type: str
) -> tuple[str, str, list]:

    # Get second url and city/state
    try:
        response = r.get(url=f'https://api.weather.gov/points/{lat},{lon}')
        if response.status_code == 400:
            raise HTTPError('Bad Request')
        elif response.status_code == 404:
            raise HTTPError(f'Invalid Points: {lat}, {lon}')
        elif response.status_code == 500:
            raise HTTPError('Unexpected Error')
        else:
            content = response.json()
            location = content['properties']['relativeLocation']['properties']
            city = location['city']
            state = location['state']

        # Forecast Info
        forecast_link = content['properties']['forecast']
        response = r.get(url=f"{forecast_link}?units={unit_type}")
        if response.status_code == 400:
            raise HTTPError('Bad Request')
        elif response.status_code == 404:
            raise HTTPError('Invalid Grid')
        elif response.status_code == 500:
            raise HTTPError('Unexpected Error')
        else:
            content = response.json()
            return (city, state, content['properties']['periods'])
    except ConnectionError as e:
        logger.exception(
            f'Connection Error Resolving API.Weather.Gov: {str(e)}'
        )
        raise e
    except HTTPError as e:
        logger.exception(f'HTTPError From API.Weather.Gov: {str(e)}')
        raise e
    except KeyError as e:
        logger.exception(f'KeyError: {str(e)}')
        raise e
    except Exception as e:
        logger.exception(f'get_usa_weather Exception: {str(e)}')
        raise e


async def get_astronomy_picture(
        start_date: str = None, end_date: str = None
) -> tuple[list[str], list[str], list[str], list[str]]:

    api_key = os.getenv('NASA_API_KEY')

    params = dict()
    if start_date and not end_date:
        params['start_date'] = start_date
        logger.debug('Astronomy Start Date Assigned')
    elif start_date and end_date:
        params['start_date'] = start_date
        params['end_date'] = end_date
        logger.debug('Astronomy Date Range Assigned')
    params['api_key'] = api_key
    params['thumbs'] = True
    user_agent = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit'
                  '/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
    headers = {
        'User-Agent': user_agent
    }

    async def get_request(params: dict):
        logger.info('get_response called')
        response = r.get(
            url='https://api.nasa.gov/planetary/apod',
            params=params, headers=headers
        )
        if response.status_code == 400:
            raise HTTPError('Bad Request')
        elif response.status_code == 403:
            raise HTTPError('No API Key Passed')
        elif response.status_code == 500:
            raise HTTPError('API Error')
        else:
            response.raise_for_status()
        return response.json()

    try:
        content = await get_request(params=params)

        # If empty list
        if len(content) == 0:
            logger.debug('len(content) == 0')
            content = await get_request(
                params={'api_key': api_key, 'thumbs': True}
            )

    except ConnectionError as e:
        logger.error(f'Connection Error Resolving API.NASA.Gov: {str(e)}')
        raise e
    except socket.gaierror as e:
        logger.error(f'gaierror Resolving API.NASA.Gov: {str(e)}')
        raise e
    except HTTPError as e:
        logger.error(f'HTTPError From API.NASA.Gov: {str(e)}')
        raise e
    except Exception as e:
        logger.exception(f'get_astronomy Exception: {str(e)}')
        raise e

    # Make sure data is a list
    if isinstance(content, dict):
        data: list[dict] = list()
        data.append(content)
        logger.debug('Added APOD dict to list')
    else:
        data = content

    urls: list[str] = list()
    dates: list[str] = list()
    titles: list[str] = list()
    explanations: list[str] = list()

    try:
        for point in data:
            if point['media_type'] == 'image':
                urls.append(point['hdurl'])
            elif point['media_type'] == 'video':
                urls.append(point['thumbnail_url'])
            else:
                continue
            dates.append(point['date'])
            titles.append(point['title'])
            explanations.append(point['explanation'])
    except KeyError as e:
        logger.exception(f'KeyError: {str(e)}')
        raise e
    return (urls, dates, titles, explanations)
