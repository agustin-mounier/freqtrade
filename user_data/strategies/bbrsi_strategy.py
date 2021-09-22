# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement

import talib.abstract as ta
import numpy as np
from pandas import Series, DataFrame

import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy.interface import IStrategy

"""
  minimal_roi = {
        "0": 0.265,
        "31": 0.072,
        "91": 0.018,
        "197": 0
    }

    # Optimal stoploss designed for the strategy
    stoploss = -0.333


 dataframe.loc[
            (
                (dataframe['rsi'] <= 29) &
                (dataframe['close'] <= dataframe['bb_lowerband_1'])
                
            ),
            'buy'] = 1

dataframe.loc[
            (
                (dataframe['close'] >= dataframe['bb_lowerband_1'])
            ),
            'sell'] = 1
"""


class BBRSI(IStrategy):
    """
    Default Strategy provided by freqtrade bot.
    Please do not modify this strategy, it's  intended for internal use only.
    Please look at the SampleStrategy in the user_data/strategy directory
    or strategy repository https://github.com/freqtrade/freqtrade-strategies
    for samples and inspiration.
    """
    INTERFACE_VERSION = 2

    # Minimal ROI designed for the strategy
    minimal_roi = {
        "0": 0.094,
        "20": 0.071,
        "43": 0.015,
        "133": 0
    }

    # Optimal stoploss designed for the strategy
    stoploss = -0.331

    # Optimal timeframe for the strategy
    timeframe = '15m'

    # Optional order type mapping
    order_types = {
        'buy': 'limit',
        'sell': 'limit',
        'stoploss': 'limit',
        'stoploss_on_exchange': False
    }

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 20

    # Optional time in force for orders
    order_time_in_force = {
        'buy': 'gtc',
        'sell': 'gtc',
    }

    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        These pair/interval combinations are non-tradeable, unless they are part
        of the whitelist as well.
        For more information, please consult the documentation
        :return: List of tuples in the format (pair, interval)
            Sample: return [("ETH/USDT", "5m"),
                            ("BTC/USDT", "15m"),
                            ]
        """
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different TA indicators to the given DataFrame

        Performance Note: For the best performance be frugal on the number of indicators
        you are using. Let uncomment only the indicator you are using in your strategies
        or your hyperopt configuration, otherwise you will waste your memory and CPU usage.
        :param dataframe: Dataframe with data from the exchange
        :param metadata: Additional information, like the currently traded pair
        :return: a Dataframe with all mandatory indicators for the strategies
        """

        # RSI
        dataframe['rsi'] = ta.RSI(dataframe)

        # William R
        dataframe['wr'] = ta.WILLR(dataframe)

        typical_price = qtpylib.typical_price(dataframe)

        # Bollinger bands
        bollinger_1 = qtpylib.bollinger_bands(typical_price, window=20, stds=1)
        dataframe['bb_lowerband_1'] = bollinger_1['lower']
        dataframe['bb_middleband_1'] = bollinger_1['mid']
        dataframe['bb_upperband_1'] = bollinger_1['upper']

        bollinger_2 = qtpylib.bollinger_bands(typical_price, window=20, stds=2)
        dataframe['bb_lowerband_2'] = bollinger_2['lower']
        dataframe['bb_middleband_2'] = bollinger_2['mid']
        dataframe['bb_upperband_2'] = bollinger_2['upper']

        bollinger_3 = qtpylib.bollinger_bands(typical_price, window=20, stds=3)
        dataframe['bb_lowerband_3'] = bollinger_3['lower']
        dataframe['bb_middleband_3'] = bollinger_3['mid']
        dataframe['bb_upperband_3'] = bollinger_3['upper']

        return dataframe




    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                (dataframe['rsi'] <= 31) &
                (dataframe['wr'] <= -74) &
                (dataframe['close'] <= dataframe['bb_lowerband_1'])
                
            ),
            'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the sell signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                (dataframe['close'] >= dataframe['bb_lowerband_2'])
            ),
            'sell'] = 1
        return dataframe
