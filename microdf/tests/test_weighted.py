import pandas as pd

import microdf as mdf


X = [1, 5, 2]
Y = [0, -6, 3]
W = [4, 1, 1]
df = pd.DataFrame({"x": X, "y": Y, "w": W})
# Also make a version with groups.
df2 = df.copy(deep=True)
df2.x *= 2
df2.y *= 1.5
dfg = pd.concat([df, df2])
dfg["g"] = ["a"] * 3 + ["b"] * 3


def test_weighted_quantile():
    Q = [0, 0.5, 1]
    mdf.weighted_quantile(df, "x", "w", Q).tolist()


def test_weighted_median():
    assert mdf.weighted_median(df, "x") == 2
    mdf.weighted_median(df, "x", "w")
    # Test with groups.
    mdf.weighted_median(dfg, "x", "w", "g")


def test_weighted_mean():
    # Test umweighted.
    assert mdf.weighted_mean(df, "x") == 8 / 3
    # Test weighted.
    assert mdf.weighted_mean(df, "x", "w") == 11 / 6
    # Test weighted with multiple columns.
    assert mdf.weighted_mean(df, ["x", "y"], "w").tolist() == [11 / 6, -3 / 6]
    # Test grouped.
    mdf.weighted_mean(dfg, "x", "w", "g")
    mdf.weighted_mean(dfg, ["x", "y"], "w", "g")


def test_weighted_sum():
    # Test unweighted.
    assert mdf.weighted_sum(df, "x") == 8
    # Test weighted.
    assert mdf.weighted_sum(df, "x", "w") == 11
    # Test weighted with multiple columns.
    assert mdf.weighted_sum(df, ["x", "y"], "w").tolist() == [11, -3]
    # Test grouped.
    mdf.weighted_sum(dfg, "x", "w", "g")
    mdf.weighted_sum(dfg, ["x", "y"], "w", "g")


def test_gini():
    # Unweighted
    mdf.gini(df, "x")
    # Weighted
    mdf.gini(df, "x", "w")
    # Unweighted, grouped
    mdf.gini(dfg, "x", groupby="g")
    # Weighted, grouped
    mdf.gini(dfg, "x", "w", groupby="g")
