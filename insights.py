def generate_core_insights(
    price_index=None,
    rating_gap=None,
    rating_volume_index=None,
):

    insights = []

    if (
        price_index is not None
        and rating_gap is not None
        and price_index > 1.10
        and rating_gap < -0.10
    ):
        insights.append(
            {
                "title": "Premium price without a reputation premium",
                "interpretation": (
                    "The restaurant is priced materially above its "
                    "competitive cohort while its rating trails the cohort."
                ),
                "confidence": "High",
            }
        )

    if (
        rating_volume_index is not None
        and rating_gap is not None
        and rating_volume_index > 1
        and rating_gap < 0
    ):
        insights.append(
            {
                "title": "Trial appears stronger than satisfaction",
                "interpretation": (
                    "Public rating volume is above the competitive median, "
                    "while customer rating remains below the cohort."
                ),
                "confidence": "Medium",
            }
        )

    return insights
