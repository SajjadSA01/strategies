'''Strategy by Sajjad'''

import math
from TradeMaster.backtesting import Backtest, Strategy
from TradeMaster.test import GOOG, EURUSD
from TradeMaster.trade_management.atr_tm import ATR_RR_TradeManagement
from TradeMaster.risk_management.equal_weigh_rm import EqualRiskManagement
import talib

class MeanReversion_IBS_RollingMean(Strategy):
    risk_reward_ratio = 1.5
    atr_multiplier = 3
    initial_risk_per_trade = 0.01
    
    hl_rolling_mean_window = 25
    rolling_high_window = 10
    lowerband_multiplier = 2.5

    def init(self):
        # Calculate indicators directly using talib
        self.hl_rolling_mean = self.I(lambda: talib.SMA(self.data.High - self.data.Low, timeperiod=self.hl_rolling_mean_window), name="HL_RollingMean")
        self.ibs = self.I(lambda: (self.data.Close - self.data.Low) / (self.data.High - self.data.Low), name='IBS')
        self.rolling_high = self.I(lambda: talib.MAX(self.data.High, timeperiod=self.rolling_high_window), name='RollingHigh')
        self.lower_band = self.I(lambda: self.rolling_high - self.lowerband_multiplier * self.hl_rolling_mean, name='LowerBand')

        # Risk and Trade Management Strategies
        self.trade_management_strategy = ATR_RR_TradeManagement(self.atr_multiplier, self.risk_reward_ratio)
        self.risk_management_strategy = EqualRiskManagement(initial_risk_per_trade=self.initial_risk_per_trade, initial_capital=self._broker._cash)
        self.total_trades = len(self.closed_trades)

    def next(self):
        # Bull Market Entry (IBS < 0.3 and price below lower band)
        if self.data.Close[-1] < self.lower_band[-1] and self.ibs[-1] < 0.3:
            if not self.position:
                self.add_buy_trade()
        
        # Exit Strategy if Price Exceeds High (Mean-Reversion Exit)
        elif self.data.Close[-1] > self.rolling_high[-2]:
            if self.position:
                self.position.close()

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
bt = Backtest(GOOG, MeanReversion_IBS_RollingMean, cash=100000, commission=.002)
stats = bt.run()
bt.plot()
print(stats)
