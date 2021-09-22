# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# isort: skip_file
# --- Do not remove these libs ---
from functools import reduce
from typing import Any, Callable, Dict, List

import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from freqtrade.optimize.space import Categorical, Dimension, Integer, SKDecimal, Real  # noqa

from freqtrade.optimize.hyperopt_interface import IHyperOpt

# --------------------------------
# Add your lib to import here
import talib.abstract as ta  # noqa
import freqtrade.vendor.qtpylib.indicators as qtpylib


class BBRSIOPT(IHyperOpt):
    """
    This is a sample hyperopt to inspire you.
    Feel free to customize it.

    More information in the documentation: https://www.freqtrade.io/en/latest/hyperopt/

    You should:
    - Rename the class name to some unique name.
    - Add any methods you want to build your hyperopt.
    - Add any lib you need to build your hyperopt.

    You must keep:
    - The prototypes for the methods: populate_indicators, indicator_space, buy_strategy_generator.

    The methods roi_space, generate_roi_table and stoploss_space are not required
    and are provided by default.
    However, you may override them if you need the
    'roi' and the 'stoploss' spaces that differ from the defaults offered by Freqtrade.

    This sample illustrates how to override these methods.
    """
    @staticmethod
    def populate_indicators(dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        This method can also be loaded from the strategy, if it doesn't exist in the hyperopt class.
        """
        dataframe['rsi'] = ta.RSI(dataframe)
        dataframe['wr'] = ta.WILLR(dataframe)
        
        # Bollinger bands
        bollinger_1 = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=1)
        dataframe['bb_lowerband_1'] = bollinger_1['lower']
        dataframe['bb_middleband_1'] = bollinger_1['mid']
        dataframe['bb_upperband_1'] = bollinger_1['upper']

        bollinger_2 = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband_2'] = bollinger_2['lower']
        dataframe['bb_middleband_2'] = bollinger_2['mid']
        dataframe['bb_upperband_2'] = bollinger_2['upper']

        bollinger_3 = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=3)
        dataframe['bb_lowerband_3'] = bollinger_3['lower']
        dataframe['bb_middleband_3'] = bollinger_3['mid']
        dataframe['bb_upperband_3'] = bollinger_3['upper']

        return dataframe

    @staticmethod
    def indicator_space() -> List[Dimension]:
        """
        Define your Hyperopt space for searching buy strategy parameters.
        """
        return [
            Integer(5, 40, name='rsi-value'),
            Integer(-100, -70, name='wr-value'),
            Categorical([True, False], name='rsi-enabled'),
            Categorical([True, False], name='wr-enabled'),
            Categorical(['bb_lower_1', 'bb_lower_2', 'bb_lower_3'], name='trigger')
        ]

    @staticmethod
    def buy_strategy_generator(params: Dict[str, Any]) -> Callable:
        """
        Define the buy strategy parameters to be used by hyperopt
        """
        def populate_buy_trend(dataframe: DataFrame, metadata: dict) -> DataFrame:
            """
            Buy strategy Hyperopt will build and use
            """
            conditions = []
            # GUARDS AND TRENDS
            if 'rsi-enabled' in params and params['rsi-enabled']:
                    conditions.append(dataframe['rsi'] <= params['rsi-value'])
            if 'wr-enabled' in params and params['wr-enabled']:
                    conditions.append(dataframe['wr'] <= params['wr-value'])
            

            # TRIGGERS
            if 'trigger' in params:
                if params['trigger'] == 'bb_lower_1':
                    conditions.append(dataframe['close'] < dataframe['bb_lowerband_1'])
                if params['trigger'] == 'bb_lower_2':
                    conditions.append(dataframe['close'] < dataframe['bb_lowerband_2'])
                if params['trigger'] == 'bb_lower_3':
                    conditions.append(dataframe['close'] < dataframe['bb_lowerband_3'])
            
            if conditions:
                dataframe.loc[
                    reduce(lambda x, y: x & y, conditions),
                    'buy'] = 1

            return dataframe

        return populate_buy_trend

    @staticmethod
    def sell_indicator_space() -> List[Dimension]:
        """
        Define your Hyperopt space for searching sell strategy parameters.
        """
        return [
            Integer(-30, 0, name='sell-wr-value'),
            Categorical([True, False], name='sell-wr-enabled'),
            Categorical(['sell-bb_lower_2',
                         'sell-bb_lower_1',
                         'sell-bb_middle_1'], name='sell-trigger')
        ]

    @staticmethod
    def sell_strategy_generator(params: Dict[str, Any]) -> Callable:
        """
        Define the sell strategy parameters to be used by hyperopt
        """
        def populate_sell_trend(dataframe: DataFrame, metadata: dict) -> DataFrame:
            """
            Sell strategy Hyperopt will build and use
            """
            # print(params)
            conditions = []
            # GUARDS AND TRENDS
            if 'sell-wr-enabled' in params and params['sell-wr-enabled']:
                    conditions.append(dataframe['wr'] >= params['sell-wr-value'])

            # TRIGGERS
            if 'sell-trigger' in params:
                if params['sell-trigger'] == 'sell-bb_middle_1':
                    conditions.append(dataframe['close'] > dataframe['bb_middleband_1'])
                if params['sell-trigger'] == 'sell-bb_lower_1':
                    conditions.append(dataframe['close'] > dataframe['bb_lowerband_1'])
                if params['sell-trigger'] == 'sell-bb_lower_2':
                    conditions.append(dataframe['close'] > dataframe['bb_lowerband_2'])
                

            if conditions:
                dataframe.loc[
                    reduce(lambda x, y: x & y, conditions),
                    'sell'] = 1

            return dataframe

        return populate_sell_trend

    @staticmethod
    def generate_roi_table(params: Dict) -> Dict[int, float]:
        """
        Generate the ROI table that will be used by Hyperopt

        This implementation generates the default legacy Freqtrade ROI tables.

        Change it if you need different number of steps in the generated
        ROI tables or other structure of the ROI tables.

        Please keep it aligned with parameters in the 'roi' optimization
        hyperspace defined by the roi_space method.
        """
        roi_table = {}
        roi_table[0] = params['roi_p1'] + params['roi_p2'] + params['roi_p3']
        roi_table[params['roi_t3']] = params['roi_p1'] + params['roi_p2']
        roi_table[params['roi_t3'] + params['roi_t2']] = params['roi_p1']
        roi_table[params['roi_t3'] + params['roi_t2'] + params['roi_t1']] = 0

        return roi_table

    @staticmethod
    def roi_space() -> List[Dimension]:
        """
        Values to search for each ROI steps

        Override it if you need some different ranges for the parameters in the
        'roi' optimization hyperspace.

        Please keep it aligned with the implementation of the
        generate_roi_table method.
        """
        return [
            Integer(10, 120, name='roi_t1'),
            Integer(10, 60, name='roi_t2'),
            Integer(10, 40, name='roi_t3'),
            SKDecimal(0.01, 0.04, decimals=3, name='roi_p1'),
            SKDecimal(0.01, 0.07, decimals=3, name='roi_p2'),
            SKDecimal(0.01, 0.20, decimals=3, name='roi_p3'),
        ]

    @staticmethod
    def stoploss_space() -> List[Dimension]:
        """
        Stoploss Value to search

        Override it if you need some different range for the parameter in the
        'stoploss' optimization hyperspace.
        """
        return [
            SKDecimal(-0.35, -0.02, decimals=3, name='stoploss'),
        ]

    @staticmethod
    def trailing_space() -> List[Dimension]:
        """
        Create a trailing stoploss space.

        You may override it in your custom Hyperopt class.
        """
        return [
            # It was decided to always set trailing_stop is to True if the 'trailing' hyperspace
            # is used. Otherwise hyperopt will vary other parameters that won't have effect if
            # trailing_stop is set False.
            # This parameter is included into the hyperspace dimensions rather than assigning
            # it explicitly in the code in order to have it printed in the results along with
            # other 'trailing' hyperspace parameters.
            Categorical([True], name='trailing_stop'),

            SKDecimal(0.01, 0.35, decimals=3, name='trailing_stop_positive'),

            # 'trailing_stop_positive_offset' should be greater than 'trailing_stop_positive',
            # so this intermediate parameter is used as the value of the difference between
            # them. The value of the 'trailing_stop_positive_offset' is constructed in the
            # generate_trailing_params() method.
            # This is similar to the hyperspace dimensions used for constructing the ROI tables.
            SKDecimal(0.001, 0.1, decimals=3, name='trailing_stop_positive_offset_p1'),

            Categorical([True, False], name='trailing_only_offset_is_reached'),
        ]
