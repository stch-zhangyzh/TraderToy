# Source: https://nautilustrader.io/docs/latest/tutorials/backtest_fx_bars

from decimal import Decimal
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.engine import BacktestEngineConfig
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import RiskEngineConfig
from nautilus_trader.model import BarType
from nautilus_trader.model import Money
from nautilus_trader.model import Venue
from nautilus_trader.model.currencies import JPY
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import OmsType
from nautilus_trader.persistence.wranglers import QuoteTickDataWrangler
from nautilus_trader.test_kit.providers import TestDataProvider
from nautilus_trader.test_kit.providers import TestInstrumentProvider

# Reuse our existing EMACrossStrategy
from strategies.definitions import EMACrossStrategy, EMACrossConfig


def main():
    print("=== NautilusTrader FX Bar Data Backtest ===")
    print("This example demonstrates backtesting with FX Bar (Candle) data.")
    print("Note: This example uses synthetic/test data included with nautilus_trader.")

    # 1. Initialize Engine Config
    config = BacktestEngineConfig(
        trader_id="BACKTESTER-FX-BARS",
        logging=LoggingConfig(log_level="ERROR"),
        risk_engine=RiskEngineConfig(
            bypass=True,  # Bypass pre-trade risk checks for faster backtesting
        ),
    )
    engine = BacktestEngine(config=config)

    # 2. Configure Venue & Fill Model
    # A probabilistic fill model simulates slippage and partial fills
    fill_model = FillModel(
        prob_fill_on_limit=0.2,
        prob_fill_on_stop=0.95,
        prob_slippage=0.5,
        random_seed=42,
    )

    SIM = Venue("SIM")
    engine.add_venue(
        venue=SIM,
        oms_type=OmsType.HEDGING,  # Hedging allows concurrent long/short positions
        account_type=AccountType.MARGIN,
        base_currency=None,  # Multi-currency account
        starting_balances=[Money(1_000_000, USD), Money(10_000_000, JPY)],
        fill_model=fill_model,
        # modules=[fx_rollover_interest], # Can add rollover interest module here
    )

    # 3. Add Instrument
    USDJPY_SIM = TestInstrumentProvider.default_fx_ccy("USD/JPY", SIM)
    engine.add_instrument(USDJPY_SIM)

    # 4. Load & Wrangle Data
    # We use TestDataProvider to get built-in sample CSVs
    print("Loading FX bar data...")
    provider = TestDataProvider()
    
    # In a real scenario, you would provide paths to your own CSV files
    # The wrangler converts Bar data (Open/High/Low/Close) into QuoteTicks
    # because the engine is event-driven by Ticks.
    wrangler = QuoteTickDataWrangler(instrument=USDJPY_SIM)
    ticks = wrangler.process_bar_data(
        bid_data=provider.read_csv_bars("fxcm/usdjpy-m1-bid-2013.csv"),
        ask_data=provider.read_csv_bars("fxcm/usdjpy-m1-ask-2013.csv"),
    )
    print(f"Processed {len(ticks)} ticks from bar data.")
    engine.add_data(ticks)

    # 5. Configure Strategy
    # Note: bar_type string must match the data resolution if using bars for signals
    # Here we are just using the ticks generated from bars
    strategy_config = EMACrossConfig(
        instrument_id=USDJPY_SIM.id,
        fast_period=10,
        slow_period=20,
        trade_size=1_000_000,
    )
    strategy = EMACrossStrategy(config=strategy_config)
    engine.add_strategy(strategy=strategy)

    # 6. Run Backtest
    print("\nRunning backtest...")
    engine.run()
    print("Backtest complete.")

    # 7. Analysis
    print("\n=== Results ===")
    account_report = engine.trader.generate_account_report(SIM)
    print(account_report.tail(1).to_string())
    
    positions = engine.trader.generate_positions_report()
    print(f"\nTotal Positions: {len(positions)}")

if __name__ == "__main__":
    main()
