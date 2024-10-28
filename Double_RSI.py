import math
import pandas as pd
import yfinance as yf
from TradeMaster.backtesting import Backtest, Strategy
from TradeMaster.test import GOOG, EURUSD
from TradeMaster.trade_management.atr_tm import ATR_RR_TradeManagement
from TradeMaster.risk_management.equal_weigh_rm import EqualRiskManagement
import talib


class DoubleRSI(Strategy):
    risk_reward_ratio = 1.5
    atr_multiplier = 3
    initial_risk_per_trade = 0.01
    
    rsi_period = 14
    father_rsi_period = 19
    overbought = 70
    oversold = 30
    # persistence = 3

    def init(self):
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.rsi_father = self.I(talib.RSI, self.data.Close, timeperiod=self.father_rsi_period)

        self.trade_management_strategy = ATR_RR_TradeManagement(self.atr_multiplier, self.risk_reward_ratio)
        self.risk_management_strategy = EqualRiskManagement(initial_risk_per_trade=self.initial_risk_per_trade, initial_capital=self._broker._cash)
        self.total_trades = len(self.closed_trades)
        
    def next(self):
        rsi = self.rsi[-1]
        rsi_father = self.rsi_father[-1]

        # Check for a buy signal
        if rsi < self.oversold and rsi_father < self.oversold:
            if not self.position:
                self.add_buy_trade()

        # Check for a sell signal
        elif rsi > self.overbought and rsi_father > self.overbought:
            if self.position:
                self.position.close()
                
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

    
bt = Backtest(df, DoubleRSI, cash=100000, commission=.002)
stats = bt.run()
print(stats)
bt.plot()
# bt.tear_sheet()