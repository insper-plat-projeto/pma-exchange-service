"""Exchange microservice: current exchange rate between two currencies.

The gateway authenticates every request and forwards the account id in the
`id-account` header; the rate itself comes from a third-party API (AwesomeAPI).
"""

import os
from typing import Annotated

import requests
from fastapi import FastAPI, Header, HTTPException, Path
from prometheus_fastapi_instrumentator import Instrumentator

# third-party API: GET {URL}/USD-EUR -> {"USDEUR": {"bid": ..., "ask": ..., "create_date": ...}}
AWESOMEAPI_URL = os.getenv(
    "AWESOMEAPI_URL", "https://economia.awesomeapi.com.br/json/last"
)
TIMEOUT_SECONDS = float(os.getenv("AWESOMEAPI_TIMEOUT", "5"))

# three letters (ISO 4217, e.g. USD); anything else answers 422
Currency = Annotated[str, Path(pattern=r"^[A-Za-z]{3}$")]

app = FastAPI(title="exchange-service")

# metrics in Prometheus format, under the service prefix like the Spring services
# (/accounts/actuator/prometheus): request count and latency per route, plus process stats
Instrumentator().instrument(app).expose(app, endpoint="/exchanges/metrics")


@app.get("/exchanges/health-check")
def health_check():
    return {"status": "up"}


@app.get("/exchanges/{from_currency}/{to_currency}")
def get_exchange(
    from_currency: Currency,
    to_currency: Currency,
    id_account: Annotated[str | None, Header(alias="id-account")] = None,
):
    # only the gateway sets id-account, after it validated the JWT cookie
    if not id_account:
        raise HTTPException(status_code=401, detail="Unauthorized")

    rate = fetch_rate(from_currency.upper(), to_currency.upper())

    return {
        # bid: price the market pays (the user sells), ask: price it charges (the user buys)
        "sell": float(rate["ask"]),
        "buy": float(rate["bid"]),
        "date": rate["create_date"],
        "id-account": id_account,
    }


def fetch_rate(from_currency: str, to_currency: str) -> dict:
    pair = f"{from_currency}-{to_currency}"
    try:
        response = requests.get(f"{AWESOMEAPI_URL}/{pair}", timeout=TIMEOUT_SECONDS)
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Exchange rate provider unavailable")

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail=f"Currency pair {pair} not found")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Exchange rate provider error")

    # AwesomeAPI keys the result by the pair without the dash: USDEUR
    rate = response.json().get(f"{from_currency}{to_currency}")
    if rate is None:
        raise HTTPException(status_code=502, detail="Unexpected provider response")
    return rate
