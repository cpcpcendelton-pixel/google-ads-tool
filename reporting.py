# src/reporting.py
# Performance reporting for Google Ads accounts under a single manager account.
# Pulls spend / impressions / clicks / conversions / cost-per-conversion per
# campaign via GAQL, aggregates per account, and optionally exports to CSV.
#
#   python src/reporting.py --days 7
#   python src/reporting.py --days 30 --channel MULTI_CHANNEL --csv report.csv
#
#   pip install google-ads
import argparse
import csv
import sys
from datetime import date, timedelta

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


def load_client(config_path):
    return GoogleAdsClient.load_from_storage(config_path)


def iter_child_accounts(client, mcc_id):
    """Yield (customer_id, name) for enabled, non-manager accounts under the MCC."""
    ga = client.get_service("GoogleAdsService")
    query = """
        SELECT customer_client.id,
               customer_client.descriptive_name
        FROM customer_client
        WHERE customer_client.level <= 2
          AND customer_client.manager = FALSE
          AND customer_client.status = 'ENABLED'
    """
    for row in ga.search(customer_id=mcc_id, query=query):
        yield str(row.customer_client.id), row.customer_client.descriptive_name


def fetch_campaign_metrics(client, customer_id, start, end, channel=None):
    """Return per-campaign metric dicts for the given account and date range."""
    ga = client.get_service("GoogleAdsService")
    channel_filter = (
        f"AND campaign.advertising_channel_type = '{channel}'" if channel else ""
    )
    query = f"""
        SELECT campaign.name,
               campaign.advertising_channel_type,
               metrics.cost_micros,
               metrics.impressions,
               metrics.clicks,
               metrics.conversions
        FROM campaign
        WHERE segments.date BETWEEN '{start}' AND '{end}'
          AND campaign.status = 'ENABLED'
          {channel_filter}
        ORDER BY metrics.cost_micros DESC
    """
    rows = []
    for r in ga.search(customer_id=customer_id, query=query):
        cost = r.metrics.cost_micros / 1_000_000
        conv = r.metrics.conversions
        rows.append({
            "campaign": r.campaign.name,
            "channel": r.campaign.advertising_channel_type.name,
            "spend": round(cost, 2),
            "impressions": r.metrics.impressions,
            "clicks": r.metrics.clicks,
            "conversions": round(conv, 1),
            "cpa": round(cost / conv, 2) if conv else None,
        })
    return rows


def collect(client, mcc_id, start, end, channel=None):
    """Walk all child accounts and return a flat list of rows tagged with account."""
    out = []
    for cid, name in iter_child_accounts(client, mcc_id):
        try:
            for row in fetch_campaign_metrics(client, cid, start, end, channel):
                out.append({"account_id": cid, "account": name, **row})
        except GoogleAdsException as ex:
            print(f"[{name}] error: {ex.error.code().name}", file=sys.stderr)
    return out


def print_table(rows):
    if not rows:
        print("No data for the selected period/filters.")
        return
    header = f"{'Account':<22}{'Campaign':<32}{'Channel':<14}{'Spend':>10}{'Conv':>8}{'CPA':>9}"
    print(header)
    print("-" * len(header))
    for r in rows:
        cpa = f"${r['cpa']:.2f}" if r["cpa"] is not None else "—"
        print(f"{r['account'][:21]:<22}{r['campaign'][:31]:<32}{r['channel']:<14}"
              f"${r['spend']:>9.2f}{r['conversions']:>8.1f}{cpa:>9}")


def export_csv(rows, path):
    fields = ["account_id", "account", "campaign", "channel",
              "spend", "impressions", "clicks", "conversions", "cpa"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {path}")


def main():
    parser = argparse.ArgumentParser(description="Google Ads performance reporting via GAQL.")
    parser.add_argument("--days", type=int, default=7, help="Look-back window in days (default: 7).")
    parser.add_argument("--config", default="google-ads.yaml", help="Path to google-ads.yaml.")
    parser.add_argument("--channel", default=None,
                        help="Filter by advertising_channel_type, e.g. MULTI_CHANNEL, SEARCH, DISPLAY.")
    parser.add_argument("--csv", default=None, help="Optional path to export results as CSV.")
    args = parser.parse_args()

    client = load_client(args.config)
    mcc_id = client.login_customer_id
    if not mcc_id:
        raise SystemExit("login_customer_id is missing in the configuration file.")

    end = date.today()
    start = end - timedelta(days=args.days - 1)

    rows = collect(client, mcc_id, start.isoformat(), end.isoformat(), args.channel)
    print_table(rows)
    if args.csv:
        export_csv(rows, args.csv)


if __name__ == "__main__":
    main()
