from statistics import median


def _median(values):
    clean = [value for value in values if value is not None]
    return median(clean) if clean else None


def _clamp(value, low=0, high=100):
    return max(low, min(high, value))


def _overlap(left, right):
    a = {str(item).lower() for item in left or []}
    b = {str(item).lower() for item in right or []}
    if not a or not b:
        return None
    return len(a & b) / len(a | b)


def build_market_position(target_summary, competitive_metrics):
    price_index = competitive_metrics.get("price_index")
    rating_gap = competitive_metrics.get("rating_gap")

    if price_index is None or rating_gap is None:
        return {
            "quadrant": "Insufficient public data",
            "headline": "Market position could not be resolved confidently.",
            "price_delta_pct": None,
            "rating_gap": rating_gap,
        }

    price_delta_pct = (price_index - 1) * 100

    if price_delta_pct >= 8 and rating_gap >= 0.1:
        quadrant = "Premium Leader"
        headline = "The restaurant charges a premium and publicly earns it."
    elif price_delta_pct >= 8 and rating_gap < 0:
        quadrant = "Premium Under Pressure"
        headline = "Price is ahead of relative reputation — the premium needs stronger proof."
    elif price_delta_pct <= -8 and rating_gap >= 0.1:
        quadrant = "Value Hero"
        headline = "Reputation is stronger than the price position suggests."
    elif price_delta_pct <= -8 and rating_gap < 0:
        quadrant = "Value / Reputation Drag"
        headline = "Lower pricing is not yet translating into a reputation advantage."
    elif rating_gap >= 0.1:
        quadrant = "Reputation Advantage"
        headline = "Pricing is near the market while reputation sits above it."
    elif rating_gap <= -0.1:
        quadrant = "Reputation Catch-up"
        headline = "Pricing is near the market but reputation trails the cohort."
    else:
        quadrant = "Market Parity"
        headline = "Price and reputation both sit close to the competitive middle."

    return {
        "quadrant": quadrant,
        "headline": headline,
        "price_delta_pct": price_delta_pct,
        "rating_gap": rating_gap,
    }


def build_gap_metrics(
    target_summary,
    competitive_metrics,
    cross_source_metrics,
    discovery,
    customer_voice,
    content_summary,
    competitors,
    source_summaries,
):
    reputation_pct = competitive_metrics.get("reputation_percentile")
    volume_pct = competitive_metrics.get("volume_percentile")
    discovery_share = discovery.get("share_of_observed_mentions")

    demand_capture_gap = None
    if reputation_pct is not None and discovery_share is not None:
        demand_capture_gap = reputation_pct - discovery_share * 100

    advocacy_conversion_gap = None
    if volume_pct is not None and reputation_pct is not None:
        advocacy_conversion_gap = volume_pct - reputation_pct

    target_discount = target_summary.get("discount_percent") if target_summary else None
    competitor_discounts = [
        item.get("metrics", {}).get("discount_percent")
        for item in competitors or []
        if item.get("metrics", {}).get("discount_percent") is not None
    ]
    cohort_discount = _median(competitor_discounts)
    promotion_pressure = None
    if target_discount is not None and cohort_discount is not None:
        promotion_pressure = target_discount - cohort_discount

    rating_spread = cross_source_metrics.get("rating_spread")
    price_spread = cross_source_metrics.get("price_spread")
    district_price = (source_summaries.get("District") or {}).get("cost_for_two")
    price_spread_pct = (
        price_spread / district_price * 100
        if price_spread is not None and district_price
        else None
    )

    offer_values = [
        summary.get("discount_percent")
        for summary in source_summaries.values()
        if summary and summary.get("discount_percent") is not None
    ]
    offer_spread = max(offer_values) - min(offer_values) if len(offer_values) >= 2 else None

    fragmentation_parts = []
    if rating_spread is not None:
        fragmentation_parts.append(_clamp(rating_spread / 0.5 * 100))
    if price_spread_pct is not None:
        fragmentation_parts.append(_clamp(price_spread_pct / 25 * 100))
    if offer_spread is not None:
        fragmentation_parts.append(_clamp(offer_spread / 20 * 100))
    platform_fragmentation = (
        sum(fragmentation_parts) / len(fragmentation_parts)
        if fragmentation_parts
        else None
    )

    strongest_positive = customer_voice.get("strengths", [])[:1]
    strongest_negative = customer_voice.get("concerns", [])[:1]

    creator_lift = content_summary.get("creator_lift")

    return {
        "demand_capture_gap": demand_capture_gap,
        "advocacy_conversion_gap": advocacy_conversion_gap,
        "promotion_pressure_pp": promotion_pressure,
        "platform_fragmentation_index": platform_fragmentation,
        "price_spread_pct": price_spread_pct,
        "offer_spread_pp": offer_spread,
        "creator_lift": creator_lift,
        "strongest_positive_topic": strongest_positive[0]["topic"] if strongest_positive else None,
        "strongest_negative_topic": strongest_negative[0]["topic"] if strongest_negative else None,
    }


def build_positioning_white_space(target_summary, competitors, customer_voice, earned):
    target_tags = target_summary.get("positioning_tags", []) if target_summary else []
    competitor_tags = [
        set(item.get("metrics", {}).get("positioning_tags", []))
        for item in competitors or []
    ]

    distinctive = []
    crowded = []
    for tag in target_tags:
        count = sum(tag in tags for tags in competitor_tags)
        if count <= 1:
            distinctive.append(tag)
        if competitor_tags and count >= max(2, len(competitor_tags) // 2):
            crowded.append(tag)

    customer_strengths = [item.get("topic") for item in customer_voice.get("strengths", [])]
    customer_concerns = [item.get("topic") for item in customer_voice.get("concerns", [])]
    earned_themes = [theme for theme, _count in earned.get("top_themes", [])]

    return {
        "distinctive_tags": distinctive,
        "crowded_tags": crowded,
        "customer_strengths": customer_strengths,
        "customer_concerns": customer_concerns,
        "earned_themes": earned_themes,
    }


def build_executive_story(market_position, gaps, white_space):
    lines = [market_position.get("headline")]

    capture_gap = gaps.get("demand_capture_gap")
    if capture_gap is not None:
        if capture_gap >= 25:
            lines.append("Public reputation is materially stronger than generic discovery visibility — a demand-capture gap is visible.")
        elif capture_gap <= -20:
            lines.append("Discovery visibility is stronger than relative reputation — awareness may be outrunning advocacy.")

    fragmentation = gaps.get("platform_fragmentation_index")
    if fragmentation is not None and fragmentation >= 55:
        lines.append("The restaurant presents a fragmented public story across platforms, creating inconsistent expectations before a visit.")

    promo = gaps.get("promotion_pressure_pp")
    if promo is not None and promo >= 10:
        lines.append("Visible discounting is materially heavier than the competitor cohort, making promotion dependence worth investigating.")

    if white_space.get("distinctive_tags"):
        lines.append(
            "Distinctive public territory exists around "
            + ", ".join(white_space["distinctive_tags"][:3])
            + "."
        )

    return [line for line in lines if line][:4]
