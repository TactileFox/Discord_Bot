import unittest 
import json
from api_requests import get_usa_weather, get_astronomy_picture
from unittest.mock import patch, MagicMock

# import psql_connection as psql
# import main
# from discord import Message, User, Guild

# In terminal, run python -m unittest unit_tests.py
    



class TestAPI(unittest.TestCase):

    @classmethod # Runs once at start
    def setUpClass(cls):

        with open('./unit_tests/mock_nws_points.json') as f:
            cls.mock_nws_points_json = json.load(f)
        with open('./unit_tests/mock_nws_gridpoints.json') as f:
            cls.mock_nws_gridpoints_json = json.load(f)
        with open('./unit_tests/mock_nasa_apod_singular.json') as f:
            cls.mock_nasa_apod_singular_json = json.load(f)
        with open('./unit_tests/mock_nasa_apod_range.json') as f:
            cls.mock_nasa_apod_range_json = json.load(f)

    @classmethod # Runs once at end
    def tearDownClass(cls):
        return NotImplemented

    def setUp(self): # runs before every test method
        pass
    
    def tearDown(self): # runs after every test method
        pass 


    def test_weather_api(self):
        #TODO what is a context manager??
        with patch('requests.get') as mocker:
            
            # Points
            mock_response_one = MagicMock()
            mock_response_one.status_code = 200
            mock_response_one.json.return_value = self.mock_nws_points_json

            # Gridpoints / Forecast
            mock_response_two = MagicMock()
            mock_response_two.status_code = 200
            mock_response_two.json.return_value = self.mock_nws_gridpoints_json
            
            mocker.side_effect = [mock_response_one, mock_response_two]
            result_city, result_state, result_list = get_usa_weather(46.0, 76.0, 'F')

            self.assertEqual(result_city, 'Rochester')
            self.assertEqual(result_state, 'MI')
            self.assertEqual(result_list, self.mock_nws_gridpoints_json['properties']['periods'])

            # Invalid Points


            # Status 400

    def test_apod_api(self):

        # Singular, 200
        mock_response_singular_200 = MagicMock()
        mock_response_singular_200.status_code = 200
        mock_response_singular_200.json.return_value = self.mock_nasa_apod_singular_json
        result_urls, result_dates, result_titles, result_explanations = get_astronomy_picture()
        self.assertEqual(result_urls, self.mock_nasa_apod_singular_json['hdurl'])
        self.assertEqual(result_dates, self.mock_nasa_apod_singular_json['date'])
        self.assertEqual(result_titles, self.mock_nasa_apod_singular_json['title'])
        self.assertEqual(result_explanations, self.mock_nasa_apod_singular_json['explanation'])

        # Range, 200
        mock_response_range_200 = MagicMock()
        mock_response_range_200.status_code = 200

        

urls, dates, titles, explanations
    