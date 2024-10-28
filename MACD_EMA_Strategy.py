'''
Strategy by Sajjad
'''

import math
from TradeMaster.backtesting import Backtest, Strategy
from backtesting.lib import crossover
from TradeMaster.test import GOOG
from TradeMaster.trade_management.atr_tm import ATR_RR_TradeManagement
from TradeMaster.risk_management.equal_weigh_rm import EqualRiskManagement
import talib

class MACD_EMA_Strategy(Strategy):
    risk_reward_ratio = 1.5
    atr_multiplier = 3
    initial_risk_per_trade = 0.01

    macd_fastperiod = 12
    macd_slowperiod = 26
    macd_signalperiod = 9
    ema_window = 200

    def init(self):
        self.ema = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_window)
        self.macd, self.macd_signal, _ = self.I(talib.MACD, self.data.Close, 
                                                 fastperiod=self.macd_fastperiod, 
                                                 slowperiod=self.macd_slowperiod, 
                                                 signalperiod=self.macd_signalperiod)

        self.trade_management_strategy = ATR_RR_TradeManagement(self.atr_multiplier, self.risk_reward_ratio)
        self.risk_management_strategy = EqualRiskManagement(initial_risk_per_trade=self.initial_risk_per_trade, initial_capital=self._broker._cash)
        self.total_trades = len(self.closed_trades)

    def next(self):
        self.on_trade_close()

        if self.data.Low[-1] > self.ema[-1]:  # Uptrend
            if crossover(self.macd, self.macd_signal) and self.macd[-1] < 0:
                # Buy condition: MACD crosses above the signal line and it happens below zero line
                if self.position.is_short:
                    self.position.close()
                if not self.position:
                    self.add_buy_trade()
        
        elif self.data.High[-1] < self.ema[-1]:  # Downtrend
            if crossover(self.macd_signal, self.macd) and self.macd[-1] > 0:
                # Sell condition: MACD crosses below the signal line and it happens above zero line
                if not self.position:
                    self.add_sell_trade()

    def add_buy_trade(self):
        """Add a buy trade with calculated stop-loss and take-profit."""
        risk_per_trade = self.risk_management_strategy.get_risk_per_trade(self._broker._cash)
        entry = self.data.Close[-1]
        if risk_per_trade > 0:
            stop_loss, take_profit = self.trade_management_strategy.calculate_tp_sl(df=self.data.df, direction="buy")
            stop_loss_perc = (entry - stop_loss) / entry
            trade_size = risk_per_trade / stop_loss_perc
            qty = math.ceil(trade_size / self.data.Close[-1])
            self.buy(size=qty, sl=stop_loss, tp=take_profit)

    def add_sell_trade(self):
        """Add a sell trade with calculated stop-loss and take-profit."""
        risk_per_trade = self.risk_management_strategy.get_risk_per_trade(self._broker._cash)
        entry = self.data.Close[-1]
        if risk_per_trade > 0:
            stop_loss, take_profit = self.trade_management_strategy.calculate_tp_sl(df=self.data.df, direction="sell")
            stop_loss_perc = (stop_loss - entry) / entry
            trade_size = risk_per_trade / stop_loss_perc
            qty = math.ceil(trade_size / self.data.Close[-1])
            self.sell(size=qty, sl=stop_loss, tp=take_profit)

    def on_trade_close(self):
        """Update risk management based on closed trades."""
        num_of_trades_closed = len(self.closed_trades) - self.total_trades
        if num_of_trades_closed > 0:
            for trade in self.closed_trades[-num_of_trades_closed:]:
                if trade.pl < 0:
                    self.risk_management_strategy.update_after_loss()
                else:
                    self.risk_management_strategy.update_after_win()
        self.total_trades = len(self.closed_trades)

# Running the backtest
bt = Backtest(GOOG, MACD_EMA_Strategy, cash=10000, commission=.002)
stats = bt.run()
bt.plot()
print(stats)
