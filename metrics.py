from math import log10
from statistics import median


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


def percentile_rank(value, values):
    clean = [item for item in values if item is not None]
    if value is None or not clean:
        return None
    below_or_equal = sum(item <= value for item in clean)
    return 100 * below_or_equal / len(clean)


def cohort_median(values):
    clean = [item for item in values if item is not None]
    return median(clean) if clean else None


def clamp(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, value))


def build_competitive_metrics(target, competitors):
    competitor_metrics = [item.get("metrics", {}) for item in competitors]
    ratings = [item.get("rating") for item in competitor_metrics if item.get("rating") is not None]
    volumes = [item.get("review_count") for item in competitor_metrics if item.get("review_count") is not None]
    prices = [item.get("cost_for_two") for item in competitor_metrics if item.get("cost_for_two") is not None]

    rating_median = cohort_median(ratings)
    volume_median = cohort_median(volumes)
    price_median = cohort_median(prices)

    rating = target.get("rating") if target else None
    review_count = target.get("review_count") if target else None
    cost_for_two = target.get("cost_for_two") if target else None

    all_ratings = ratings + ([rating] if rating is not None else [])
    all_volumes = volumes + ([review_count] if review_count is not None else [])
    all_prices = prices + ([cost_for_two] if cost_for_two is not None else [])

    reputation_percentile = percentile_rank(rating, all_ratings)
    volume_percentile = percentile_rank(review_count, all_volumes)
    price_percentile = percentile_rank(cost_for_two, all_prices)

    premium_justification_gap = None
    if reputation_percentile is not None and price_percentile is not None:
        premium_justification_gap = reputation_percentile - price_percentile

    return {
        "cohort_size": len(competitors),
        "cohort_rating_median": rating_median,
        "cohort_volume_median": volume_median,
        "cohort_price_median": price_median,
        "rating_gap": calculate_rating_gap(rating, rating_median),
        "price_index": calculate_price_index(cost_for_two, price_median),
        "rating_volume_index": calculate_rating_volume_index(review_count, volume_median),
        "reputation_percentile": reputation_percentile,
        "volume_percentile": volume_percentile,
        "price_percentile": price_percentile,
        "premium_justification_gap": premium_justification_gap,
    }


def build_cross_source_metrics(source_summaries):
    ratings = []
    prices = []
    volumes = []
    for summary in source_summaries.values():
        if not summary:
            continue
        if summary.get("rating") is not None:
            ratings.append(summary["rating"])
        if summary.get("cost_for_two") is not None:
            prices.append(summary["cost_for_two"])
        if summary.get("review_count") is not None:
            volumes.append(summary["review_count"])
    return {
        "platforms_with_rating": len(ratings),
        "platforms_with_price": len(prices),
        "rating_spread": max(ratings) - min(ratings) if len(ratings) >= 2 else None,
        "price_spread": max(prices) - min(prices) if len(prices) >= 2 else None,
        "max_public_review_count": max(volumes) if volumes else None,
    }


def social_presence_score(instagram_metrics, content_summary):
    score = 0.0
    coverage = 0
    followers = instagram_metrics.get("followers")
    posts = instagram_metrics.get("posts")
    if followers is not None:
        score += clamp(20 + 25 * max(0, log10(max(followers, 1)) - 2))
        coverage += 1
    if posts is not None:
        score += clamp(posts / 4)
        coverage += 1
    sample_size = content_summary.get("sample_size", 0)
    if sample_size:
        score += clamp(30 + sample_size * 8)
        coverage += 1
    return score / coverage if coverage else None


def proposition_score(target_summary):
    if not target_summary:
        return None
    tags = target_summary.get("positioning_tags", [])
    cuisines = target_summary.get("cuisines", [])
    offers = target_summary.get("offers", [])
    score = 45 + min(len(tags), 5) * 7 + min(len(cuisines), 5) * 3
    if offers:
        score += 5
    return clamp(score)


def external_health_score(target_summary, competitive_metrics, instagram_metrics, content_summary):
    reputation = competitive_metrics.get("reputation_percentile")
    volume = competitive_metrics.get("volume_percentile")
    premium_gap = competitive_metrics.get("premium_justification_gap")
    marketing = social_presence_score(instagram_metrics, content_summary)
    proposition = proposition_score(target_summary)

    components = {}
    if reputation is not None:
        components["Reputation"] = reputation
    elif target_summary and target_summary.get("rating") is not None:
        components["Reputation"] = clamp((target_summary["rating"] - 3.0) / 2.0 * 100)
    if volume is not None:
        components["Public interaction volume"] = volume
    if premium_gap is not None:
        components["Price-value fit"] = clamp(50 + premium_gap * 0.6)
    if marketing is not None:
        components["Public marketing presence"] = marketing
    if proposition is not None:
        components["Proposition clarity"] = proposition

    weights = {
        "Reputation": 0.30,
        "Public interaction volume": 0.20,
        "Price-value fit": 0.20,
        "Public marketing presence": 0.15,
        "Proposition clarity": 0.15,
    }
    available_weight = sum(weights[name] for name in components if name in weights)
    if not available_weight:
        return {"score": None, "components": components, "coverage": 0}

    weighted = sum(components[name] * weights[name] for name in components if name in weights) / available_weight
    return {
        "score": round(weighted, 1),
        "components": {name: round(value, 1) for name, value in components.items()},
        "coverage": round(available_weight * 100),
    }
