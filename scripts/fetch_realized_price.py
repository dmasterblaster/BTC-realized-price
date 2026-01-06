import os
import io
import json
from pathlib import Path

import pandas as pd
import requests

API_URL = "https://api.bitcoinmagazinepro.com/metrics/realized-price"
# If this ever breaks, try:
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
    if not raw_text.strip():
        raise RuntimeError("Empty response from BMP API")

    # Unquote and turn literal "\n" into real newlines
    csv_quoted = raw_text.strip()
    if csv_quoted.startswith('"') and csv_quoted.endswith('"'):
        csv_quoted = csv_quoted[1:-1]
    csv_text = csv_quoted.replace("\\n", "\n")

    df = pd.read_csv(io.StringIO(csv_text))

    if df.empty or len(df.columns) == 0:
        raise RuntimeError(f"Parsed empty DataFrame. Columns: {list(df.columns)}")

    print("Parsed columns:", list(df.columns))

    # Expected columns include: Date, Price, realized_price
    if "Date" not in df.columns:
        raise RuntimeError(f"Expected 'Date' column, got {list(df.columns)}")
    if "realized_price" not in df.columns:
        raise RuntimeError(f"Expected 'realized_price' column, got {list(df.columns)}")
    if "Price" not in df.columns:
        raise RuntimeError(f"Expected 'Price' column, got {list(df.columns)}")

    # Build JSON with BOTH series
    df = df.set_index("Date")

    rp = df["realized_price"].astype(float)
    px = df["Price"].astype(float)

    out = []
    for d in df.index.astype(str).tolist():
        out.append(
            {
                "date": d,
                "realized_price": float(rp.loc[d]),
                "price": float(px.loc[d]),
            }
        )

    out_path = Path("data/realized-price.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))

    print(f"Wrote {len(out)} points to {out_path}")


if __name__ == "__main__":
    main()
