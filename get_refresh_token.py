# get_refresh_token.py — one-time OAuth flow to obtain a refresh token.
# Usage: place client_secret.json next to this file, then run.
#   pip install google-auth-oauthlib
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/adwords"]


def main():
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", scopes=SCOPES)
    creds = flow.run_local_server(port=0)  # opens a browser; grant consent
    print("\nCopy this into your google-ads.yaml:\n")
    print("refresh_token:", creds.refresh_token)


if __name__ == "__main__":
    main()
