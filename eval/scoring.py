def scaled_credit(value,floor,target):
    """Protocol linear interpolation, including lower-is-better bounds."""
    if value is None or floor is None or target is None:
        return None
    return min(1.0,max(0.0,(value-floor)/(target-floor)))
