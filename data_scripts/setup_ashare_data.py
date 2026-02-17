# Source: https://github.com/mpquant/Ashare
# Source: https://nautilustrader.io/docs/latest/tutorials/data_catalog

import sys
import shutil
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

# Add Ashare directory to path
sys.path.append(str(Path(__file__).parent / "Ashare"))

try:
    from Ashare import get_price
except ImportError:
    print("Error: Could not import Ashare. Make sure Ashare.py is in data_scripts/Ashare/")
    sys.exit(1)

from nautilus_trader.model.currencies import CNY
from nautilus_trader.model.enums import PriceType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.instruments import Equity
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.model.data import Bar, BarType, BarSpecification
from nautilus_trader.model.identifiers import Symbol
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.persistence.wranglers import BarDataWrangler


def create_ashare_instrument(symbol: Symbol, venue_name: str) -> Equity:
    """Create a Nautilus Equity instrument for A-share stock."""
    # Example: 600519.SSE
    instrument_id_str = f"{symbol.value}.{venue_name}"
    
    return Equity(
        instrument_id=InstrumentId.from_str(instrument_id_str),
        raw_symbol=symbol,
        currency=CNY,
        price_precision=2,
        price_increment=Price.from_str("0.01"),
        lot_size=Quantity.from_int(100),  # Standard lot size in China is 100
        ts_event=0,
        ts_init=0,
    )

def fetch_and_process_data(code: str, symbol: Symbol, venue: str, days: int = 300):
    print(f"Fetching data for {code}...")
    
    # Fetch data using Ashare
    # frequency='1d' for daily bars
    df = get_price(code, frequency='1d', count=days)
    
    if df.empty:
        print(f"Warning: No data found for {code}")
        return None, None

    # Rename columns to match Nautilus requirements (lowercase)
    # Ashare returns: open, close, high, low, volume (already lowercase usually, but let's be safe)
    df.columns = [c.lower() for c in df.columns]
    
    # Ashare index is already datetime, but naive. Assume it's Beijing Time (UTC+8)
    # We need to convert to UTC for Nautilus
    # 1. Localize to Asia/Shanghai
    # 2. Convert to UTC
    # Note: Ashare dates are usually just dates (YYYY-MM-DD) for daily data, representing 00:00 or 15:00?
    # Usually daily bars are stamped at 00:00 or close time. 
    # Let's assume the timestamp is the date. We'll set it to UTC directly for simplicity 
    # or properly localize. Nautilus prefers UTC.
    
    # If index is just date, pd.to_datetime might make it 00:00:00.
    # Let's localize to UTC+8 then convert to UTC
    df.index = df.index.tz_localize("Asia/Shanghai").tz_convert("UTC")
    
    # Create Instrument
    instrument = create_ashare_instrument(symbol, venue)
    bar_type = BarType.from_str(f"{instrument.id}-1-DAY-LAST-EXTERNAL")

    return instrument, df, bar_type

def main():
    print("=== NautilusTrader A-share Data Setup ===")
    
    # 1. Setup Catalog
    project_root = Path(__file__).parent.parent
    catalog_path = project_root / "catalog_ashare"
    
    if catalog_path.exists():
        shutil.rmtree(catalog_path)
    catalog_path.mkdir()
    
    catalog = ParquetDataCatalog(str(catalog_path))
    print(f"Created catalog at: {catalog_path}")

    # 2. Define Stocks to Fetch
    # Format: (Ashare_Code, Symbol, Venue)
    stocks = [
        ("sh600519", "600519", "SSE"),  # Kweichow Moutai
        ("sz000001", "000001", "SZSE"), # Ping An Bank
    ]

    for code, symbol_str, venue_name in stocks:
        try:
            # Need BarAggregation enum
            from nautilus_trader.model.enums import BarAggregation
            
            instrument, df, bar_type = fetch_and_process_data(code, Symbol(symbol_str), venue_name)
            
            if instrument and df is not None:
                # Wrangle Data
                wrangler = BarDataWrangler(
                    bar_type=bar_type,
                    instrument=instrument,
                )
                
                print(f"Processing {len(df)} bars for {instrument.id}...")
                bars = wrangler.process(df)
                
                # Write to Catalog
                catalog.write_data([instrument])
                catalog.write_data(bars)
                print(f"Written {len(bars)} bars to catalog.")
                
        except Exception as e:
            print(f"Error processing {code}: {e}")
            import traceback
            traceback.print_exc()

    # 3. Verify
    print("\nVerifying catalog contents...")
    instruments = catalog.instruments()
    print(f"Instruments: {[str(i.id) for i in instruments]}")

if __name__ == "__main__":
    main()
