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
from nautilus_trader.model import Bar
from nautilus_trader.model import BarType, BarSpecification
from nautilus_trader.model import Venue
from nautilus_trader.model.enums import PriceType, BarAggregation
from nautilus_trader.persistence.catalog import ParquetDataCatalog

def main():
    print("=== NautilusTrader A-share Bar Backtest ===")
    
    # 1. Load Catalog
    project_root = Path(__file__).parent.parent
    catalog_path = project_root / "catalog_ashare"
    
    if not catalog_path.exists():
        print(f"Error: Catalog not found at {catalog_path}")
        print("Please run 'python data_scripts/setup_ashare_data.py' first.")
        return

    catalog = ParquetDataCatalog(str(catalog_path))
    instruments = catalog.instruments()

    if not instruments:
        print("Error: No instruments found in catalog.")
        return
    
    # Use the first instrument (e.g., Moutai 600519.SSE)
    instrument = instruments[0]
    print(f"Using instrument: {instrument.id}")

    # 2. Define BarType (Must match what was written in setup_ashare_data.py)
    # We used: BarSpecification(1, "DAY", PriceType.LAST), aggregation_source=EXTERNAL
    bar_type = BarType.from_str(f"{instrument.id}-1-DAY-LAST-EXTERNAL")
    
    # Verify we have data for this bar type
    bars = catalog.bars(instrument_ids=[instrument.id], bar_types=[bar_type])
    print(f"Found {len(bars)} bars for backtest.")
    if not bars:
        print("Error: No bars found matching criteria.")
        return

    # 3. Configure Venue
    # Configure venues dynamically based on the instruments found
    # Each venue in the instruments must have a corresponding configuration
    venue_names = {i.id.venue.value for i in instruments}
    venues = []
    
    for venue_name in venue_names:
        venues.append(BacktestVenueConfig(
            name=venue_name,
            oms_type="NETTING", # Simple netting for stock
            account_type="CASH", # Cash account
            base_currency="CNY",
            starting_balances=["10_000_000 CNY"],
        ))
    
    print(f"Configured venues: {venue_names}")

    # 4. Configure Data
    # Load data for all instruments
    data_configs = []
    for instrument in instruments:
        # Reconstruct BarType for each instrument
        bar_type = BarType.from_str(f"{instrument.id}-1-DAY-LAST-EXTERNAL")
        
        data_configs.append(BacktestDataConfig(
            catalog_path=str(catalog.path),
            data_cls=Bar,
            instrument_id=instrument.id,
        ))

    # 5. Configure Engine & Strategy
    # Create a strategy for each instrument (or one strategy managing multiple)
    # Here we create one strategy instance per instrument for simplicity
    strategies = []
    for instrument in instruments:
        # Reconstruct BarType string
        bar_type = BarType.from_str(f"{instrument.id}-1-DAY-LAST-EXTERNAL")
        
        strategies.append(ImportableStrategyConfig(
            strategy_path="strategies.definitions:EMACrossBarStrategy",
            config_path="strategies.definitions:EMACrossBarConfig",
            config={
                "instrument_id": instrument.id,
                "bar_type": str(bar_type),
                "fast_period": 5,
                "slow_period": 20,
                "trade_size": 100, # 1 lot
            },
        ))

    engine = BacktestEngineConfig(
        strategies=strategies,
        logging=LoggingConfig(log_level="ERROR"),
    )

    # 6. Run Config
    run_config = BacktestRunConfig(
        engine=engine,
        venues=venues,
        data=data_configs,
    )

    # 7. Run Backtest
    print("\nStarting backtest...")
    node = BacktestNode(configs=[run_config])
    results = node.run()
    print("Backtest complete.")

    # 8. Analysis
    engine_instance = node.get_engine(run_config.id)
    
    for venue_name in venue_names:
        print(f"\n=== PERFORMANCE ({venue_name}) ===")
        # Wrap venue_name string in Venue object
        venue = Venue(venue_name)
        account = engine_instance.trader.generate_account_report(venue)
        print("\n=== FINAL ACCOUNT STATE ===")
        print(account.tail(1).to_string())

    positions = engine_instance.trader.generate_positions_report()
    
    print("\n=== OVERALL POSITIONS ===")
    print(f"Total Positions: {len(positions)}")
    
    if not positions.empty:
        # Simple PnL sum (check column name, might be 'realized_pnl' object)
        total_pnl = 0
        for pnl in positions['realized_pnl']:
            # PnL is a Money object, convert to float if needed
            total_pnl += float(str(pnl).split()[0])
        print(f"Total Realized PnL: {total_pnl:.2f} CNY")


if __name__ == "__main__":
    main()
