# NautilusTrader 示例项目

本项目包含使用 NautilusTrader 进行量化回测的多种示例，涵盖了从基础入门到高阶用法的完整流程。项目代码基于官方文档和教程整理，旨在帮助用户快速上手并理解核心概念。

## 📁 项目结构

*   `backtests/`: 存放所有回测示例脚本。
    *   `01_quickstart_macd.py`: 快速入门示例，MACD 策略。
    *   `02_high_level_ema.py`: 使用 High-Level API (Node) 的 EMA 策略。
    *   `03_low_level_ema.py`: 使用 Low-Level API (Engine) 的 EMA 策略。
    *   `04_fx_bars.py`: 使用 K 线 (Bar/Candle) 数据的回测示例。
    *   `05_orderbook.py`: 使用 Level 2 订单簿数据的回测模板。
    *   `06_ashare_bars.py`: A股日线数据回测示例。
*   `strategies/`: 存放策略实现代码。
    *   `definitions.py`: 定义了项目中用到的所有策略类。
*   `data_scripts/`: 数据下载与 Catalog 设置脚本。
    *   `setup_sample_data.py`: 下载 EUR/USD 样本数据并生成 Catalog。
    *   `setup_databento.py`: 从 Databento 下载并加载 L2 数据。
    *   `setup_ashare_data.py`: 使用 Ashare 下载 A股数据并生成 Catalog。
*   `catalog/`: (自动生成) 默认的数据存储目录，用于存放 Tick 和 Bar 数据。
    *   数据以 Parquet 格式存储，这是 NautilusTrader 的标准持久化格式。
*   `catalog_databento/`: (自动生成) 存放 Databento 数据的目录。
*   `catalog_ashare/`: (自动生成) 存放 A股数据的目录。

## 🛠️ 环境准备

1.  **安装依赖**:
    建议使用 Python 3.12+ 环境。
    ```bash
    pip install -r requirements.txt
    ```
    
    **当前测试通过的依赖版本**:
    *   `nautilus_trader` == 1.222.0
    *   `pandas` == 2.3.3
    *   `databento` == 0.70.0

2.  **准备数据**:
    
    **选项 A: 基础外汇数据 (必选，用于示例 01-04)**
    运行此脚本会自动下载 2020年1月的 EUR/USD Tick 数据，并将其转换为 Nautilus Catalog 格式。
    ```bash
    python data_scripts/setup_sample_data.py
    ```

    **选项 B: Databento Level 2 数据 (可选)**
    如果你有 Databento API Key，可以运行此脚本下载 CME 期货的 MBP-10 (10档深度) 数据。
    *   需要设置环境变量 `DATABENTO_API_KEY` 或在脚本中修改。
    ```bash
    python data_scripts/setup_databento.py
    ```

    **选项 C: A股历史数据 (可选)**
    使用 `Ashare` 接口下载 A股日线数据（如贵州茅台、平安银行），无需 API Key。
    ```bash
    python data_scripts/setup_ashare_data.py
    ```

## 🚀 回测示例详解

所有示例脚本均位于 `backtests/` 目录下。

### 1. 快速入门 (Quickstart)
**脚本**: `backtests/01_quickstart_macd.py`
**简介**: 这是最基础的 "Hello World" 级示例。它演示了如何加载数据、配置一个简单的 MACD 策略，并运行回测。
**核心概念**:
*   加载 `ParquetDataCatalog`。
*   配置 `MACDStrategy` (在 `strategies/definitions.py` 中定义)。
*   使用 `BacktestNode` 运行回测并打印报告。
```bash
python backtests/01_quickstart_macd.py
```

### 2. High-Level API 回测
**脚本**: `backtests/02_high_level_ema.py`
**简介**: 使用 `BacktestNode` 进行声明式配置。这是 NautilusTrader 推荐的标准回测方式。
**特点**:
*   **声明式配置**: 通过 `BacktestRunConfig` 组合 Engine、Venue 和 Data 配置。
*   **自动数据加载**: 只需指定 Catalog 路径和时间范围，Node 会自动处理数据加载。
*   **适用场景**: 参数优化、批量运行、标准策略开发。
```bash
python backtests/02_high_level_ema.py
```

### 3. Low-Level API 回测
**脚本**: `backtests/03_low_level_ema.py`
**简介**: 直接操作 `BacktestEngine`。这种方式提供了最大的灵活性，适合需要深入理解引擎内部机制或自定义数据流的场景。
**特点**:
*   **命令式配置**: 手动调用 `engine.add_venue()`, `engine.add_data()`, `engine.add_strategy()`。
*   **手动数据注入**: 需要手动将数据加载到内存并注入引擎。
*   **适用场景**: 调试、复杂的多 Venue 编排、自定义数据源。
```bash
python backtests/03_low_level_ema.py
```

### 4. K线 (Bar/Candle) 数据回测
**脚本**: `backtests/04_fx_bars.py`
**简介**: 演示如何使用 OHLC K线数据（而非 Tick 数据）进行回测。
**关键技术**:
*   **数据转换**: Nautilus 核心是事件驱动的 (Event-Driven)。使用 `QuoteTickDataWrangler.process_bar_data` 将 K线转换为 QuoteTick 事件流。
*   **填充模型 (Fill Model)**: 配置概率填充模型来模拟滑点和部分成交。
*   **风控引擎 (Risk Engine)**: 演示如何配置或绕过风控检查。
```bash
python backtests/04_fx_bars.py
```

### 5. 订单簿 (OrderBook) 数据回测
**脚本**: `backtests/05_orderbook.py`
**简介**: 一个用于回测 Level 2 (L2) 市场深度数据的模板。
**注意**: 此脚本需要较大的外部数据文件（如 Binance/Bybit 的 CSV），默认情况下仅作为代码结构演示。
**关键技术**:
*   **L2_MBP**: 处理 Market-By-Price 的订单簿数据。
*   **OrderBookDelta**: 处理增量更新 (Delta) 和快照 (Snapshot)。
```bash
python backtests/05_orderbook.py
```

### 6. A股 (A-share) 数据回测
**脚本**: `backtests/06_ashare_bars.py`
**简介**: 演示如何使用 A股日线数据进行回测。
**关键技术**:
*   **Ashare 集成**: 自动获取 A股历史行情。
*   **BarDataWrangler**: 将 Pandas DataFrame 转换为 Nautilus Bar 对象。
*   **A股策略**: 适配 A股的 Long-Only 策略逻辑。
```bash
python backtests/06_ashare_bars.py
```

## 🧠 策略说明

所有策略逻辑都集中在 `strategies/definitions.py` 文件中，方便复用和修改。

*   **`MACDStrategy`**:
    *   **逻辑**: 经典的 MACD 零轴交叉策略。
    *   **信号**: MACD 上穿零轴做多，下穿零轴做空。
    *   **特点**: 简单直接，适合测试数据流是否通畅。

*   **`EMACrossStrategy`**:
    *   **逻辑**: 双均线 (快线/慢线) 交叉策略。
    *   **信号**: 快线上穿慢线做多，下穿慢线做空。
    *   **特点**: 趋势跟踪策略的代表。

*   **`EMACrossBarStrategy`**:
    *   **逻辑**: 适用于 Bar (K线) 数据的双均线策略。
    *   **特点**: 仅做多 (Long Only)，适合股票市场回测。

*   **`MACDEnhancedStrategy`**:
    *   **逻辑**: 在 MACD 基础上增加了风险管理。
    *   **特点**: 包含 **止损 (Stop Loss)** 和 **止盈 (Take Profit)** 订单的逻辑实现。展示了如何管理挂单和仓位退出。

## 📚 参考资料

本项目代码基于 NautilusTrader 官方文档和教程：
*   [Quickstart Guide](https://nautilustrader.io/docs/latest/getting_started/quickstart)
*   [Backtest High-Level API](https://nautilustrader.io/docs/latest/getting_started/backtest_high_level)
*   [Backtest Low-Level API](https://nautilustrader.io/docs/latest/getting_started/backtest_low_level)
*   [Databento Integration](https://nautilustrader.io/docs/latest/tutorials/databento_overview)
