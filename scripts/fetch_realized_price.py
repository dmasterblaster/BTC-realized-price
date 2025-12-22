import os
import io
import json
from pathlib import Path

import pandas as pd
import requests

API_URL = "https://api.bitcoinmagazinepro.com/metrics/realized-price"
# If this ever breaks, you can also try the v1 version:
# API_URL = "https://api.bitcoinmagazinepro.com/v1/metrics/realized-price"


def main():
    api_key = os.environ["BMP_API_KEY"]

    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    resp = requests.get(API_URL, headers=headers, timeout=30)
    print("BMP API status code:", resp.status_code)
    resp.raise_for_status()

    raw_text = resp.text
    print("First 200 characters of *raw* response:")
    print(raw_text[:200])

    if not raw_text.strip():
        raise RuntimeError("Empty response from BMP API")

    # The response is a quoted string with literal "\n" characters.
    # Example: ",Date,Price,realized_price\n0,2010-08-17,..."
    # 1) Strip surrounding quotes
    csv_quoted = raw_text.strip()
    if csv_quoted.startswith('"') and csv_quoted.endswith('"'):
        csv_quoted = csv_quoted[1:-1]

    # 2) Convert literal "\n" sequences into real newlines
    csv_text = csv_quoted.replace("\\n", "\n")

    print("First 200 characters after unquoting / replacing \\n:")
    print(csv_text[:200])

    # 3) Parse CSV
    df = pd.read_csv(io.StringIO(csv_text))

    if df.empty or len(df.columns) == 0:
        raise RuntimeError(f"Parsed empty DataFrame from CSV. Columns: {list(df.columns)}")

    print("Parsed columns:", list(df.columns))

    # The first column is an unnamed index (0,1,2,...) because of the leading comma.
    # The useful columns are "Date", "Price", "realized_price".
    if "Date" not in df.columns or "realized_price" not in df.columns:
        raise RuntimeError(f"Expected 'Date' and 'realized_price' columns, got {list(df.columns)}")

    # Use Date as index
    df = df.set_index("Date")

    series = df["realized_price"].dropna()

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
