"""Unit tests: the third-party API is replaced by a fake, so no network is used."""

from unittest.mock import Mock, patch

import requests
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)
HEADERS = {"id-account": "0195ae95-5be7-7dd3-b35d-7a7d87c404fb"}

USD_EUR = {
    "USDEUR": {
        "bid": "0.80",
        "ask": "0.82",
        "create_date": "2021-09-01 14:23:42",
    }
}


def provider(status_code=200, body=None):
    return Mock(status_code=status_code, json=Mock(return_value=body))


def test_health_check():
    response = client.get("/exchanges/health-check")
    assert response.status_code == 200


@patch("main.requests.get", return_value=provider(body=USD_EUR))
def test_exchange_returns_rate(get):
    response = client.get("/exchanges/USD/EUR", headers=HEADERS)

    assert response.status_code == 200
    assert response.json() == {
        "sell": 0.82,
        "buy": 0.80,
        "date": "2021-09-01 14:23:42",
        "id-account": HEADERS["id-account"],
    }
    assert get.call_args.args[0].endswith("/USD-EUR")


@patch("main.requests.get", return_value=provider(body=USD_EUR))
def test_lowercase_codes_are_accepted(get):
    response = client.get("/exchanges/usd/eur", headers=HEADERS)
    assert response.status_code == 200


def test_missing_id_account_is_unauthorized():
    response = client.get("/exchanges/USD/EUR")
    assert response.status_code == 401


def test_invalid_currency_code_is_rejected():
    response = client.get("/exchanges/US/EURO", headers=HEADERS)
    assert response.status_code == 422


@patch("main.requests.get", return_value=provider(status_code=404, body={}))
def test_unknown_pair_is_not_found(get):
    response = client.get("/exchanges/XYZ/ABC", headers=HEADERS)
    assert response.status_code == 404


@patch("main.requests.get", side_effect=requests.Timeout())
def test_provider_down_is_bad_gateway(get):
    response = client.get("/exchanges/USD/EUR", headers=HEADERS)
    assert response.status_code == 502
