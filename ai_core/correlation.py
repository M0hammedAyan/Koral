import numpy as np

def pearson_corr(x, y):
    if len(x) < 2:
        return 0
    return np.corrcoef(x, y)[0, 1]


def lag_correlation(a_data, b_data, max_lag=3):
    best_corr = -1
    best_lag = 0

    a_values = [a["value"] for a in a_data]
    b_values = [b["value"] for b in b_data]

    min_len = min(len(a_values), len(b_values))

    for lag in range(max_lag + 1):
        x = a_values[:min_len - lag]
        y = b_values[lag:min_len]

        if len(x) < 2:
            continue

        corr = pearson_corr(x, y)

        # 🔥 tie-break logic
        if (
            corr > best_corr
            or (abs(corr - best_corr) < 1e-6 and lag > best_lag)
        ):
            best_corr = corr
            best_lag = lag

    return float(best_corr), int(best_lag)