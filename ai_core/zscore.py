import numpy as np

def compute_z_score(values, current):
    mean = np.mean(values)
    std = np.std(values)

    if std == 0:
        return 0

    return (current - mean) / std