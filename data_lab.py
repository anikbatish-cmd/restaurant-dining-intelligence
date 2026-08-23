from statistics import median


PLATFORM_ROLES = {
    "District": "Primary dine-in benchmark",
    "Swiggy Dineout": "Cross-platform dine-in validation",
    "EazyDiner": "Promotion and booking-market context",
    "Justdial": "Local-directory reputation context",
    "Web": "Broader public positioning / price context",
}

PLATFORM_NOTES = {
    "District": "Used for the target restaurant and competitive cohort when high-confidence direct-page data is available.",
    "Swiggy Dineout": "Kept separate from District. Useful for spotting rating, review-pool, price and offer divergence.",
    "EazyDiner": "Often most useful for visible promotion intensity; not blended into the District benchmark.",
    "Justdial": "Review counts can represent a different review universe, so they are never treated as District ratings volume.",
    "Web": "Directional only. Useful for positioning and price context; lower priority than direct dining-platform pages.",
}


def _pct_delta(value, baseline):
    if value is None or baseline in (None, 0):
        return None
    return (value / baseline - 1) * 100


def _safe_median(values):
    clean = [value for value in values if value is not None]
    return median(clean) if clean else None


def _money(value):
    return f"₹{value:,.0f}" if value is not None else "—"


def _num(value):
    return f"{value:,.0f}" if value is not None else "—"


def _pct(value, decimals=0):
    return f"{value:.{decimals}f}%" if value is not None else "—"


def build_platform_comparison(source_summaries, primary_source="District"):
    primary = source_summaries.get(primary_source) or {}
    base_rating = primary.get("rating")
    base_reviews = primary.get("review_count")
    base_price = primary.get("cost_for_two")
    base_discount = primary.get("discount_percent")

    rows = []
    for source in ["District", "Swiggy Dineout", "EazyDiner", "Justdial", "Web"]:
        summary = source_summaries.get(source)
        if not summary:
            continue

        rating = summary.get("rating")
        reviews = summary.get("review_count")
        price = summary.get("cost_for_two")
        discount = summary.get("discount_percent")
        coverage = sum(
            value is not None
            for value in [rating, reviews, price, discount]
        )

        rows.append(
            {
                "Platform": source,
                "Role": PLATFORM_ROLES.get(source, "Supporting public signal"),
                "Rating": rating,
                "Δ rating vs District": (
                    rating - base_rating
                    if rating is not None and base_rating is not None
                    else None
                ),
                "Ratings / Reviews": reviews,
                "Δ review pool vs District %": _pct_delta(reviews, base_reviews),
                "Cost for Two": price,
                "Δ price vs District": (
                    price - base_price
                    if price is not None and base_price is not None
                    else None
                ),
                "Δ price vs District %": _pct_delta(price, base_price),
                "Top Offer %": discount,
                "Δ offer vs District pp": (
                    discount - base_discount
                    if discount is not None and base_discount is not None
                    else None
                ),
                "Cuisine framing": ", ".join(summary.get("cuisines", [])[:6]) or "—",
                "Positioning": ", ".join(summary.get("positioning_tags", [])[:6]) or "—",
                "Confidence": summary.get("confidence", "Medium"),
                "Method": summary.get("method", "search_snippet").replace("_", " ").title(),
                "Coverage": f"{coverage}/4 core fields",
                "How dashboard uses it": PLATFORM_NOTES.get(source, "Supporting public context."),
                "URL": summary.get("url"),
            }
        )

    return rows


def build_platform_tensions(source_summaries):
    summaries = {
        source: summary
        for source, summary in source_summaries.items()
        if summary
    }
    tensions = []

    ratings = [
        (source, summary.get("rating"))
        for source, summary in summaries.items()
        if summary.get("rating") is not None
    ]
    if len(ratings) >= 2:
        low = min(ratings, key=lambda row: row[1])
        high = max(ratings, key=lambda row: row[1])
        spread = high[1] - low[1]
        if spread >= 0.2:
            tensions.append(
                {
                    "title": "Reputation changes by platform",
                    "signal": f"{low[0]} {low[1]:.1f} → {high[0]} {high[1]:.1f} ({spread:.1f}-point spread)",
                    "question": "Are these platforms attracting different diner cohorts, or is listing/review recency creating the gap?",
                    "logic": "max(observed platform rating) − min(observed platform rating)",
                }
            )

    prices = [
        (source, summary.get("cost_for_two"))
        for source, summary in summaries.items()
        if summary.get("cost_for_two") is not None
    ]
    if len(prices) >= 2:
        low = min(prices, key=lambda row: row[1])
        high = max(prices, key=lambda row: row[1])
        spread = high[1] - low[1]
        denominator = summaries.get("District", {}).get("cost_for_two") or high[1]
        spread_pct = spread / denominator * 100 if denominator else None
        if spread_pct is not None and spread_pct >= 10:
            tensions.append(
                {
                    "title": "Diners see different price expectations",
                    "signal": f"{low[0]} {_money(low[1])} → {high[0]} {_money(high[1])} ({spread_pct:.0f}% spread vs District price)",
                    "question": "Which public price is closest to the current bill expectation, and which listings need refreshing?",
                    "logic": "max(cost for two) − min(cost for two), divided by District cost for two",
                }
            )

    review_pools = [
        (source, summary.get("review_count"))
        for source, summary in summaries.items()
        if summary.get("review_count") not in (None, 0)
    ]
    if len(review_pools) >= 2:
        low = min(review_pools, key=lambda row: row[1])
        high = max(review_pools, key=lambda row: row[1])
        ratio = high[1] / low[1] if low[1] else None
        if ratio is not None and ratio >= 1.5:
            tensions.append(
                {
                    "title": "Review universes are materially different",
                    "signal": f"{low[0]} {_num(low[1])} vs {high[0]} {_num(high[1])} ({ratio:.1f}x larger pool)",
                    "question": "Which platform is currently acquiring reviews fastest, and do complaint themes differ by platform?",
                    "logic": "largest observed review/rating count ÷ smallest observed review/rating count",
                }
            )

    discounts = [
        (source, summary.get("discount_percent"))
        for source, summary in summaries.items()
        if summary.get("discount_percent") is not None
    ]
    if len(discounts) >= 2:
        low = min(discounts, key=lambda row: row[1])
        high = max(discounts, key=lambda row: row[1])
        gap = high[1] - low[1]
        if gap >= 10:
            tensions.append(
                {
                    "title": "Promotion exposure differs sharply",
                    "signal": f"{low[0]} {low[1]:.0f}% vs {high[0]} {high[1]:.0f}% ({gap:.0f}pp gap)",
                    "question": "Is this intentional channel-level promotion strategy or inconsistent public merchandising?",
                    "logic": "largest visible offer % − smallest visible offer %",
                }
            )

    district = summaries.get("District")
    dineout = summaries.get("Swiggy Dineout")
    if district and dineout:
        district_cuisines = {item.lower() for item in district.get("cuisines", [])}
        dineout_cuisines = {item.lower() for item in dineout.get("cuisines", [])}
        union = district_cuisines | dineout_cuisines
        if union:
            overlap = len(district_cuisines & dineout_cuisines) / len(union)
            if overlap <= 0.35 and len(union) >= 4:
                tensions.append(
                    {
                        "title": "Platforms frame the cuisine proposition differently",
                        "signal": "District: " + (", ".join(district.get("cuisines", [])[:5]) or "—") + " · Dineout: " + (", ".join(dineout.get("cuisines", [])[:5]) or "—"),
                        "question": "Which cuisine/category story should the restaurant deliberately own across discovery platforms?",
                        "logic": "Jaccard overlap of visible cuisine labels across District and Swiggy Dineout",
                    }
                )

    return tensions


def build_metric_dictionary(
    target_summary,
    competitive_metrics,
    cross_source_metrics,
    competitors,
    content_summary,
    discovery,
):
    target_summary = target_summary or {}
    competitor_metrics = [item.get("metrics", {}) for item in competitors or []]

    target_price = target_summary.get("cost_for_two")
    cohort_price = competitive_metrics.get("cohort_price_median")
    target_rating = target_summary.get("rating")
    cohort_rating = competitive_metrics.get("cohort_rating_median")
    target_reviews = target_summary.get("review_count")
    cohort_reviews = competitive_metrics.get("cohort_volume_median")
    target_discount = target_summary.get("discount_percent")
    competitor_discounts = [
        item.get("discount_percent")
        for item in competitor_metrics
        if item.get("discount_percent") is not None
    ]
    cohort_discount = _safe_median(competitor_discounts)

    metrics = [
        {
            "Metric": "Price Index",
            "Value": f"{competitive_metrics.get('price_index'):.2f}x" if competitive_metrics.get("price_index") is not None else "—",
            "Formula": "Restaurant cost for two ÷ cohort median cost for two",
            "Live calculation": f"{_money(target_price)} ÷ {_money(cohort_price)}" if target_price is not None and cohort_price is not None else "Insufficient data",
            "Interpretation": "Above 1.00x = priced above the selected competitive cohort; below 1.00x = priced below it.",
            "Guardrail": "Depends on cohort quality and public listing price accuracy. It is not realised average bill value.",
            "Source": "Primary dining source + selected competitor cohort",
        },
        {
            "Metric": "Rating Gap",
            "Value": f"{competitive_metrics.get('rating_gap'):+.1f}" if competitive_metrics.get("rating_gap") is not None else "—",
            "Formula": "Restaurant rating − cohort median rating",
            "Live calculation": f"{target_rating:.1f} − {cohort_rating:.1f}" if target_rating is not None and cohort_rating is not None else "Insufficient data",
            "Interpretation": "Positive = reputation above cohort median; negative = below cohort median.",
            "Guardrail": "Different platforms have different review pools; benchmark is kept on a common primary platform wherever possible.",
            "Source": "Primary dining source + selected competitor cohort",
        },
        {
            "Metric": "Public Interaction Index",
            "Value": f"{competitive_metrics.get('rating_volume_index'):.2f}x" if competitive_metrics.get("rating_volume_index") is not None else "—",
            "Formula": "Restaurant public ratings/reviews count ÷ cohort median ratings/reviews count",
            "Live calculation": f"{_num(target_reviews)} ÷ {_num(cohort_reviews)}" if target_reviews is not None and cohort_reviews is not None else "Insufficient data",
            "Interpretation": "Shows relative public review/rating accumulation, not footfall or bookings.",
            "Guardrail": "Never translate this metric into customer visits. Review propensity differs across brands and platforms.",
            "Source": "Primary dining source + selected competitor cohort",
        },
        {
            "Metric": "Reputation Percentile",
            "Value": _pct(competitive_metrics.get("reputation_percentile")),
            "Formula": "Percent of target + cohort ratings at or below the restaurant rating",
            "Live calculation": f"Rank {target_rating:.1f} inside {len(competitors or []) + 1} observed restaurants" if target_rating is not None else "Insufficient data",
            "Interpretation": "Higher percentile means stronger relative public rating within this specific cohort.",
            "Guardrail": "Not a city-wide percentile. It only refers to the selected competitive cohort.",
            "Source": "Primary dining cohort",
        },
        {
            "Metric": "Premium Justification Gap",
            "Value": f"{competitive_metrics.get('premium_justification_gap'):+.0f} pts" if competitive_metrics.get("premium_justification_gap") is not None else "—",
            "Formula": "Reputation percentile − price percentile",
            "Live calculation": (
                f"{competitive_metrics.get('reputation_percentile'):.0f} − {competitive_metrics.get('price_percentile'):.0f}"
                if competitive_metrics.get("reputation_percentile") is not None and competitive_metrics.get("price_percentile") is not None
                else "Insufficient data"
            ),
            "Interpretation": "Positive = reputation sits higher in the cohort than price does; negative = price positioning is ahead of relative reputation.",
            "Guardrail": "Directional positioning metric—not willingness-to-pay, margin, or pricing elasticity.",
            "Source": "Primary dining cohort",
        },
        {
            "Metric": "Offer Pressure",
            "Value": f"{target_discount - cohort_discount:+.0f}pp" if target_discount is not None and cohort_discount is not None else "—",
            "Formula": "Restaurant top visible offer % − cohort median top visible offer %",
            "Live calculation": f"{_pct(target_discount)} − {_pct(cohort_discount)}" if target_discount is not None and cohort_discount is not None else "Insufficient data",
            "Interpretation": "Positive = visibly discounting more aggressively than peers; negative = lighter visible discounting.",
            "Guardrail": "Uses visible headline offers, not redeemed discount, economics, or incremental booking impact.",
            "Source": "Primary dining listings",
        },
        {
            "Metric": "Cross-platform Rating Spread",
            "Value": f"{cross_source_metrics.get('rating_spread'):.1f}" if cross_source_metrics.get("rating_spread") is not None else "—",
            "Formula": "Highest observed platform rating − lowest observed platform rating",
            "Live calculation": "Calculated across available District / Dineout / directory / web summaries",
            "Interpretation": "Flags inconsistent reputation signals that a diner can encounter across platforms.",
            "Guardrail": "Do not average platform ratings; their review populations and freshness can differ.",
            "Source": "Cross-platform public evidence",
        },
        {
            "Metric": "Cross-platform Price Spread",
            "Value": _money(cross_source_metrics.get("price_spread")),
            "Formula": "Highest observed cost for two − lowest observed cost for two",
            "Live calculation": "Calculated across public sources with an extractable cost-for-two value",
            "Interpretation": "Flags inconsistent public price expectation.",
            "Guardrail": "Public cost-for-two can use different inclusions and update cadences.",
            "Source": "Cross-platform public evidence",
        },
        {
            "Metric": "Creator Visible Lift",
            "Value": f"{content_summary.get('creator_lift'):.2f}x" if content_summary.get("creator_lift") is not None else "—",
            "Formula": "Median visible engagement on creator/UGC sample ÷ median visible engagement on owned sample",
            "Live calculation": (
                f"{_num(content_summary.get('median_creator_engagement'))} ÷ {_num(content_summary.get('median_owned_engagement'))}"
                if content_summary.get("creator_lift") is not None
                else "Insufficient comparable content sample"
            ),
            "Interpretation": "Above 1.0x means observed creator content earned more visible interaction than observed owned content.",
            "Guardrail": "Visible engagement is not bookings, ROAS, reach quality, or incremental demand.",
            "Source": "Search-visible Instagram content sample",
        },
        {
            "Metric": "Search Discovery Share",
            "Value": f"{discovery.get('share_of_observed_mentions'):.0%}" if discovery.get("share_of_observed_mentions") is not None else "—",
            "Formula": "Target mentions ÷ total target + cohort mentions in standardized search snapshot",
            "Live calculation": f"{discovery.get('target_mentions', 0)} target mentions across observed cohort mentions",
            "Interpretation": "Directional visibility in generic high-intent public searches.",
            "Guardrail": "Not a universal search ranking. Search results vary by time, location and engine.",
            "Source": "Standardized public search queries",
        },
        {
            "Metric": "Signal Priority Score",
            "Value": "0–100 attention score",
            "Formula": "Rule-based magnitude score using anomaly size, direction and evidence strength",
            "Live calculation": "Each radar signal has its own documented threshold and magnitude scaling",
            "Interpretation": "Ranks what deserves attention first inside this report.",
            "Guardrail": "Not a restaurant health score and not comparable across unrelated restaurants as a business KPI.",
            "Source": "Derived from the metrics above",
        },
    ]

    return metrics


def classify_search_errors(errors):
    rows = []
    for error in errors or []:
        text = (error.get("error") or "").lower()
        if "timeout" in text:
            kind = "Timeout"
        elif "no results" in text:
            kind = "No results"
        else:
            kind = "Other error"
        rows.append(
            {
                "Layer": error.get("group", "Search"),
                "Type": kind,
                "Query": error.get("query", ""),
                "Error": error.get("error", ""),
            }
        )
    return rows


def build_scan_summary(debug_data, public_intel, competitor_result, dining_metrics, total_elapsed_ms=None):
    direct_attempts = dining_metrics.get("direct_page_debug", [])
    direct_success = sum(
        row.get("status_code") == 200 and not row.get("error")
        for row in direct_attempts
    )
    public_errors = public_intel.get("errors", [])
    timeout_count = sum("timeout" in (row.get("error") or "").lower() for row in public_errors)

    return {
        "Total scan ms": total_elapsed_ms,
        "Resolver search ms": debug_data.get("search_elapsed_ms"),
        "Competitor engine ms": competitor_result.get("elapsed_ms"),
        "Public intelligence ms": public_intel.get("elapsed_ms"),
        "Direct pages attempted": len(direct_attempts),
        "Direct pages successful": direct_success,
        "Competitor candidates found": competitor_result.get("candidate_count", 0),
        "Competitors enriched": competitor_result.get("enriched_count", 0),
        "Public search errors": len(public_errors),
        "Timeouts": timeout_count,
    }
