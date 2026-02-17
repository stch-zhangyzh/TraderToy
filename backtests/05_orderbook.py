# Source: https://nautilustrader.io/docs/latest/tutorials/backtest_binance_orderbook
# Source: https://nautilustrader.io/docs/latest/tutorials/backtest_bybit_orderbook

from decimal import Decimal
from pathlib import Path
import shutil

import pandas as pd
from nautilus_trader.backtest.node import BacktestDataConfig
from nautilus_trader.backtest.node import BacktestEngineConfig
from nautilus_trader.backtest.node import BacktestNode
from nautilus_trader.backtest.node import BacktestRunConfig
from nautilus_trader.backtest.node import BacktestVenueConfig
from nautilus_trader.config import ImportableStrategyConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model import OrderBookDelta
from nautilus_trader.model import Venue
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.persistence.wranglers import OrderBookDeltaDataWrangler
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.test_kit.providers import TestDataProvider
from nautilus_trader.test_kit.providers import BinanceOrderBookDeltaDataLoader

def main():
    print("=== NautilusTrader OrderBook Data Backtest (Binance/Bybit) ===")
    print("This example demonstrates backtesting with Level 2 OrderBook Delta data.")
    print("We will simulate using built-in test data (simulated Binance format).")

    # 1. Setup Data
    # For this example, we'll use a test provider to simulate loading orderbook data
    # In a real scenario, you would load your own CSVs from Binance/Bybit
    
    # Path to your data directory (Example)
    # DATA_DIR = "~/Downloads/Data/Binance"
    # path_snap = data_path / "BTCUSDT_T_DEPTH_2022-11-01_depth_snap.csv"
    # path_update = data_path / "BTCUSDT_T_DEPTH_2022-11-01_depth_update.csv"

    print("Simulating OrderBook data load...")
    provider = TestDataProvider()
    # Using built-in test data for demonstration
    # Note: These exact files might not exist in the public repo test data, 
    # but the logic follows the tutorial. We'll use a placeholder or skip actual file loading
    # if files are missing, but for this code to run, we need valid data.
    
    # Let's use the catalog setup pattern but acknowledge we might not have the raw files
    # to make this runnable out-of-the-box without large data downloads.
    
    print("NOTE: This example requires large OrderBook data files which are not included.")
    print("Please refer to the tutorial links to download sample data from Binance/Bybit.")
    print("Below is the code structure you would use.")
    
    # --- Code Structure for Real Data ---
    """
    # 1. Load Snapshots & Updates
    df_snap = BinanceOrderBookDeltaDataLoader.load(path_snap)
    df_update = BinanceOrderBookDeltaDataLoader.load(path_update, nrows=1_000_000)

    # 2. Wrangle Data
    BTCUSDT_BINANCE = TestInstrumentProvider.btcusdt_binance()
    wrangler = OrderBookDeltaDataWrangler(BTCUSDT_BINANCE)
    deltas = wrangler.process(df_snap)
    deltas += wrangler.process(df_update)
    deltas.sort(key=lambda x: x.ts_init)

    # 3. Write to Catalog
    CATALOG_PATH = Path.cwd() / "catalog_ob"
    if CATALOG_PATH.exists():
        shutil.rmtree(CATALOG_PATH)
    CATALOG_PATH.mkdir()
    
    catalog = ParquetDataCatalog(CATALOG_PATH)
    catalog.write_data([BTCUSDT_BINANCE])
    catalog.write_data(deltas)

    # 4. Configure Backtest
    book_type = "L2_MBP" # Level 2 Market-By-Price

    data_config = BacktestDataConfig(
        catalog_path=str(CATALOG_PATH),
        data_cls=OrderBookDelta,
        instrument_id=BTCUSDT_BINANCE.id,
    )

    venue_config = BacktestVenueConfig(
        name="BINANCE",
        oms_type="NETTING",
        account_type="CASH",
        base_currency=None,
        starting_balances=["10 BTC", "100_000 USDT"],
        book_type=book_type, 
    )

    # 5. Configure Strategy (OrderBookImbalance)
    # Note: This strategy is part of nautilus_trader examples
    strategy_config = ImportableStrategyConfig(
        strategy_path="nautilus_trader.examples.strategies.orderbook_imbalance:OrderBookImbalance",
        config_path="nautilus_trader.examples.strategies.orderbook_imbalance:OrderBookImbalanceConfig",
        config={
            "instrument_id": BTCUSDT_BINANCE.id,
            "book_type": book_type,
            "max_trade_size": Decimal("0.1"),
            "min_seconds_between_triggers": 1.0,
        },
    )

    run_config = BacktestRunConfig(
        engine=BacktestEngineConfig(
            strategies=[strategy_config],
            logging=LoggingConfig(log_level="ERROR"),
        ),
        data=[data_config],
        venues=[venue_config],
    )

    # 6. Run
    node = BacktestNode(configs=[run_config])
    result = node.run()
    """

if __name__ == "__main__":
    main()
