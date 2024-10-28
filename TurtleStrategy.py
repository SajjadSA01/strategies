'''
Strategy By Sajjad
'''

import math
import pandas as pd
import yfinance as yf
from TradeMaster.backtesting import Backtest, Strategy
from TradeMaster.test import GOOG, EURUSD
from TradeMaster.trade_management.atr_tm import ATR_RR_TradeManagement
from TradeMaster.risk_management.equal_weigh_rm import EqualRiskManagement
import talib

def rolling_max(data, window):
    return pd.Series(data).rolling(window).max()

def rolling_min(data, window):
    return pd.Series(data).rolling(window).min()

class TurtleStrategy(Strategy):
    risk_reward_ratio = 1.5
    atr_multiplier = 3
    initial_risk_per_trade = 0.01

    rolling_high = 200
    rolling_low = 10
    def init(self):
        self.high_200 = self.I(rolling_max, self.data.High, self.rolling_high)
        self.low_10 = self.I(rolling_min, self.data.Low, self.rolling_low)

        self.trade_management_strategy = ATR_RR_TradeManagement(self.atr_multiplier, self.risk_reward_ratio)
        self.risk_management_strategy = EqualRiskManagement(initial_risk_per_trade=self.initial_risk_per_trade, initial_capital=self._broker._cash)
        self.total_trades = len(self.closed_trades)
        
    def next(self):
        self.on_trade_close()
        if self.data.High[-1] >= self.high_200[-1]:
            if self.position.is_short:
                self.position.close()
            if not self.position:
                self.add_buy_trade()
        if self.data.Low[-1] <= self.low_10[-1]:
            if self.position.is_long:
                self.position.close()
            if not self.position:
                self.add_sell_trade()

    def add_buy_trade(self):
        risk_per_trade = self.risk_management_strategy.get_risk_per_trade(self._broker._cash)
        entry = self.data.Close[-1]
        if risk_per_trade > 0:
            stop_loss, take_profit = self.trade_management_strategy.calculate_tp_sl(df=self.data.df, direction="buy")
            stop_loss_perc = (entry - stop_loss) / entry
            trade_size = risk_per_trade / stop_loss_perc
            qty = math.ceil(trade_size / self.data.Close[-1])
            self.buy(size=qty, sl=stop_loss, tp=take_profit)

    def add_sell_trade(self):
        risk_per_trade = self.risk_management_strategy.get_risk_per_trade(self._broker._cash)
        entry = self.data.Close[-1]
        if risk_per_trade > 0:
            stop_loss, take_profit = self.trade_management_strategy.calculate_tp_sl(df=self.data.df, direction="sell")
            stop_loss_perc = (stop_loss - entry) / entry
            trade_size = risk_per_trade / stop_loss_perc
            qty = math.ceil(trade_size / self.data.Close[-1])
            self.sell(size=qty, sl=stop_loss, tp=take_profit)

    def on_trade_close(self):
        num_of_trades_closed = len(self.closed_trades) - self.total_trades
        if num_of_trades_closed > 0:
            for trade in self.closed_trades[-num_of_trades_closed:]:
                if trade.pl < 0:
                    self.risk_management_strategy.update_after_loss()
                else:
                    self.risk_management_strategy.update_after_win()
        self.total_trades = len(self.closed_trades)


bt = Backtest(GOOG, TurtleStrategy, cash=10000, commission=.002)
stats = bt.run()
bt.plot()
# bt.tear_sheet()
print(stats)