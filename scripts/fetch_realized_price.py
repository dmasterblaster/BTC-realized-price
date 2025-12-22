import os
import io
import json
from pathlib import Path

import pandas as pd
import requests

# NOTE: if this ever 404s, try removing the /v1 part, but this is the pattern BMP uses.
API_URL = "https://api.bitcoinmagazinepro.com/v1/metrics/realized-price"


def main():
    api_key = os.environ["BMP_API_KEY"]

    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    resp = requests.get(API_URL, headers=headers, timeout=30)

    # Debug info that will show up in the GitHub Actions log
    print("BMP API status code:", resp.status_code)
    resp.raise_for_status()
    csv_text = resp.text
    print("First 200 characters of response:")
    print(csv_text[:200])

    if not csv_text.strip():
        raise RuntimeError("Empty response from BMP API")

    # Parse CSV
    df = pd.read_csv(io.StringIO(csv_text), index_col=0)

    if df.empty or len(df.columns) == 0:
        raise RuntimeError(f"Parsed empty DataFrame from CSV. Columns: {list(df.columns)}")

    # Take the last column as the realized price series (most BMP metrics have the value last)
    value_col = df.columns[-1]
    series = df[value_col].dropna()

    dates = series.index.astype(str).tolist()
    values = series.astype(float).tolist()

    data = [
        {"date": d, "value": v}
        for d, v in zip(dates, values)
    ]

    out_path = Path("data/realized-price.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2))

    print(f"Wrote {len(data)} points to {out_path}")


if __name__ == "__main__":
    main()
