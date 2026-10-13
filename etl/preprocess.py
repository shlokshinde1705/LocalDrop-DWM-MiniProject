"""
LocalDrop: Data Preprocessing Engine
Implements modular data cleaning, validation, outlier detection, and feature derivation.
Every function returns a tuple of (processed_df, log_metrics_dict).
"""

import re
import pandas as pd
import numpy as np
from datetime import datetime


def remove_duplicates(df, subset=None):
    """
    Identify and remove duplicate records.
    Returns: (cleaned_df, metrics_dict)
    """
    initial_count = len(df)
    duplicates_count = df.duplicated(subset=subset).sum()
    cleaned_df = df.drop_duplicates(subset=subset, keep='first').copy()
    
    return cleaned_df, {
        "operation": "remove_duplicates",
        "initial_rows": int(initial_count),
        "duplicates_removed": int(duplicates_count),
        "final_rows": int(len(cleaned_df))
    }


def handle_missing_values(df, strategies=None):
    """
    Handle missing/null values based on explicit column strategies:
    - 'drop': drop rows where column is null
    - 'mode': impute with mode
    - 'median': impute with median
    - 'default:<val>': impute with default constant
    """
    if strategies is None:
        strategies = {}

    cleaned_df = df.copy()
    null_counts_before = df.isnull().sum().to_dict()
    actions_taken = {}

    for col, strategy in strategies.items():
        if col not in cleaned_df.columns:
            continue
        missing_count = cleaned_df[col].isnull().sum()
        if missing_count > 0:
            if strategy == 'drop':
                cleaned_df = cleaned_df.dropna(subset=[col])
                actions_taken[col] = f"Dropped {missing_count} rows with NULL"
            elif strategy == 'mode':
                mode_val = cleaned_df[col].mode()[0] if not cleaned_df[col].mode().empty else "Unknown"
                cleaned_df[col] = cleaned_df[col].fillna(mode_val)
                actions_taken[col] = f"Imputed {missing_count} NULLs with mode: '{mode_val}'"
            elif strategy == 'median':
                med_val = cleaned_df[col].median()
                cleaned_df[col] = cleaned_df[col].fillna(med_val)
                actions_taken[col] = f"Imputed {missing_count} NULLs with median: {med_val}"
            elif strategy.startswith('default:'):
                def_val = strategy.split(':', 1)[1]
                cleaned_df[col] = cleaned_df[col].fillna(def_val)
                actions_taken[col] = f"Imputed {missing_count} NULLs with default: '{def_val}'"

    null_counts_after = cleaned_df.isnull().sum().to_dict()

    return cleaned_df, {
        "operation": "handle_missing_values",
        "null_counts_before": {k: int(v) for k, v in null_counts_before.items() if v > 0},
        "null_counts_after": {k: int(v) for k, v in null_counts_after.items() if v > 0},
        "actions": actions_taken,
        "rows_remaining": int(len(cleaned_df))
    }


def parse_and_standardize_dates(df, date_col='order_date'):
    """
    Parse non-standard dates (e.g. DD/MM/YYYY, YYYY.MM.DD) to ISO YYYY-MM-DD.
    Drops unparseable dates.
    """
    cleaned_df = df.copy()
    initial_count = len(cleaned_df)
    parsed_dates = []
    invalid_date_count = 0

    def parse_single_date(d_val):
        if pd.isnull(d_val):
            return None
        d_str = str(d_val).strip()
        # Common formats in order of check
        formats = [
            '%Y-%m-%d', '%d/%m/%Y', '%Y.%m.%d', '%d-%m-%Y', '%Y/%m/%d'
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(d_str, fmt)
                # Ensure plausible range 2020-2030
                if 2020 <= dt.year <= 2030:
                    return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        return None

    standardized = cleaned_df[date_col].apply(parse_single_date)
    invalid_mask = standardized.isnull()
    invalid_date_count = int(invalid_mask.sum())

    cleaned_df[date_col] = standardized
    cleaned_df = cleaned_df[~invalid_mask].copy()

    return cleaned_df, {
        "operation": "parse_and_standardize_dates",
        "column": date_col,
        "invalid_dates_dropped": invalid_date_count,
        "valid_dates_retained": int(len(cleaned_df))
    }


def validate_numeric_bounds(df, rules=None):
    """
    Validates numeric columns within sensible operational bounds.
    rules: dict of col -> (min_val, max_val, action: 'drop' | 'clamp')
    """
    if rules is None:
        rules = {}

    cleaned_df = df.copy()
    corrections = {}

    for col, (min_v, max_v, action) in rules.items():
        if col not in cleaned_df.columns:
            continue
        cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
        out_of_bounds = (cleaned_df[col] < min_v) | (cleaned_df[col] > max_v)
        oob_count = int(out_of_bounds.sum())

        if oob_count > 0:
            if action == 'drop':
                cleaned_df = cleaned_df[~out_of_bounds].copy()
                corrections[col] = f"Dropped {oob_count} rows outside [{min_v}, {max_v}]"
            elif action == 'clamp':
                cleaned_df[col] = cleaned_df[col].clip(lower=min_v, upper=max_v)
                corrections[col] = f"Clamped {oob_count} values to interval [{min_v}, {max_v}]"

    return cleaned_df, {
        "operation": "validate_numeric_bounds",
        "corrections": corrections,
        "rows_after_validation": int(len(cleaned_df))
    }


def filter_invalid_orders(df):
    """
    Remove invalid orders (e.g. quantity <= 0, empty status).
    """
    cleaned_df = df.copy()
    initial_rows = len(cleaned_df)
    
    # Filter negative or zero quantity
    valid_mask = (cleaned_df['quantity'] > 0)
    invalid_qty_count = int((~valid_mask).sum())
    cleaned_df = cleaned_df[valid_mask].copy()

    return cleaned_df, {
        "operation": "filter_invalid_orders",
        "negative_or_zero_quantity_dropped": invalid_qty_count,
        "valid_orders_count": int(len(cleaned_df))
    }


def detect_outliers_iqr(df, column):
    """
    Detect outliers using Interquartile Range (IQR) method.
    Outlier boundaries: [Q1 - 1.5*IQR, Q3 + 1.5*IQR]
    Returns: (df_with_flag, outlier_summary)
    """
    series = df[column].dropna()
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    outliers_mask = (df[column] < lower_bound) | (df[column] > upper_bound)
    outlier_count = int(outliers_mask.sum())

    flagged_df = df.copy()
    flagged_df[f"{column}_is_outlier"] = outliers_mask

    return flagged_df, {
        "column": column,
        "q1": round(float(q1), 2),
        "median": round(float(series.median()), 2),
        "q3": round(float(q3), 2),
        "iqr": round(float(iqr), 2),
        "lower_bound": round(float(lower_bound), 2),
        "upper_bound": round(float(upper_bound), 2),
        "outlier_count": outlier_count,
        "outlier_percentage": round(float((outlier_count / len(df)) * 100), 2)
    }


def create_derived_fields(sales_df, orders_df=None):
    """
    Derives analytical features:
    - Year, Month, Quarter, Day of Week, Month Name
    - Profit Margin Percentage
    - Order Value Band (Low, Medium, High, Premium)
    """
    df = sales_df.copy()
    dt_series = pd.to_datetime(df['sale_date'])

    df['year'] = dt_series.dt.year
    df['month'] = dt_series.dt.month
    df['quarter'] = dt_series.dt.quarter
    df['month_name'] = dt_series.dt.strftime('%B')
    df['day_name'] = dt_series.dt.strftime('%A')

    # Derived Profit Margin %
    # Avoid zero division
    df['profit_margin_pct'] = np.where(
        df['total_amount'] > 0,
        np.round((df['profit'] / df['total_amount']) * 100, 2),
        0.0
    )

    # Order Value Band
    # Bins: < 500: Low | 500-1500: Medium | 1500-4000: High | >= 4000: Premium
    conditions = [
        (df['total_amount'] < 500),
        (df['total_amount'] >= 500) & (df['total_amount'] < 1500),
        (df['total_amount'] >= 1500) & (df['total_amount'] < 4000),
        (df['total_amount'] >= 4000)
    ]
    choices = ['Low (< ₹500)', 'Medium (₹500-₹1500)', 'High (₹1500-₹4000)', 'Premium (≥ ₹4000)']
    df['order_value_band'] = np.select(conditions, choices, default='Medium (₹500-₹1500)')

    return df, {
        "operation": "create_derived_fields",
        "new_columns": ['year', 'month', 'quarter', 'month_name', 'day_name', 'profit_margin_pct', 'order_value_band'],
        "sample_derived_records": int(len(df))
    }
