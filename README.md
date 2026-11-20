# exchange-service

Microsserviço de câmbio da plataforma (Python + FastAPI). Devolve a cotação atual entre duas moedas, buscada na [AwesomeAPI](https://docs.awesomeapi.com.br/api-de-moedas).

## Endpoints

| Método | Caminho | Resposta |
|---|---|---|
| GET | `/exchanges/{from}/{to}` | `200 {"sell", "buy", "date", "id-account"}` |
| GET | `/exchanges/health-check` | `200 {"status": "up"}` |
| GET | `/exchanges/metrics` | métricas no formato do Prometheus (requisições e latência por rota) |

```json
GET /exchanges/USD/EUR

{
    "sell": 0.82,
    "buy": 0.80,
    "date": "2021-09-01 14:23:42",
    "id-account": "0195ae95-5be7-7dd3-b35d-7a7d87c404fb"
}
```

- `buy` é o `bid` da AwesomeAPI e `sell` é o `ask`.
- `id-account` vem do header que o gateway coloca depois de validar o JWT; sem ele, a resposta é `401`.
- Códigos de moeda com tamanho diferente de 3 letras: `422`. Par inexistente: `404`. API de terceiros fora do ar: `502`.

## Executar

```bash
docker compose up -d --build exchange
```

O serviço não publica porta: é acessado pelo gateway em `http://exchange:8080`.

## Testes

```bash
python -m venv .venv
.venv/Scripts/activate        # Linux/Mac: source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

Os testes substituem a API de terceiros por um mock e não usam a rede.

## Variáveis de ambiente

| Variável | Padrão |
|---|---|
| `AWESOMEAPI_URL` | `https://economia.awesomeapi.com.br/json/last` |
| `AWESOMEAPI_TIMEOUT` | `5` (segundos) |
