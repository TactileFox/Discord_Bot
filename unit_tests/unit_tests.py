import unittest
import json
from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError
from api_requests import get_usa_weather, get_astronomy_picture

# In terminal, run python -m unittest unit_tests.py


class TestAPI(unittest.IsolatedAsyncioTestCase):

    @classmethod  # Runs once at start
    def setUpClass(cls):

        with open('./unit_tests/mock_nws_points.json') as f:
            cls.mock_nws_points_json = json.load(f)
        with open('./unit_tests/mock_nws_gridpoints.json') as f:
            cls.mock_nws_gridpoints_json = json.load(f)
        with open('./unit_tests/mock_nasa_apod_singular.json') as f:
            cls.mock_nasa_apod_singular_json = json.load(f)
        with open('./unit_tests/mock_nasa_apod_range.json') as f:
            cls.mock_nasa_apod_range_json = json.load(f)

    async def test_weather_api_200(self):
        with patch('requests.get') as mocker:

            # Points
            mock_response_one = MagicMock()
            mock_response_one.status_code = 200
            mock_response_one.json.return_value = self.mock_nws_points_json

            # Gridpoints / Forecast
            nws_json = self.mock_nws_gridpoints_json
            mock_response_two = MagicMock()
            mock_response_two.status_code = 200
            mock_response_two.json.return_value = nws_json

            mocker.side_effect = [mock_response_one, mock_response_two]
            result = await get_usa_weather(46.0, 76.0, 'F')
            result_city, result_state, result_list = result

            self.assertEqual(result_city, 'Rochester')
            self.assertEqual(result_state, 'MI')
            self.assertEqual(result_list, nws_json['properties']['periods'])

    async def test_weather_api_points_400(self):
        with patch('requests.get') as mocker:

            mock_response = MagicMock()
            mock_response.status_code = 400
            mocker.return_value = mock_response

            with self.assertRaises(HTTPError):
                await get_usa_weather(46.0, -76.0, 'F')

    async def test_weather_api_points_404(self):
        with patch('requests.get') as mocker:

            mock_response = MagicMock()
            mock_response.status_code = 404
            mocker.return_value = mock_response

            with self.assertRaises(HTTPError):
                await get_usa_weather(46.0, -76.0, 'F')

    async def test_weather_api_points_500(self):
        with patch('requests.get') as mocker:

            mock_response = MagicMock()
            mock_response.status_code = 500
            mocker.return_value = mock_response

            with self.assertRaises(HTTPError):
                await get_usa_weather(46.0, -76.0, 'F')

    async def test_weather_api_forecast_400(self):
        with patch('requests.get') as mocker:

            mock_response_one = MagicMock()
            mock_response_one.status_code = 200

            mock_response_two = MagicMock()
            mock_response_two.status_code = 400

            mocker.side_effect = [mock_response_one, mock_response_two]

            with self.assertRaises(HTTPError):
                await get_usa_weather(46.0, -76.0, 'F')

    async def test_weather_api_forecast_404(self):
        with patch('requests.get') as mocker:

            mock_response_one = MagicMock()
            mock_response_one.status_code = 200

            mock_response_two = MagicMock()
            mock_response_two.status_code = 404

            mocker.side_effect = [mock_response_one, mock_response_two]

            with self.assertRaises(HTTPError):
                await get_usa_weather(46.0, -76.0, 'F')

    async def test_weather_api_forecast_500(self):
        with patch('requests.get') as mocker:

            mock_response_one = MagicMock()
            mock_response_one.status_code = 200

            mock_response_two = MagicMock()
            mock_response_two.status_code = 500

            mocker.side_effect = [mock_response_one, mock_response_two]

            with self.assertRaises(HTTPError):
                await get_usa_weather(46.0, -76.0, 'F')

    async def test_apod_api_singular_200(self):
        with patch('requests.get') as mocker:

            nasa_json = self.mock_nasa_apod_singular_json
            mock_response_singular_200 = MagicMock()
            mock_response_singular_200.status_code = 200
            mock_response_singular_200.json.return_value = nasa_json
            mocker.return_value = mock_response_singular_200

            result = await get_astronomy_picture()
            result_url, result_date, result_title, result_explanation = result
            self.assertEqual(result_url[0], nasa_json['hdurl'])
            self.assertEqual(result_date[0], nasa_json['date'])
            self.assertEqual(result_title[0], nasa_json['title'])
            self.assertEqual(result_explanation[0], nasa_json['explanation'])

    async def test_apod_range_200(self):
        with patch('requests.get') as mocker:

            nasa_json = self.mock_nasa_apod_range_json
            mock_response_range_200 = MagicMock()
            mock_response_range_200.status_code = 200
            mock_response_range_200.json.return_value = nasa_json
            mocker.return_value = mock_response_range_200

            urls: list[str] = list()
            dates: list[str] = list()
            titles: list[str] = list()
            explanations: list[str] = list()
            for point in nasa_json:
                urls.append(point['hdurl'])
                dates.append(point['date'])
                titles.append(point['title'])
                explanations.append(point['explanation'])

            results = await get_astronomy_picture('2024-12-05', '2024-12-20')
            result_urls, result_dates, result_titles, result_explanations = results
            self.assertEqual(result_urls, urls)
            self.assertEqual(result_dates, dates)
            self.assertEqual(result_titles, titles)
            self.assertEqual(result_explanations, explanations)

    async def test_apod_400(self):
        with patch('requests.get') as mocker:

            mock_response_400 = MagicMock()
            mock_response_400.status_code = 400
            mocker.return_value = mock_response_400

            with self.assertRaises(HTTPError):
                await get_astronomy_picture()

    async def test_apod_403(self):
        with patch('requests.get') as mocker:

            mock_response_403 = MagicMock()
            mock_response_403.status_code = 403
            mocker.return_value = mock_response_403

            with self.assertRaises(HTTPError):
                await get_astronomy_picture()

    async def test_apod_500(self):
        with patch('requests.get') as mocker:

            mock_response_500 = MagicMock()
            mock_response_500.status_code = 500
            mocker.return_value = mock_response_500

            with self.assertRaises(HTTPError):
                await get_astronomy_picture()

    async def test_apod_empty_list_200(self):
        with patch('requests.get') as mocker:

            nasa_json = self.mock_nasa_apod_singular_json
            mock_response_empty_one = MagicMock()
            mock_response_empty_one.status_code = 200
            mock_response_empty_one.json.return_value = list()

            mock_response_empty_two = MagicMock()
            mock_response_empty_two.status_code = 200
            mock_response_empty_two.json.return_value = nasa_json

            mocker.side_effect = [mock_response_empty_one,
                                  mock_response_empty_two]

            result = await get_astronomy_picture()
            result_url, result_date, result_title, result_explanation = result
            self.assertEqual(result_url[0], nasa_json['hdurl'])
            self.assertEqual(result_date[0], nasa_json['date'])
            self.assertEqual(result_title[0], nasa_json['title'])
            self.assertEqual(result_explanation[0], nasa_json['explanation'])
            self.assertEqual(mocker.call_count, 2)

    async def test_apod_empty_list_400(self):
        with patch('requests.get') as mocker:
            # Empty List, 200
            mock_response_empty_one = MagicMock()
            mock_response_empty_one.status_code = 200
            mock_response_empty_one.json.return_value = list()

            # 400
            mock_response_empty_two = MagicMock()
            mock_response_empty_two.status_code = 400

            mocker.side_effect = [mock_response_empty_one,
                                  mock_response_empty_two]

            with self.assertRaises(HTTPError):
                await get_astronomy_picture()
            self.assertEqual(mocker.call_count, 2)
