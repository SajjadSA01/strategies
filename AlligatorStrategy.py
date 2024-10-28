'''
Strategy by Sajjad
'''

import math
import pandas as pd
import yfinance as yf
from TradeMaster.backtesting import Backtest, Strategy
from backtesting.lib import crossover
from TradeMaster.test import GOOG, EURUSD
from TradeMaster.trade_management.atr_tm import ATR_RR_TradeManagement
from TradeMaster.risk_management.equal_weigh_rm import EqualRiskManagement
import talib as ta

class AlligatorIndicator(Strategy):
    risk_reward_ratio = 1.5
    atr_multiplier = 3
    initial_risk_per_trade = 0.01
    
    sma1_window, sma1_lag = 5, 3
    sma2_window, sma2_lag = 8, 5
    sma3_window, sma3_lag = 13, 8
    ema_window = 200

    def init(self):
        self.sma1 = self.I(ta.SMA, self.data.Close, timeperiod=self.sma1_window)
        self.sma2 = self.I(ta.SMA, self.data.Close, timeperiod=self.sma1_window)
        self.sma3 = self.I(ta.SMA, self.data.Close, timeperiod=self.sma1_window)
        self.ema = self.I(ta.EMA, self.data.Close, timeperiod=self.ema_window)

        self.trade_management_strategy = ATR_RR_TradeManagement(self.atr_multiplier, self.risk_reward_ratio)
        self.risk_management_strategy = EqualRiskManagement(initial_risk_per_trade=self.initial_risk_per_trade, initial_capital=self._broker._cash)
        self.total_trades = len(self.closed_trades)

    def next(self):
        self.on_trade_close()
        
        close = self.data.Close[-1]
        high = self.data.High[-1]
        low = self.data.Low[-1]
        sma1 = self.sma1[-self.sma1_lag]
        sma2 = self.sma2[-self.sma2_lag]
        sma3 = self.sma3[-self.sma3_lag]
        ema = self.ema[-1]
        
        if sma1 < sma2 < sma3 and ema < low:
            if self.position.is_short:
                self.position.close()
            if not self.position:
                self.add_buy_trade()

        if sma1 > sma2 > sma3 and ema > high:
            if self.position.is_long:
                self.position.close
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


bt = Backtest(GOOG, AlligatorIndicator, cash=100000, commission=.002)
stats = bt.run()
bt.plot()
# bt.tear_sheet()
print(stats)
