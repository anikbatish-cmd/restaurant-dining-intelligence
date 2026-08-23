from statistics import median


def _clamp(value, low=0, high=100):
    return max(low, min(high, value))


def _safe_median(values):
    clean = [value for value in values if value is not None]
    return median(clean) if clean else None


def _add(signals, category, title, signal, severity, score, why, proof, direction="Neutral"):
    signals.append(
        {
            "category": category,
            "title": title,
            "signal": signal,
            "severity": severity,
            "score": round(_clamp(score)),
            "why": why,
            "proof": proof,
            "direction": direction,
        }
    )


def build_signal_radar(
    competitive_metrics,
    cross_source_metrics,
    customer_voice,
    content_summary,
    discovery,
    earned,
    target_summary,
    source_summaries,
    competitors,
    instagram_metrics,
):
    """Build a ranked feed of public-market anomalies, advantages and tensions.

    The radar deliberately ranks observable tensions rather than prescribing actions.
    Scores express attention priority inside this report; they are not business KPIs.
    """

    signals = []
    price_index = competitive_metrics.get("price_index")
    rating_gap = competitive_metrics.get("rating_gap")
    volume_index = competitive_metrics.get("rating_volume_index")
    premium_gap = competitive_metrics.get("premium_justification_gap")
    reputation_pct = competitive_metrics.get("reputation_percentile")
    price_pct = competitive_metrics.get("price_percentile")

    # PRICE x REPUTATION
    if price_index is not None and rating_gap is not None:
        premium_pct = (price_index - 1) * 100
        if premium_pct >= 10 and rating_gap <= -0.1:
            score = 62 + min(22, premium_pct * 0.8) + min(16, abs(rating_gap) * 30)
            _add(
                signals,
                "Competitive",
                "Price premium is outrunning reputation",
                f"{premium_pct:+.0f}% price vs cohort · {rating_gap:+.1f} rating gap",
                "Critical" if score >= 80 else "Watch",
                score,
                "The restaurant asks the market to pay more while public rating trails comparable restaurants.",
                "Price index and cohort rating gap",
                "Risk",
            )
        elif premium_pct >= 10 and rating_gap >= 0.1:
            score = 68 + min(18, premium_pct * 0.6) + min(14, rating_gap * 25)
            _add(
                signals,
                "Competitive",
                "The premium is publicly justified",
                f"{premium_pct:+.0f}% price vs cohort · {rating_gap:+.1f} rating gap",
                "Advantage",
                score,
                "The restaurant commands a premium while maintaining a reputation advantage over the cohort.",
                "Price index and cohort rating gap",
                "Positive",
            )
        elif premium_pct <= -10 and rating_gap >= 0.1:
            score = 70 + min(20, abs(premium_pct) * 0.5) + min(10, rating_gap * 20)
            _add(
                signals,
                "Competitive",
                "High reputation at a relative value price",
                f"{premium_pct:+.0f}% price vs cohort · {rating_gap:+.1f} rating gap",
                "Opportunity",
                score,
                "Public reputation is stronger than the cohort even though price is materially lower.",
                "Price index and cohort rating gap",
                "Positive",
            )

    # INTERACTION VOLUME x SATISFACTION
    if volume_index is not None and rating_gap is not None:
        if volume_index >= 1.25 and rating_gap < 0:
            score = 68 + min(18, (volume_index - 1) * 25) + min(14, abs(rating_gap) * 25)
            _add(
                signals,
                "Reputation",
                "Interaction is strong; advocacy is lagging",
                f"{volume_index:.2f}x public rating volume · {rating_gap:+.1f} rating gap",
                "Watch",
                score,
                "The restaurant has accumulated more public interaction than peers, but that interaction is not translating into a stronger relative rating.",
                "Rating-volume index and cohort rating gap",
                "Risk",
            )
        elif volume_index <= 0.70 and rating_gap > 0:
            score = 66 + min(20, (1 - volume_index) * 45) + min(12, rating_gap * 20)
            _add(
                signals,
                "Reputation",
                "Loved by fewer people than the rating deserves",
                f"{volume_index:.2f}x public rating volume · {rating_gap:+.1f} rating gap",
                "Opportunity",
                score,
                "Relative satisfaction is strong, but public interaction volume is materially below the cohort.",
                "Rating-volume index and cohort rating gap",
                "Positive",
            )

    # PREMIUM JUSTIFICATION
    if premium_gap is not None:
        if premium_gap <= -20:
            score = 64 + min(30, abs(premium_gap) * 0.7)
            _add(
                signals,
                "Competitive",
                "Price percentile is ahead of reputation percentile",
                f"{price_pct:.0f}th price pct · {reputation_pct:.0f}th reputation pct",
                "Critical" if premium_gap <= -35 else "Watch",
                score,
                "Within the observed cohort, pricing sits materially higher in the distribution than reputation does.",
                "Premium justification gap",
                "Risk",
            )
        elif premium_gap >= 20:
            score = 64 + min(28, premium_gap * 0.65)
            _add(
                signals,
                "Competitive",
                "Reputation is ahead of price positioning",
                f"{reputation_pct:.0f}th reputation pct · {price_pct:.0f}th price pct",
                "Advantage",
                score,
                "The public reputation percentile materially exceeds the price percentile inside the selected cohort.",
                "Premium justification gap",
                "Positive",
            )

    # CROSS-SOURCE CONTRADICTIONS
    rating_spread = cross_source_metrics.get("rating_spread")
    if rating_spread is not None and rating_spread >= 0.25:
        score = 58 + min(35, rating_spread * 70)
        _add(
            signals,
            "Source consistency",
            "Platforms disagree on reputation",
            f"{rating_spread:.1f}-point observed rating spread",
            "Critical" if rating_spread >= 0.5 else "Watch",
            score,
            "Customers researching on different platforms can encounter materially different reputation signals.",
            "Cross-source rating spread",
            "Risk",
        )

    target_price = target_summary.get("cost_for_two") if target_summary else None
    price_spread = cross_source_metrics.get("price_spread")
    if price_spread is not None and target_price:
        spread_pct = price_spread / target_price * 100
        if spread_pct >= 15:
            score = 58 + min(32, spread_pct * 0.9)
            _add(
                signals,
                "Source consistency",
                "Public price perception is fragmented",
                f"₹{price_spread:,.0f} spread across sources · {spread_pct:.0f}% of benchmark price",
                "Watch",
                score,
                "The same restaurant presents a materially different cost expectation depending on the public source a diner sees.",
                "Cross-source cost-for-two spread",
                "Risk",
            )

    # OFFER PRESSURE
    target_discount = target_summary.get("discount_percent") if target_summary else None
    competitor_discounts = [
        item.get("metrics", {}).get("discount_percent")
        for item in competitors or []
        if item.get("metrics", {}).get("discount_percent") is not None
    ]
    cohort_discount = _safe_median(competitor_discounts)
    if target_discount is not None and cohort_discount is not None:
        discount_gap = target_discount - cohort_discount
        if discount_gap >= 10:
            score = 61 + min(29, discount_gap * 1.5)
            _add(
                signals,
                "Promotions",
                "Discount intensity is above the cohort",
                f"{target_discount:.0f}% visible offer · cohort median {cohort_discount:.0f}%",
                "Watch",
                score,
                "The restaurant is visibly leaning harder on promotion than comparable restaurants in the observed cohort.",
                "Top visible offer vs competitor median",
                "Risk",
            )
        elif discount_gap <= -10 and rating_gap is not None and rating_gap >= 0:
            score = 64 + min(24, abs(discount_gap) * 1.2)
            _add(
                signals,
                "Promotions",
                "Reputation holds with less visible discounting",
                f"{target_discount:.0f}% visible offer · cohort median {cohort_discount:.0f}%",
                "Advantage",
                score,
                "Relative reputation is at least in line with peers despite a materially lighter visible offer.",
                "Top visible offer vs competitor median",
                "Positive",
            )

    # CUSTOMER VOICE
    for concern in customer_voice.get("concerns", [])[:3]:
        mentions = concern.get("mentions", 0)
        negatives = concern.get("negative", 0)
        negative_share = negatives / mentions if mentions else 0
        score = 54 + min(24, mentions * 5) + min(22, negative_share * 22)
        _add(
            signals,
            "Customer voice",
            f"{concern['topic']} is a negative public friction point",
            f"{mentions} observed mentions · {negative_share:.0%} negative skew",
            "Critical" if score >= 80 and mentions >= 3 else "Watch",
            score,
            "This topic is one of the clearest negative patterns in the search-visible review sample.",
            f"Customer voice sample · {customer_voice.get('confidence', 'Low')} confidence",
            "Risk",
        )

    for strength in customer_voice.get("strengths", [])[:2]:
        mentions = strength.get("mentions", 0)
        positives = strength.get("positive", 0)
        positive_share = positives / mentions if mentions else 0
        score = 52 + min(24, mentions * 4) + min(20, positive_share * 20)
        _add(
            signals,
            "Customer voice",
            f"{strength['topic']} is carrying public advocacy",
            f"{mentions} observed mentions · {positive_share:.0%} positive skew",
            "Advantage",
            score,
            "This is one of the strongest positive themes visible in the public review sample.",
            f"Customer voice sample · {customer_voice.get('confidence', 'Low')} confidence",
            "Positive",
        )

    # SEARCH DISCOVERY
    share = discovery.get("share_of_observed_mentions")
    if share is not None:
        if share < 0.15:
            score = 70 + min(24, (0.15 - share) * 150)
            _add(
                signals,
                "Discovery",
                "The restaurant disappears in generic discovery",
                f"{share:.0%} share of observed cohort mentions",
                "Critical" if share < 0.08 else "Watch",
                score,
                "Across the standardized generic discovery snapshot, competitors surface much more often than the target restaurant.",
                "Standardized public-search snapshot",
                "Risk",
            )
        elif share >= 0.35:
            score = 66 + min(25, (share - 0.35) * 100)
            _add(
                signals,
                "Discovery",
                "The restaurant over-indexes in generic discovery",
                f"{share:.0%} share of observed cohort mentions",
                "Advantage",
                score,
                "The target captures a disproportionate share of mentions across the standardized high-intent search snapshot.",
                "Standardized public-search snapshot",
                "Positive",
            )

    # CONTENT / CREATOR
    creator_lift = content_summary.get("creator_lift")
    if creator_lift is not None:
        if creator_lift >= 1.30:
            score = 64 + min(28, (creator_lift - 1) * 35)
            _add(
                signals,
                "Marketing",
                "Creators outperform owned content in visible engagement",
                f"{creator_lift:.1f}x creator visible engagement lift",
                "Opportunity",
                score,
                "Third-party content earns materially more visible interaction than the observable owned-content sample.",
                "Owned vs creator/UGC public-content sample",
                "Positive",
            )
        elif creator_lift <= 0.70:
            score = 58 + min(26, (1 - creator_lift) * 45)
            _add(
                signals,
                "Marketing",
                "Creator content is not outperforming owned content",
                f"{creator_lift:.1f}x creator visible engagement lift",
                "Watch",
                score,
                "The observable creator/UGC sample is not earning the expected visible engagement premium over owned content.",
                "Owned vs creator/UGC public-content sample",
                "Risk",
            )

    themes = content_summary.get("themes", [])
    sample_size = content_summary.get("sample_size", 0)
    if themes and sample_size >= 5:
        top_theme = max(themes, key=lambda row: row.get("count", 0))
        concentration = top_theme.get("count", 0) / sample_size
        if concentration >= 0.60:
            score = 56 + min(30, (concentration - 0.60) * 100)
            _add(
                signals,
                "Marketing",
                "Content is concentrated in one creative territory",
                f"{top_theme.get('theme', 'Top theme')} = {concentration:.0%} of observed content sample",
                "Watch",
                score,
                "The public content mix appears heavily concentrated, reducing observable breadth of the brand story.",
                "Observable Instagram/creator content sample",
                "Risk",
            )

    # EARNED POSITIONING VS OWNED POSITIONING
    target_tags = set(target_summary.get("positioning_tags", []) if target_summary else [])
    earned_themes = {theme for theme, _count in earned.get("top_themes", [])[:4]}
    if earned.get("count", 0) >= 3 and target_tags and earned_themes:
        overlap = target_tags & earned_themes
        if not overlap:
            score = 63 + min(22, earned.get("count", 0) * 3)
            _add(
                signals,
                "Positioning",
                "Earned attention tells a different story from owned positioning",
                "Owned: " + ", ".join(sorted(target_tags)[:3]) + " · Earned: " + ", ".join(sorted(earned_themes)[:3]),
                "Opportunity",
                score,
                "External coverage appears to remember the restaurant for different cues than the cues emphasized in its public proposition.",
                "Owned proposition vs earned-media theme classification",
                "Neutral",
            )

    # POSITIONING WHITE SPACE / CROWDING
    competitor_tag_sets = [
        set(item.get("metrics", {}).get("positioning_tags", []))
        for item in competitors or []
    ]
    if target_tags and competitor_tag_sets:
        unique_tags = [
            tag for tag in target_tags
            if sum(tag in tags for tags in competitor_tag_sets) <= 1
        ]
        crowded_tags = [
            tag for tag in target_tags
            if sum(tag in tags for tags in competitor_tag_sets) >= max(2, len(competitor_tag_sets) // 2)
        ]
        if unique_tags:
            score = 62 + min(26, len(unique_tags) * 7)
            _add(
                signals,
                "Positioning",
                "There is visible positioning white space",
                "Distinctive cues: " + ", ".join(unique_tags[:4]),
                "Advantage",
                score,
                "These public positioning cues appear relatively uncommon across the selected competitive cohort.",
                "Target vs competitor positioning-tag overlap",
                "Positive",
            )
        elif crowded_tags and len(crowded_tags) >= 2:
            score = 58 + min(22, len(crowded_tags) * 6)
            _add(
                signals,
                "Positioning",
                "The public proposition lives in crowded territory",
                "Shared cues: " + ", ".join(crowded_tags[:4]),
                "Watch",
                score,
                "Several of the restaurant's visible positioning cues are also common across comparable competitors.",
                "Target vs competitor positioning-tag overlap",
                "Risk",
            )

    # SOCIAL SCALE CONTEXT (only if meaningfully large; no performance claim)
    followers = instagram_metrics.get("followers")
    if followers is not None and followers >= 10000:
        score = 52 + min(24, followers / 5000)
        _add(
            signals,
            "Marketing",
            "Owned social audience is a meaningful public asset",
            f"{followers:,.0f} Instagram followers",
            "Advantage",
            score,
            "The restaurant has accumulated a visible owned audience that can be evaluated alongside creator and discovery signals.",
            "Public Instagram profile",
            "Positive",
        )

    severity_order = {"Critical": 4, "Watch": 3, "Opportunity": 2, "Advantage": 1}
    signals.sort(
        key=lambda item: (item["score"], severity_order.get(item["severity"], 0)),
        reverse=True,
    )

    for index, item in enumerate(signals, start=1):
        item["rank"] = index

    return signals


def build_conversation_starters(signals, limit=6):
    starters = []
    for item in signals[:limit]:
        if item["severity"] in {"Critical", "Watch"}:
            starters.append(
                f"{item['title']}: what changed operationally or commercially that could explain {item['signal'].lower()}?"
            )
        elif item["severity"] == "Opportunity":
            starters.append(
                f"{item['title']}: is this something the team already sees internally, or is the public signal ahead of internal measurement?"
            )
        else:
            starters.append(
                f"{item['title']}: do you intentionally own this advantage, or has it emerged organically?"
            )
    return starters
