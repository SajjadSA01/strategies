import pandas_ta as ta
from backtesting import Backtest, Strategy
from backtesting.test import GOOG
import pandas as pd

class VolatilityStopCloudStrategy(Strategy):
    atr_period_long = 20
    atr_multiplier_long = 3.0
    atr_period_short = 20
    atr_multiplier_short = 1.5

    def init(self):
        # Calculate ATR
        high = pd.Series(self.data.High)
        low = pd.Series(self.data.Low)
        close = pd.Series(self.data.Close)
        
        atr_long = ta.atr(high, low, close, length=self.atr_period_long)
        atr_short = ta.atr(high, low, close, length=self.atr_period_short)
        
        self.atr_long = self.I(lambda: atr_long, name='ATR_Long')
        self.atr_short = self.I(lambda: atr_short, name='ATR_Short')

        # Initialize VStop indicators using the ATR values
        self.vstop_long = self.I(self.volatility_stop, self.data.Close, self.atr_long, self.atr_multiplier_long)
        self.vstop_short = self.I(self.volatility_stop, self.data.Close, self.atr_short, self.atr_multiplier_short)

    def volatility_stop(self, src, atr, atr_multiplier):
        return src - (atr * atr_multiplier)

    def next(self):
        cross_up = self.vstop_short[-1] > self.vstop_long[-1] and self.vstop_short[-2] <= self.vstop_long[-2]
        cross_down = self.vstop_short[-1] < self.vstop_long[-1] and self.vstop_short[-2] >= self.vstop_long[-2]

        if cross_up:
            self.position.close()
            self.buy()
        
        if cross_down:
            self.position.close()
            self.sell()

bt = Backtest(GOOG, VolatilityStopCloudStrategy, cash=1000000, commission=.002)
stats = bt.run()
bt.plot()
