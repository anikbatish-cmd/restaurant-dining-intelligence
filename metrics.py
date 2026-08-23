def calculate_price_index(price, cohort_median):
    if not price or not cohort_median:
        return None

    return price / cohort_median


def calculate_rating_gap(rating, cohort_rating):
    if rating is None or cohort_rating is None:
        return None

    return rating - cohort_rating


def calculate_rating_volume_index(ratings, cohort_median):
    if not ratings or not cohort_median:
        return None

    return ratings / cohort_median
