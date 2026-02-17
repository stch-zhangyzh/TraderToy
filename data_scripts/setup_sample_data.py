# Source: https://nautilustrader.io/docs/latest/getting_started/quickstart

import os
import urllib.request
from pathlib import Path

from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.persistence.wranglers import QuoteTickDataWrangler
from nautilus_trader.test_kit.providers import CSVTickDataLoader
from nautilus_trader.test_kit.providers import TestInstrumentProvider


def main():
    # Create catalog directory in project root (parent of this script)
    project_root = Path(__file__).parent.parent
    catalog_path = project_root / "catalog"
    catalog_path.mkdir(exist_ok=True)

    print(f"Project root: {project_root}")
    print(f"Catalog directory: {catalog_path}")

    try:
        # Download EUR/USD sample data
        print("Downloading EUR/USD sample data...")
        url = "https://raw.githubusercontent.com/nautechsystems/nautilus_data/main/raw_data/fx_hist_data/DAT_ASCII_EURUSD_T_202001.csv.gz"
        filename = "EURUSD_202001.csv.gz"
        
        # Download to data_scripts directory temporarily
        local_filename = Path(__file__).parent / filename

        if not local_filename.exists():
            print(f"Downloading from: {url}")
            urllib.request.urlretrieve(url, local_filename)  # noqa: S310
            print("Download complete")
        else:
            print("File already exists, skipping download.")

        # Create the instrument
        print("Creating EUR/USD instrument...")
        instrument = TestInstrumentProvider.default_fx_ccy("EUR/USD")

        # Load and process the tick data
        print("Loading tick data...")
        wrangler = QuoteTickDataWrangler(instrument)

        df = CSVTickDataLoader.load(
            local_filename,
            index_col=0,
            datetime_format="%Y%m%d %H%M%S%f",
        )
        df.columns = ["bid_price", "ask_price", "size"]
        print(f"Loaded {len(df)} ticks")

        # Process ticks
        print("Processing ticks...")
        ticks = wrangler.process(df)

        # Write to catalog
        print("Writing data to catalog...")
        catalog = ParquetDataCatalog(str(catalog_path))

        catalog.write_data([instrument])
        print("Instrument written to catalog")

        catalog.write_data(ticks)
        print("Tick data written to catalog")

        # Verify what was written
        print("\nVerifying catalog contents...")
        test_catalog = ParquetDataCatalog(str(catalog_path))
        loaded_instruments = test_catalog.instruments()
        print(f"Instruments in catalog: {[str(i.id) for i in loaded_instruments]}")

        # Clean up downloaded file
        if local_filename.exists():
            os.unlink(local_filename)
        print("\nData setup complete!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
