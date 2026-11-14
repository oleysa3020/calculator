import pytest
import requests
from unittest.mock import patch, MagicMock
from api import fetch_rates


def test_fetch_rates_success():
    """Проверяет успешность получения данных"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"Valute": {"USD": {"Value": 90.0}}}

    with patch('api.requests.get', return_value=mock_response):
        result = fetch_rates()

    assert result == {"Valute": {"USD": {"Value": 90.0}}}

def test_fetch_rates_success_without_success_field():
    """Проверяет успешность получения данных без поля success"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"Valute": {"USD": {"Value": 90.0}}}

    with patch('api.requests.get', return_value=mock_response):
        result = fetch_rates()

    assert result == {"Valute": {"USD": {"Value": 90.0}}}
    assert "success" not in result

def test_fetch_rates_http_error():
    """Проверяет на наличие HTTP-ошибок"""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

    with patch('api.requests.get', return_value=mock_response):
        result = fetch_rates()

    assert result == {}

def test_fetch_rates_connection_error():
    """Проверяет на наличие ошибок подключения"""
    with patch('api.requests.get') as mock_get:
        mock_get.side_effect = requests.ConnectionError("Connection failed")

        result = fetch_rates()

    assert result == {}


def test_fetch_rates_timeout_error():
    """Проверяет на наличие timeout-ошибок"""
    with patch('api.requests.get') as mock_get:
        mock_get.side_effect = requests.Timeout("Request timed out")

        result = fetch_rates()

    assert result == {}


def test_fetch_rates_empty_valute():
    """Проверяет, если API вернуло пустое поле Valute"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"Valute": {}}

    with patch('api.requests.get', return_value=mock_response):
        result = fetch_rates()

    assert result == {"Valute": {}}


def test_fetch_rates_malformed_json():
    """Проверяет JSON-файл на структурность"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Expecting value")

    with patch('api.requests.get', return_value=mock_response):
        with pytest.raises(ValueError):
            fetch_rates()


def test_fetch_rates_ssl_error():
    """Проверяет SSL-ошибку"""
    with patch('api.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.SSLError("SSL Certificate error")

        result = fetch_rates()

    assert result == {}