def ema_filter(prev_value, new_value, alpha=0.2):
    """
    Simple exponential moving average filter.
    alpha closer to 1.0 = reacts faster, more noise
    alpha closer to 0.0 = smoother, slower
    """
    if prev_value is None:
        return new_value
    return alpha * new_value + (1.0 - alpha) * prev_value
