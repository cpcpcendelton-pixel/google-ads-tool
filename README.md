# google-ads-tool

Lightweight Python tooling for **Google Ads API** automation: performance
reporting via GAQL and threshold-based campaign/budget management across
accounts under a single manager account (MCC).

Built on the official [`google-ads`](https://pypi.org/project/google-ads/)
Python client library.

## Features

- **Reporting** — pull spend, conversions and cost-per-acquisition by
  campaign and account using GAQL.
- **Account discovery** — enumerate enabled child accounts under an MCC.
- **Budget & tCPA automation** — adjust budgets and target CPA based on
  configurable internal performance thresholds.

## Intended use

This is an internal tool operated by the developer for their own Google Ads
accounts under a single manager account. It is used for performance reporting
and campaign management only. It does not resell or redistribute Google Ads
API data, and it is not provided to external parties.

## Setup

```bash
pip install -r requirements.txt
cp google-ads.yaml.example google-ads.yaml   # fill in your own credentials
python get_refresh_token.py                  # one-time OAuth flow
python read_check.py                         # verify credentials
```

## Configuration

Credentials are supplied via `google-ads.yaml` (never committed — see
`.gitignore`). Use `google-ads.yaml.example` as a template.

## Requirements

- Python 3.12+
- A Google Ads manager account (MCC) and an approved developer token

## License

MIT
