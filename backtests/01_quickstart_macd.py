# Source: https://nautilustrader.io/docs/latest/getting_started/quickstart

from pathlib import Path
import sys

# Add project root to path to allow importing strategies
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
    # Load the catalog from project root
    project_root = Path(__file__).parent.parent
    catalog_path = project_root / "catalog"
    
    if not catalog_path.exists():
        print(f"Error: Catalog not found at {catalog_path}")
        print("Please run 'python data_scripts/setup_sample_data.py' first.")
        return

    catalog = ParquetDataCatalog(str(catalog_path))
    instruments = catalog.instruments()

    print(f"Loaded catalog from: {catalog_path}")
    print(f"Available instruments: {[str(i.id) for i in instruments]}")

    if instruments:
        print(f"\nUsing instrument: {instruments[0].id}")
    else:
        print("\nNo instruments found. Please run setup_data.py first.")
        return

    # Configure Venue
    venue = BacktestVenueConfig(
        name="SIM",
        oms_type="NETTING",
        account_type="MARGIN",
        base_currency="USD",
        starting_balances=["1_000_000 USD"],
    )

    # Configure Data
    data = BacktestDataConfig(
        catalog_path=str(catalog.path),
        data_cls=QuoteTick,
        instrument_id=instruments[0].id,
        end_time="2020-01-10",
    )

    # Configure Engine
    # Update strategy path to point to the new location: strategies.definitions
    engine = BacktestEngineConfig(
        strategies=[
            ImportableStrategyConfig(
                strategy_path="strategies.definitions:MACDStrategy",
                config_path="strategies.definitions:MACDConfig",
                config={
                    "instrument_id": instruments[0].id,
                    "fast_period": 12,
                    "slow_period": 26,
                },
            )
        ],
        logging=LoggingConfig(log_level="ERROR"),
    )

    # Run Config
    config = BacktestRunConfig(
        engine=engine,
        venues=[venue],
        data=[data],
    )

    # Run Backtest
    print("\nStarting backtest...")
    node = BacktestNode(configs=[config])
    results = node.run()
    print("Backtest complete.")

    # Analysis
    engine_instance = node.get_engine(config.id)
    
    # Get performance statistics
    # Get the account and positions
    account = engine_instance.trader.generate_account_report(Venue("SIM"))
    positions = engine_instance.trader.generate_positions_report()
    orders = engine_instance.trader.generate_order_fills_report()

    # Print summary statistics
    print("\n=== STRATEGY PERFORMANCE ===")
    print(f"Total Orders: {len(orders)}")
    print(f"Total Positions: {len(positions)}")

    if len(positions) > 0:
        # Convert P&L strings to numeric values
        positions["pnl_numeric"] = positions["realized_pnl"].apply(
            lambda x: float(str(x).replace(" USD", "").replace(",", ""))
            if isinstance(x, str)
            else float(x)
        )

        # Calculate win rate
        winning_trades = positions[positions["pnl_numeric"] > 0]
        losing_trades = positions[positions["pnl_numeric"] < 0]
        win_rate = len(winning_trades) / len(positions) * 100 if len(positions) > 0 else 0

        print(f"\nWin Rate: {win_rate:.1f}%")
        print(f"Winning Trades: {len(winning_trades)}")
        print(f"Losing Trades: {len(losing_trades)}")

        # Calculate returns
        total_pnl = positions["pnl_numeric"].sum()
        avg_pnl = positions["pnl_numeric"].mean()
        max_win = positions["pnl_numeric"].max()
        max_loss = positions["pnl_numeric"].min()

        print(f"\nTotal P&L: {total_pnl:.2f} USD")
        print(f"Average P&L: {avg_pnl:.2f} USD")
        print(f"Best Trade: {max_win:.2f} USD")
        print(f"Worst Trade: {max_loss:.2f} USD")

        # Calculate risk metrics if we have both wins and losses
        if len(winning_trades) > 0 and len(losing_trades) > 0:
            avg_win = winning_trades["pnl_numeric"].mean()
            avg_loss = abs(losing_trades["pnl_numeric"].mean())
            profit_factor = winning_trades["pnl_numeric"].sum() / abs(
                losing_trades["pnl_numeric"].sum()
            )

            print(f"\nAverage Win: {avg_win:.2f} USD")
            print(f"Average Loss: {avg_loss:.2f} USD")
            print(f"Profit Factor: {profit_factor:.2f}")
            print(f"Risk/Reward Ratio: {avg_win / avg_loss:.2f}")

    else:
        print("\nNo positions generated. Check strategy parameters.")

    print("\n=== FINAL ACCOUNT STATE ===")
    print(account.tail(1).to_string())


if __name__ == "__main__":
    main()
