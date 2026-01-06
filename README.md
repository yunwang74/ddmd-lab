# DDMD Site — Enhanced

## Enable Analytics
GA4 is embedded with Measurement ID `G-2B172HB4HK` in all pages.

## Publications auto-update
1. Add a repository secret `ORCID_TOKEN` (scope /read-public) — obtain via ORCID client_credentials flow.
2. Run the GitHub Action “Update Publications from ORCID”.
3. The script pulls `https://pub.orcid.org/v3.0/0000-0001-8619-0455/works` and writes into the markers.

If no items appear, check that the token is valid and your ORCID works are public.
