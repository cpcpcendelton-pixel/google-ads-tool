# read_check.py — credential sanity check.
# Lists enabled child accounts under the configured MCC and prints today's
# spend / conversions / cost-per-acquisition per active campaign.
#   pip install google-ads
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


def get_child_accounts(client, mcc_id):
    ga = client.get_service("GoogleAdsService")
    query = """
        SELECT customer_client.id,
               customer_client.descriptive_name
        FROM customer_client
        WHERE customer_client.level <= 2
          AND customer_client.manager = FALSE
          AND customer_client.status = 'ENABLED'
    """
    rows = ga.search(customer_id=mcc_id, query=query)
    return [(str(r.customer_client.id), r.customer_client.descriptive_name) for r in rows]


def campaign_stats(client, customer_id):
    ga = client.get_service("GoogleAdsService")
    query = """
        SELECT campaign.name,
               campaign.status,
               campaign.advertising_channel_type,
               metrics.cost_micros,
               metrics.conversions
        FROM campaign
        WHERE segments.date DURING TODAY
          AND campaign.status = 'ENABLED'
        ORDER BY metrics.cost_micros DESC
    """
    return ga.search(customer_id=customer_id, query=query)


def main():
    client = GoogleAdsClient.load_from_storage("google-ads.yaml")
    mcc_id = client.login_customer_id  # read from google-ads.yaml, not hardcoded
    if not mcc_id:
        raise SystemExit("login_customer_id is missing in google-ads.yaml")

    children = get_child_accounts(client, mcc_id)
    print(f"Accounts found: {len(children)}\n")

    for cid, name in children:
        try:
            for r in campaign_stats(client, cid):
                cost = r.metrics.cost_micros / 1_000_000
                conv = r.metrics.conversions
                cpa = f"${cost / conv:.2f}" if conv else "—"
                print(f"[{name}] {r.campaign.name} | "
                      f"{r.campaign.advertising_channel_type.name} | "
                      f"spend ${cost:.2f} | conv {conv:.1f} | CPA {cpa}")
        except GoogleAdsException as ex:
            print(f"[{name}] error: {ex.error.code().name}")


if __name__ == "__main__":
    main()
