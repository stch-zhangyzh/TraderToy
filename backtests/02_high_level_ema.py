# Source: https://nautilustrader.io/docs/latest/getting_started/backtest_high_level

from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from nautilus_trader.backtest.node import BacktestDataConfig
from nautilus_trader.backtest.node import BacktestEngineConfig
from nautilus_trader.backtest.node import BacktestNode
from nautilus_trader.backtest.node import BacktestRunConfig
from nautilus_trader.backtest.node import BacktestVenueConfig
from nautilus_trader.config import ImportableStrategyConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model import QuoteTick
from nautilus_trader.model import Venue
from nautilus_trader.persistence.catalog import ParquetDataCatalog


def main():
    print("=== NautilusTrader High-Level API Backtest ===")
    print("This example demonstrates using the BacktestNode (High-Level API)")
    print("to run a backtest with configuration objects.")

    # 1. Load Data from Catalog
    project_root = Path(__file__).parent.parent
    catalog_path = project_root / "catalog"
    
    if not catalog_path.exists():
        print(f"Error: Catalog not found at {catalog_path}")
        print("Please run 'python data_scripts/setup_sample_data.py' first.")
        return

    catalog = ParquetDataCatalog(str(catalog_path))
    instruments = catalog.instruments()

    if not instruments:
        print("Error: No instruments found in catalog.")
        return
    
    instrument = instruments[0]
    print(f"Using instrument: {instrument.id}")

    # 2. Configure Venue
    # BacktestVenueConfig abstracts the venue setup
    venue = BacktestVenueConfig(
        name="SIM",
        oms_type="NETTING",
        account_type="MARGIN",
        base_currency="USD",
        starting_balances=["1_000_000 USD"],
    )

    # 3. Configure Data
    # BacktestDataConfig defines what data to load from catalog
    data = BacktestDataConfig(
        catalog_path=str(catalog.path),
        data_cls=QuoteTick,
        instrument_id=instrument.id,
        end_time="2020-01-10", # Optional: Limit data range
    )

    # 4. Configure Engine & Strategy
    # BacktestEngineConfig defines the system configuration
    # We use ImportableStrategyConfig to load our EMACrossStrategy
    # Note: Updated strategy path to strategies.definitions
    engine = BacktestEngineConfig(
        strategies=[
            ImportableStrategyConfig(
                strategy_path="strategies.definitions:EMACrossStrategy",
                config_path="strategies.definitions:EMACrossConfig",
                config={
                    "instrument_id": instrument.id,
                    "fast_period": 10,
                    "slow_period": 20,
                    "trade_size": 10_000,
                },
            )
        ],
        logging=LoggingConfig(log_level="ERROR"),
    )

    # 5. Create Run Configuration
    # BacktestRunConfig brings everything together
    run_config = BacktestRunConfig(
        engine=engine,
        venues=[venue],
        data=[data],
    )

    # 6. Run Backtest
    # BacktestNode orchestrates the run
    print("\nStarting backtest...")
    node = BacktestNode(configs=[run_config])
    results = node.run()
    print("Backtest complete.")

    # 7. Analyze Results
    engine_instance = node.get_engine(run_config.id)
    account = engine_instance.trader.generate_account_report(Venue("SIM"))
    print("\nFinal Account Balance:")
    print(account.tail(1).to_string())

if __name__ == "__main__":
    main()
