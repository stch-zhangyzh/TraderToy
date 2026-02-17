# Source: https://nautilustrader.io/docs/latest/getting_started/backtest_low_level

from decimal import Decimal
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.engine import BacktestEngineConfig
from nautilus_trader.model import BarType
from nautilus_trader.model import Money
from nautilus_trader.model import TraderId
from nautilus_trader.model import Venue
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import OmsType
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.test_kit.providers import TestInstrumentProvider

# Import our strategy directly
from strategies.definitions import EMACrossStrategy, EMACrossConfig

def main():
    print("=== NautilusTrader Low-Level API Backtest ===")
    print("This example demonstrates using the BacktestEngine (Low-Level API)")
    print("to manually configure and run a backtest.")

    # 1. Initialize Engine
    # Manually create the engine config and instance
    config = BacktestEngineConfig(trader_id=TraderId("BACKTESTER-001"))
    engine = BacktestEngine(config=config)

    # 2. Add Venue
    # Manually configure and add the venue to the engine
    SIM = Venue("SIM")
    engine.add_venue(
        venue=SIM,
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USD,
        starting_balances=[Money(1_000_000.0, USD)],
    )

    # 3. Add Instrument
    # Load instrument from catalog (or create manually)
    project_root = Path(__file__).parent.parent
    catalog_path = project_root / "catalog"
    if not catalog_path.exists():
        print("Error: Catalog not found. Please run setup_data.py first.")
        return

    catalog = ParquetDataCatalog(str(catalog_path))
    instruments = catalog.instruments()
    
    if not instruments:
        print("Error: No instruments found in catalog.")
        return

    instrument = instruments[0]
    print(f"Adding instrument: {instrument.id}")
    engine.add_instrument(instrument)

    # 4. Add Data
    # Manually load data and add to engine
    # In low-level API, we are responsible for feeding data to the engine
    print("Loading data from catalog...")
    # Note: We load all available ticks for the instrument
    # In a real scenario, you might want to stream or chunk this
    ticks = catalog.quote_ticks(instrument_ids=[instrument.id])
    print(f"Loaded {len(ticks)} ticks.")
    
    engine.add_data(ticks)

    # 5. Add Strategy
    # Manually instantiate and add the strategy
    print("Configuring strategy...")
    strategy_config = EMACrossConfig(
        instrument_id=instrument.id,
        fast_period=10,
        slow_period=20,
        trade_size=10_000,
    )
    strategy = EMACrossStrategy(config=strategy_config)
    
    engine.add_strategy(strategy=strategy)

    # 6. Run Backtest
    print("\nRunning backtest...")
    engine.run()
    print("Backtest complete.")

    # 7. Analyze Results
    # Directly access reports from the engine's trader
    account = engine.trader.generate_account_report(SIM)
    positions = engine.trader.generate_positions_report()
    
    print("\nTotal Positions:", len(positions))
    if not positions.empty:
         print(f"Total PnL: {positions['realized_pnl'].apply(lambda x: float(str(x).split()[0])).sum()} USD")

    print("\nFinal Account Balance:")
    print(account.tail(1).to_string())

if __name__ == "__main__":
    main()
