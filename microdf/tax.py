import pandas as pd


def mtr(val, brackets, rates):
    # Calculates the marginal tax rate applied to a value depending on a schedule.
    #
    # Args:
    #     val: Value to assess tax on, e.g. wealth or income (list or Series).
    #     brackets: Left side of each bracket (list or Series).
    #     rates: Rate corresponding to each bracket.
    #
    # Returns:
    #     Series of the size of val representing the marginal tax rate.
    df_tax = pd.DataFrame({'brackets': brackets, 'rates': rates})
    df_tax['base_tax'] = df_tax.brackets.\
                         sub(df_tax.brackets.shift(fill_value=0)).\
                         mul(df_tax.rates.shift(fill_value=0)).cumsum()
    rows = df_tax.brackets.searchsorted(val, side='right') - 1
    income_bracket_df = df_tax.loc[rows].reset_index(drop=True)
    return income_bracket_df.rates

def tax_from_mtrs(val, brackets, rates, avoidance_rate=0,
                  avoidance_elasticity=0):
    # Calculates tax liability based on a marginal tax rate schedule.
    #
    # Args:
    #     val: Value to assess tax on, e.g. wealth or income (list or Series).
    #     brackets: Left side of each bracket (list or Series).
    #     rates: Rate corresponding to each bracket.
    #     avoidance_rate: Constant avoidance/evasion rate in percentage terms.
    #                     Defaults to zero.
    #     avoidance_elasticity: Avoidance/evasion elasticity.
    #                           Response of taxable value with respect to tax rate.
    #                           Defaults to zero. Should be positive.
    #
    # Returns:
    #     Series of tax liabilities with the same size as val.
    assert avoidance_rate == 0 or avoidance_elasticity == 0, \
        "Cannot supply both avoidance_rate and avoidance_elasticity."
    assert avoidance_elasticity >= 0, "Provide nonnegative avoidance_elasticity."
    df_tax = pd.DataFrame({'brackets': brackets, 'rates': rates})
    df_tax['base_tax'] = df_tax.brackets.\
        sub(df_tax.brackets.shift(fill_value=0)).\
        mul(df_tax.rates.shift(fill_value=0)).cumsum()
    if avoidance_elasticity > 0:
        mtrs = mtr(val, brackets, rates)
        avoidance_rate = avoidance_elasticity * mtrs
    taxable = pd.Series(val) * (1 - avoidance_rate)
    rows = df_tax.brackets.searchsorted(taxable, side='right') - 1
    income_bracket_df = df_tax.loc[rows].reset_index(drop=True)
    return pd.Series(taxable).sub(income_bracket_df.brackets).\
        mul(income_bracket_df.rates).add(income_bracket_df.base_tax)
