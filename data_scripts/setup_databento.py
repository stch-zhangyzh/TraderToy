# Source: https://nautilustrader.io/docs/latest/tutorials/databento_data_catalog
# Source: https://nautilustrader.io/docs/latest/tutorials/databento_overview

import os
import shutil
from pathlib import Path

# Try to import databento, handle if not installed
try:
    import databento as db
    from databento import DBNStore
except ImportError:
    print("Error: 'databento' library is not installed.")
    print("Please run: pip install databento")
    exit(1)

from nautilus_trader.adapters.databento.loaders import DatabentoDataLoader
from nautilus_trader.persistence.catalog import ParquetDataCatalog


def main():
    print("=== NautilusTrader Databento Data Catalog Setup ===")
    print("This example demonstrates how to request data from Databento")
    print("and load it into a Nautilus Parquet Data Catalog.")

    # 1. Setup API Client
    # It is recommended to set the DATABENTO_API_KEY environment variable.
    # Alternatively, pass it directly: client = db.Historical(key="YOUR_KEY")
    api_key = os.environ.get("DATABENTO_API_KEY")
    if not api_key:
        print("\n[WARNING] DATABENTO_API_KEY environment variable not found.")
        print("You can set it in your terminal or replace this check with your key string.")
        print("Continuing... (requests might fail if key is required for the dataset)")
        # client = db.Historical(key="YOUR_KEY_HERE") 
        # For this example, we assume the user might have set it or will set it.
        try:
             client = db.Historical()
        except Exception as e:
             print(f"Failed to initialize Databento client: {e}")
             return
    else:
        client = db.Historical()

    # 2. Prepare Data Directory (in data_scripts/databento_data)
    # Use relative path to keep it contained
    DATABENTO_DATA_DIR = Path(__file__).parent / "databento_data"
    DATABENTO_DATA_DIR.mkdir(exist_ok=True)
    
    # 3. Request Data (Example: E-mini S&P 500 Futures, MBP-10)
    # We use a small range for demonstration.
    file_path = DATABENTO_DATA_DIR / "es-front-glbx-mbp10.dbn.zst"
    
    dataset = "GLBX.MDP3"
    symbols = ["ES.n.0"]  # Continuous front month
    schema = "mbp-10"     # Market by Price (L2), 10 levels
    start = "2023-12-06T14:30:00"
    end = "2023-12-06T14:35:00" # 5 minutes for demo

    print(f"\nChecking local data: {file_path}")
    if not file_path.exists():
        print("Data not found locally. Requesting from Databento...")
        try:
            # Check cost first (optional but recommended)
            cost = client.metadata.get_cost(
                dataset=dataset,
                symbols=symbols,
                stype_in="continuous",
                schema=schema,
                start=start,
                end=end,
            )
            print(f"Estimated cost: ${cost:.4f}")

            # Request and download
            print("Downloading...")
            client.timeseries.get_range(
                dataset=dataset,
                symbols=symbols,
                stype_in="continuous",
                schema=schema,
                start=start,
                end=end,
                path=file_path,
            )
            print("Download complete.")
        except Exception as e:
            print(f"Error downloading data: {e}")
            return
    else:
        print("Data found locally, skipping download.")

    # 4. Create/Reset Catalog (in project root/catalog_databento)
    project_root = Path(__file__).parent.parent
    CATALOG_PATH = project_root / "catalog_databento"
    
    if CATALOG_PATH.exists():
        shutil.rmtree(CATALOG_PATH)
    CATALOG_PATH.mkdir()
    
    catalog = ParquetDataCatalog(str(CATALOG_PATH))
    print(f"\nCreated catalog at: {CATALOG_PATH}")

    # 5. Load Data into Nautilus Objects
    print("Loading DBN file into Nautilus objects...")
    loader = DatabentoDataLoader()
    
    # The loader can infer instrument details from the DBN metadata
    try:
        # as_legacy_cython=False uses Rust objects (more efficient)
        nautilus_data = loader.from_dbn_file(
            path=file_path,
            as_legacy_cython=False, 
        )
        
        # Note: DatabentoDataLoader returns a list of objects (Instruments + Data)
        # We separate them for catalog writing (though write_data handles lists mixedly usually, 
        # it's good to be explicit or just pass the list if the catalog supports it).
        # The loader returns a list of [Instrument, Data...] usually.
        
        print(f"Loaded {len(nautilus_data)} objects.")

        # 6. Write to Catalog
        print("Writing to catalog...")
        catalog.write_data(nautilus_data)
        print("Write complete.")
        
        # 7. Verify
        instruments = catalog.instruments()
        print(f"\nInstruments in catalog: {[str(i.id) for i in instruments]}")
        
        # Check available data
        # Depending on what was loaded (QuoteTick, TradeTick, OrderBookDelta, etc.)
        # mbp-10 usually maps to OrderBookDelta or L2 data in Nautilus
        if instruments:
            inst_id = instruments[0].id
            # Try loading deltas (since it's mbp-10)
            deltas = catalog.order_book_deltas(instrument_ids=[inst_id])
            print(f"Loaded {len(deltas)} order book deltas from catalog.")
            
    except Exception as e:
        print(f"Error processing data: {e}")

if __name__ == "__main__":
    main()
