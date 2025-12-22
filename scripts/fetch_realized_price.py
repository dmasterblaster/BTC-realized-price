import os
import io
import json
from pathlib import Path

import pandas as pd
import requests

API_URL = "https://api.bitcoinmagazinepro.com/metrics/realized-price"


def main():
    api_key = os.environ["BMP_API_KEY"]

    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    resp = requests.get(API_URL, headers=headers, timeout=30)
    resp.raise_for_status()

    csv_text = resp.text

    df = pd.read_csv(
        io.StringIO(csv_text),
        index_col=0,
    )

    dates = df.index.astype(str).tolist()
    first_col = df.columns[0]
    realized_price = df[first_col].astype(float).tolist()

    data = {
        "dates": dates,
        "realized_price": realized_price,
    }

    out_dir = Path("data")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "realized-price.json"

    with out_path.open("w") as f:
        json.dump(data, f)

    print(f"Wrote {len(dates)} rows to {out_path} using column '{first_col}'")


if __name__ == "__main__":
    main()
