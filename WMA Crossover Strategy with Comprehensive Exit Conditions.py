import pandas as pd
import pandas_ta as ta
from backtesting import Strategy, Backtest
from backtesting.test import GOOG 


class EMAWMACrossoverStrategy(Strategy):
    ema_length = 9
    wma_length = 30
    fast_macd = 12
    slow_macd = 26
    signal_smoothing = 9
    points_gain_goal = 33.00
    points_loss_goal = -50.00
    
    def init(self):
        self.df = self.data.df
        
        self.ema9 = ta.ema(self.df['Close'], length=self.ema_length)
        self.wma30 = ta.wma(self.df['Close'], length=self.wma_length)
        macd = ta.macd(self.df['Close'], fast=self.fast_macd, slow=self.slow_macd, signal=self.signal_smoothing)
        self.macd_line = macd['MACD_12_26_9']
        self.signal_line = macd['MACDs_12_26_9']
        
        # self.sma200 = ta.sma(self.df['Close'], length=200)
        # self.ema21 = ta.ema(self.df['Close'], length=21)
        # self.vwap = ta.vwap(self.df['High'], self.df['Low'], self.df['Close'], self.df['Volume'])

        self.entry_price = None
        self.below_ema9_count = 0
        self.below_wma30_count = 0
    
    def next(self):
        close_price = self.data.Close[-1]
        
        crossover = self.ema9[-1] > self.wma30[-1] and self.ema9[-2] <= self.wma30[-2]
        macd_confirmation = self.macd_line[-1] > self.signal_line[-1]
        buy_signal = crossover and macd_confirmation
        
        if buy_signal:
            self.buy()
            self.entry_price = close_price
        
        if close_price < self.ema9[-1]:
            self.below_ema9_count += 1
        else:
            self.below_ema9_count = 0
            
        if close_price < self.wma30[-1]:
            self.below_wma30_count += 1
        else:
            self.below_wma30_count = 0
        
        macd_bearish_cross = self.macd_line[-1] < self.signal_line[-1]
        exit_condition1 = self.below_ema9_count >= 2 and self.below_wma30_count >= 1
        exit_condition2 = macd_bearish_cross
        
        if self.position and (exit_condition1 or exit_condition2):
            self.sell()
            self.entry_price = None
            self.below_ema9_count = 0
            self.below_wma30_count = 0



# Run backtest
bt = Backtest(GOOG, EMAWMACrossoverStrategy, cash=10000, commission=.002)
stats = bt.run()
print(stats)
bt.plot()
