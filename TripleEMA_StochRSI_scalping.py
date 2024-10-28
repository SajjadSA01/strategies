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

class TradePro_StochRSI_EMA(Strategy):
    ema1, ema2, ema3 = 8, 14, 50

    risk_reward_ratio = 2/3
    atr_multiplier = 3
    initial_risk_per_trade = 0.01

    def init(self):
        close = self.data.Close
        self.stoch_k, self.stoch_d = self.I(ta.STOCHRSI, pd.Series(close))
        self.EMA_1 = self.I(ta.EMA, pd.Series(close), timeperiod=self.ema1)
        self.EMA_2 = self.I(ta.EMA, pd.Series(close), timeperiod=self.ema2)
        self.EMA_3 = self.I(ta.EMA, pd.Series(close), timeperiod=self.ema3)

        self.trade_management_strategy = ATR_RR_TradeManagement(self.atr_multiplier, self.risk_reward_ratio)
        self.risk_management_strategy = EqualRiskManagement(initial_risk_per_trade=self.initial_risk_per_trade, initial_capital=self._broker._cash)
        self.total_trades = len(self.closed_trades)

    def next(self):
        self.on_trade_close()
        price = self.data.Close[-1]
        if (crossover(self.stoch_k, self.stoch_d) and 
            self.EMA_1[-1] > self.EMA_2[-1] and 
            self.EMA_2[-1] > self.EMA_3[-1]):
            if self.position.is_short:
                self.position.close()
            if not self.position:
                self.add_buy_trade()
        if (crossover(self.stoch_d, self.stoch_k) and 
            self.EMA_1[-1] < self.EMA_2[-1] and 
            self.EMA_2[-1] < self.EMA_3[-1]):
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


bt = Backtest(GOOG, TradePro_StochRSI_EMA, cash=100000, commission=.002)
stats = bt.run()
bt.plot()
# bt.tear_sheet()
print(stats)