# -*- coding: utf-8 -*-

from unittest import TestCase
from flask import Flask
import pysnow
from flask_snow import Snow, InvalidUsage
from flask_snow.exceptions import ConfigError


def token_updater(token):
    return token


mock_token = {
    'access_token': 'mock_access_token',
    'expires_at': 12312312.1627002,
    'expires_in': 1234,
    'refresh_token': 'mock_refresh_token',
    'scope': ['useraccount'],
    'token_type': 'Bearer'
}


class FlaskTestCase(TestCase):
    """Mix-in class for creating the Flask application."""

    def setUp(self):
        app = Flask(__name__)
        app.config['DEBUG'] = True
        app.config['TESTING'] = True

        app.config['SNOW_INSTANCE'] = 'mock_instance'
        app.config['SNOW_OAUTH_CLIENT_ID'] = 'mock_client_id'
        app.config['SNOW_OAUTH_CLIENT_SECRET'] = 'mock_client_secret'

        app.logger.disabled = True
        self.app = app

    def tearDown(self):
        self.app = None


class TestSnow(FlaskTestCase):
    def test_constructor(self):
        Snow(self.app)

    def test_init_app(self):
        snow = Snow()
        if hasattr(self.app, 'extensions'):
            del self.app.extensions

        snow.init_app(self.app)

    def test_missing_config(self):
        """flask_snow.Snow should raise ConfigError if a required OAuth setting is missing"""

        snow = Snow()
        test1 = test2 = self.app

        test1.config.pop('SNOW_OAUTH_CLIENT_ID')
        self.assertRaises(ConfigError, snow.init_app, test1)

        test2.config.pop('SNOW_OAUTH_CLIENT_SECRET')
        self.assertRaises(ConfigError, snow.init_app, test2)

    def test_client_type(self):
        """setting SNOW_OAUTH_CLIENT_ID and SNOW_OAUTH_CLIENT_SECRET should set type Snow._client_type_oauth to True"""

        snow = Snow()
        snow.init_app(self.app)

        # oauth should be True
        self.assertEqual(snow._client_type_oauth, True)

        # basic should be False
        self.assertEqual(snow._client_type_basic, False)

    def test_token_updater(self):
        """token_updater property should be set to the function passed to its setter"""

        snow = Snow()
        snow.init_app(self.app)

        snow.token_updater = token_updater

        self.assertEqual(snow.token_updater, token_updater)

    def test_oauth_connect(self):
        """client set in connection context should be an instance of pysnow.OAuthClient"""

        snow = Snow()
        snow.init_app(self.app)

        snow.token_updater = token_updater

        with self.app.app_context():
            client = snow.connection
            self.assertEqual(type(client), pysnow.OAuthClient)

    def test_invalid_params(self):
        """passing a non-ParamsBuilder object to init_app() should raise `InvalidUsage`"""

        snow = Snow()
        self.assertRaises(InvalidUsage, snow.init_app, self.app, parameters={'test': 'test'})

    def test_params_builder(self):
        """passing a ParamsBuilder object to init_app() should set `Client` parameters"""

        pb = pysnow.ParamsBuilder()
        pb.add_custom({'test': 'test'})

        snow = Snow()
        snow.init_app(self.app, parameters=pb)

        snow.token_updater = token_updater

        with self.app.app_context():
            client = snow.connection
            p = client.parameters.as_dict()
            self.assertEqual('test' in p, True)

    def test_set_token(self):
        """After passing a token to Snow.set_token(), the pysnow.OAuthClient.token should equal the passed token"""

        snow = Snow(self.app)

        with self.app.app_context():
            snow.connection.set_token(mock_token)
            self.assertEqual(snow.connection.token, mock_token)
