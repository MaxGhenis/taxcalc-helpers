import numpy as np
import pandas as pd
from typing import Callable, Union
from functools import wraps
import warnings


class MicroSeries(pd.Series):
    SCALAR_FUNCTIONS = ["sum", "count", "mean", "median", "gini"]

    def __init__(self, *args, weights: np.array = None, **kwargs):
        """A Series-inheriting class for weighted microdata.
        Weights can be provided at initialisation, or using set_weights.

        :param weights: Array of weights.
        :type weights: np.array
        """
        super().__init__(*args, **kwargs)
        self.set_weights(weights)

    def handles_zero_weights(fn):
        def safe_fn(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except ZeroDivisionError:
                return np.NaN

        return safe_fn

    def set_weights(self, weights: np.array) -> None:
        """Sets the weight values.

        :param weights: Array of weights.
        :type weights: np.array.
        """
        if weights is None:
            self.weights = pd.Series(np.ones_like(self.values), dtype=float)
        else:
            self.weights = pd.Series(weights, dtype=float)

    @handles_zero_weights
    def weight(self) -> pd.Series:
        """Calculates the weighted value of the MicroSeries.

        :returns: A Series multiplying the MicroSeries by its weight.
        :rtype: pd.Series
        """
        return self.multiply(self.weights)

    @handles_zero_weights
    def sum(self) -> float:
        """Calculates the weighted sum of the MicroSeries.

        :returns: The weighted sum.
        :rtype: float
        """
        return self.multiply(self.weights).sum()

    @handles_zero_weights
    def count(self) -> float:
        """Calculates the weighted count of the MicroSeries.

        :returns: The weighted count.
        """
        return self.weights.sum()

    @handles_zero_weights
    def mean(self) -> float:
        """Calculates the weighted mean of the MicroSeries

        :returns: The weighted mean.
        :rtype: float
        """
        return np.average(self.values, weights=self.weights)

    @handles_zero_weights
    def quantile(self, q: np.array) -> np.array:
        """Calculates weighted quantiles of the MicroSeries.

        Doesn't exactly match unweighted quantiles of stacked values.
        See stackoverflow.com/q/21844024#comment102342137_29677616.

        :param q: Array of quantiles to calculate.
        :type q: np.array

        :return: Array of weighted quantiles.
        :rtype: np.array
        """
        values = np.array(self.values)
        quantiles = np.array(q)
        sample_weight = np.array(self.weights)
        assert np.all(quantiles >= 0) and np.all(
            quantiles <= 1
        ), "quantiles should be in [0, 1]"
        sorter = np.argsort(values)
        values = values[sorter]
        sample_weight = sample_weight[sorter]
        weighted_quantiles = np.cumsum(sample_weight) - 0.5 * sample_weight
        weighted_quantiles /= np.sum(sample_weight)
        return np.interp(quantiles, weighted_quantiles, values)

    @handles_zero_weights
    def median(self) -> float:
        """Calculates the weighted median of the MicroSeries.

        :returns: The weighted median of a DataFrame's column.
        :rtype: float
        """
        return self.quantile(0.5)

    def gini(self, negatives: str = None) -> float:
        """Calculates Gini index.

        :param negatives: An optional string indicating how to treat negative
            values of x:
            'zero' replaces negative values with zeroes.
            'shift' subtracts the minimum value from all values of x,
            when this minimum is negative. That is, it adds the absolute
            minimum value.
            Defaults to None, which leaves negative values as they are.
        :type q: str
        :returns: Gini index.
        :rtype: float
        """
        x = np.array(self).astype("float")
        if negatives == "zero":
            x[x < 0] = 0
        if negatives == "shift" and np.amin(x) < 0:
            x -= np.amin(x)
        if (self.weights != np.ones(len(self))).any():  # Varying weights.
            sorted_indices = np.argsort(self)
            sorted_x = np.array(self[sorted_indices])
            sorted_w = np.array(self.weights[sorted_indices])
            cumw = np.cumsum(sorted_w)
            cumxw = np.cumsum(sorted_x * sorted_w)
            return np.sum(cumxw[1:] * cumw[:-1] - cumxw[:-1] * cumw[1:]) / (
                cumxw[-1] * cumw[-1]
            )
        else:
            sorted_x = np.sort(self)
            n = len(x)
            cumxw = np.cumsum(sorted_x)
            # The above formula, with all weights equal to 1 simplifies to:
            return (n + 1 - 2 * np.sum(cumxw) / cumxw[-1]) / n

    def top_x_pct_share(self, top_x_pct: float) -> float:
        """Calculates top x% share.

        :param top_x_pct: Decimal between 0 and 1 of the top %, e.g. 0.1,
            0.001.
        :type top_x_pct: float
        :returns: The weighted share held by the top x%.
        :rtype: float
        """
        threshold = self.quantile(1 - top_x_pct)
        top_x_pct_sum = self[self >= threshold].sum()
        total_sum = self.sum()
        return top_x_pct_sum / total_sum

    def bottom_x_pct_share(self, bottom_x_pct) -> float:
        """Calculates bottom x% share.

        :param bottom_x_pct: Decimal between 0 and 1 of the top %, e.g. 0.1,
            0.001.
        :type bottom_x_pct: float
        :returns: The weighted share held by the bottom x%.
        :rtype: float
        """
        return 1 - self.top_x_pct_share(1 - bottom_x_pct)

    def bottom_50_pct_share(self) -> float:
        """Calculates bottom 50% share.

        :returns: The weighted share held by the bottom 50%.
        :rtype: float
        """
        return self.bottom_x_pct_share(0.5)

    def top_50_pct_share(self) -> float:
        """Calculates top 50% share.

        :returns: The weighted share held by the top 50%.
        :rtype: float
        """
        return self.top_x_pct_share(0.5)

    def top_10_pct_share(self) -> float:
        """Calculates top 10% share.

        :returns: The weighted share held by the top 10%.
        :rtype: float
        """
        return self.top_x_pct_share(0.1)

    def top_1_pct_share(self) -> float:
        """Calculates top 1% share.

        :returns: The weighted share held by the top 50%.
        :rtype: float
        """
        return self.top_x_pct_share(0.01)

    def top_0_1_pct_share(self) -> float:
        """Calculates top 0.1% share.

        :returns: The weighted share held by the top 0.1%.
        :rtype: float
        """
        return self.top_x_pct_share(0.001)

    def t10_b50(self) -> float:
        """Calculates ratio between the top 10% and bottom 50% shares.

        :returns: The weighted share held by the top 10% divided by
            the weighted share held by the bottom 50%.

        """
        t10 = self.top_10_pct_share()
        b50 = self.bottom_50_pct_share()
        return t10 / b50

    def groupby(self, *args, **kwargs):
        gb = super().groupby(*args, **kwargs)
        gb.__class__ = MicroSeriesGroupBy
        gb.weights = pd.Series(self.weights).groupby(*args, **kwargs)
        return gb

    def __getitem__(self, key):
        result = super().__getitem__(key)
        if isinstance(result, pd.Series):
            weights = self.weights.__getitem__(key)
            return MicroSeries(result, weights=weights)
        return result

    def __getattr__(self, name):
        return MicroSeries(super().__getattr__(name), weights=self.weights)

    # operators

    def __add__(self, other):
        return MicroSeries(super().__add__(other), weights=self.weights)

    def __sub__(self, other):
        return MicroSeries(super().__sub__(other), weights=self.weights)

    def __mul__(self, other):
        return MicroSeries(super().__mul__(other), weights=self.weights)

    def __floordiv__(self, other):
        return MicroSeries(super().__floordiv__(other), weights=self.weights)

    def __truediv__(self, other):
        return MicroSeries(super().__truediv__(other), weights=self.weights)

    def __mod__(self, other):
        return MicroSeries(super().__mod__(other), weights=self.weights)

    def __pow__(self, other):
        return MicroSeries(super().__pow__(other), weights=self.weights)

    # comparators

    def __lt__(self, other):
        return MicroSeries(super().__lt__(other), weights=self.weights)

    def __le__(self, other):
        return MicroSeries(super().__le__(other), weights=self.weights)

    def __eq__(self, other):
        return MicroSeries(super().__eq__(other), weights=self.weights)

    def __ne__(self, other):
        return MicroSeries(super().__ne__(other), weights=self.weights)

    def __ge__(self, other):
        return MicroSeries(super().__ge__(other), weights=self.weights)

    def __gt__(self, other):
        return MicroSeries(super().__gt__(other), weights=self.weights)

    # assignment operators

    def __iadd__(self, other):
        return MicroSeries(super().__iadd__(other), weights=self.weights)

    def __isub__(self, other):
        return MicroSeries(super().__isub__(other), weights=self.weights)

    def __imul__(self, other):
        return MicroSeries(super().__imul__(other), weights=self.weights)

    def __ifloordiv__(self, other):
        return MicroSeries(super().__ifloordiv__(other), weights=self.weights)

    def __idiv__(self, other):
        return MicroSeries(super().__idiv__(other), weights=self.weights)

    def __itruediv__(self, other):
        return MicroSeries(super().__itruediv__(other), weights=self.weights)

    def __imod__(self, other):
        return MicroSeries(super().__imod__(other), weights=self.weights)

    def __ipow__(self, other):
        return MicroSeries(super().__ipow__(other), weights=self.weights)

    # other

    def __neg__(self, other):
        return MicroSeries(super().__neg__(other), weights=self.weights)

    def __pos__(self, other):
        return MicroSeries(super().__pos__(other), weights=self.weights)


class MicroSeriesGroupBy(pd.core.groupby.generic.SeriesGroupBy):
    def __init__(self, weights=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.weights = weights

    def _weighted_agg(func) -> Callable:
        def via_micro_series(row, fn, *args, **kwargs):
            return getattr(MicroSeries(row.a, weights=row.w), fn.__name__)(
                *args, **kwargs
            )

        @wraps(func)
        def _weighted_agg_fn(self, *args, **kwargs) -> Callable:
            arrays = self.apply(np.array)
            weights = self.weights.apply(np.array)
            df = pd.DataFrame(dict(a=arrays, w=weights))
            result = df.agg(
                lambda row: via_micro_series(row, func, *args, **kwargs),
                axis=1,
            )
            return result

        return _weighted_agg_fn

    @_weighted_agg
    def weight(self) -> pd.Series:
        return MicroSeries.weight(self)

    @_weighted_agg
    def sum(self) -> float:
        return MicroSeries.sum(self)

    @_weighted_agg
    def mean(self) -> float:
        return MicroSeries.mean(self)

    @_weighted_agg
    def quantile(self, quantiles) -> np.array:
        return MicroSeries.quantile(self, quantiles)

    @_weighted_agg
    def median(self) -> float:
        return MicroSeries.median(self)


class MicroDataFrame(pd.DataFrame):
    def __init__(self, *args, weights=None, **kwargs):
        """A DataFrame-inheriting class for weighted microdata.
        Weights can be provided at initialisation, or using set_weights or
        set_weight_col.

        :param weights: Array of weights.
        :type weights: np.array
        """
        super().__init__(*args, **kwargs)
        self.set_weights(weights)
        self._link_all_weights()

    def get_args_as_micro_series(*kwarg_names: tuple) -> Callable:
        """Decorator for auto-parsing column names into MicroSeries objects.
        If given, kwarg_names limits arguments checked to keyword arguments
        specified.

        :param arg_names: argument names to restrict to.
        :type arg_names: str
        """

        def arg_series_decorator(fn):
            @wraps(fn)
            def series_function(self, *args, **kwargs):
                new_args = []
                new_kwargs = {}
                if len(kwarg_names) == 0:
                    for value in args:
                        if isinstance(value, str):
                            if value not in self.columns:
                                raise Exception("Column not found")
                            new_args += [self[value]]
                        else:
                            new_args += [value]
                    for name, value in kwargs.items():
                        if isinstance(value, str) and (
                            len(kwarg_names) == 0 or name in kwarg_names
                        ):
                            if value not in self.columns:
                                raise Exception("Column not found")
                            new_kwargs[name] = self[value]
                        else:
                            new_kwargs[name] = value
                return fn(self, *new_args, **new_kwargs)

            return series_function

        return arg_series_decorator

    def __setitem__(self, *args, **kwargs):
        super().__setitem__(*args, **kwargs)
        self._link_all_weights()

    def _link_weights(self, column):
        # self[column] = ... triggers __setitem__, which forces pd.Series
        # this workaround avoids that
        self[column].__class__ = MicroSeries
        self[column].set_weights(self.weights)

    def _link_all_weights(self):
        for column in self.columns:
            if column != self.weights_col:
                self._link_weights(column)

    def set_weights(self, weights) -> None:
        """Sets the weights for the MicroDataFrame. If a string is received,
        it will be assumed to be the column name of the weight column.

        :param weights: Array of weights.
        :type weights: np.array
        """
        if isinstance(weights, str):
            self.weights_col = weights
            self.weights = pd.Series(self[weights], dtype=float)
        else:
            self.weights_col = None
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                self.weights = pd.Series(weights, dtype=float)
            self._link_all_weights()

    def set_weight_col(self, column) -> None:
        """Sets the weights for the MicroDataFrame by specifying the name of
        the weight column.

        :param weights: Array of weights.
        :type weights: np.array
        """
        self.weights = np.array(self[column])
        self.weight_col = column
        self._link_all_weights()

    def __getitem__(self, key):
        result = super().__getitem__(key)
        if isinstance(result, pd.DataFrame):
            weights = self.weights.__getitem__(key)
            return MicroDataFrame(result, weights=weights)
        return result

    def __getattr__(self, name):
        if name in MicroSeries.SCALAR_FUNCTIONS:
            results = MicroSeries(
                [self[col].__getattr__(name) for col in self.columns]
            )
            results.index = self.columns
            return results
        return super().__getattr__(name)

    def sum(self) -> MicroSeries:
        results = MicroSeries([self[col].sum() for col in self.columns])
        results.index = self.columns
        return results

    @get_args_as_micro_series()
    def poverty_rate(self, income: str, threshold: str) -> float:
        """Calculate poverty rate, i.e., the population share with income
        below their poverty threshold.

        :param income: Column indicating income.
        :type income: str
        :param threshold: Column indicating threshold.
        :type threshold: str
        :return: Poverty rate between zero and one.
        :rtype: float
        """
        pov = income < threshold
        return pov.sum() / pov.count()

    @get_args_as_micro_series()
    def deep_poverty_rate(self, income: str, threshold: str) -> float:
        """Calculate deep poverty rate, i.e., the population share with income
        below half their poverty threshold.

        :param income: Column indicating income.
        :type income: str
        :param threshold: Column indicating threshold.
        :type threshold: str
        :return: Deep poverty rate between zero and one.
        :rtype: float
        """
        pov = income < (threshold / 2)
        return pov.sum() / pov.count()

    @get_args_as_micro_series()
    def poverty_gap(self, income: str, threshold: str) -> float:
        """Calculate poverty gap, i.e., the total gap between income and
        poverty thresholds for all people in poverty.

        :param income: Column indicating income.
        :type income: str
        :param threshold: Column indicating threshold.
        :type threshold: str
        :return: Poverty gap.
        :rtype: float
        """
        gaps = (threshold - income)[threshold > income]
        return gaps.sum()

    @get_args_as_micro_series()
    def squared_poverty_gap(self, income: str, threshold: str) -> float:
        """Calculate squared poverty gap, i.e., the total squared gap between
        income and poverty thresholds for all people in poverty.
        Also known as the poverty severity index.

        :param income: Column indicating income.
        :type income: str
        :param threshold: Column indicating threshold.
        :type threshold: str
        :return: Squared poverty gap.
        :rtype: float
        """
        gaps = (threshold - income)[threshold > income]
        squared_gaps = gaps ** 2
        return squared_gaps.sum()

    def groupby(self, by: str, *args, **kwargs):
        """Returns a GroupBy object with MicroSeriesGroupBy objects for each column

        :param by: column to group by
        :type by: str

        return: DataFrameGroupBy object with columns using weights
        rtype: DataFrameGroupBy
        """
        gb = super().groupby(by, *args, **kwargs)
        weights = pd.Series(self.weights).groupby(self[by], *args, **kwargs)
        for col in self.columns:  # df.groupby(...)[col]s use weights
            if col != by:
                res = gb[col]
                res.__class__ = MicroSeriesGroupBy
                res.weights = weights
                setattr(gb, col, res)
        return gb

    @get_args_as_micro_series()
    def poverty_count(
        self,
        income: Union[MicroSeries, str],
        threshold: Union[MicroSeries, str],
    ) -> int:
        """Calculates the number of entities with income below a poverty threshold.

        :param income: income array or column name
        :type income: Union[MicroSeries, str]

        :param threshold: threshold array or column name
        :type threshold: Union[MicroSeries, str]

        return: number of entities in poverty
        rtype: int
        """
        in_poverty = income < threshold
        return in_poverty.sum()
