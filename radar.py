from statistics import median


def _clamp(value, low=0, high=100):
    return max(low, min(high, value))


def _safe_median(values):
    clean = [value for value in values if value is not None]
    return median(clean) if clean else None


def _add(
    signals,
    category,
    title,
    signal,
    severity,
    score,
    why,
    proof,
    direction="Neutral",
    confidence="Medium",
):
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
            "confidence": confidence,
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
    instagram_snapshots=None,
):
    """Rank observable public-market anomalies, advantages and tensions.

    Scores express attention priority inside this report. They are not business KPIs.
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
                "Price Index + Rating Gap",
                "Risk",
                "High",
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
                "Price Index + Rating Gap",
                "Positive",
                "High",
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
                "Price Index + Rating Gap",
                "Positive",
                "High",
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
                "Public Interaction Index + Rating Gap",
                "Risk",
                "High",
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
                "Public Interaction Index + Rating Gap",
                "Positive",
                "High",
            )

    # PREMIUM JUSTIFICATION
    if premium_gap is not None and reputation_pct is not None and price_pct is not None:
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
                "Premium Justification Gap",
                "Risk",
                "High",
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
                "Premium Justification Gap",
                "Positive",
                "High",
            )

    # CROSS-SOURCE CONTRADICTIONS
    rating_spread = cross_source_metrics.get("rating_spread")
    if rating_spread is not None and rating_spread >= 0.25:
        score = 58 + min(35, rating_spread * 70)
        _add(
            signals,
            "Platform divergence",
            "Platforms disagree on reputation",
            f"{rating_spread:.1f}-point observed rating spread",
            "Critical" if rating_spread >= 0.5 else "Watch",
            score,
            "A diner can see materially different reputation signals depending on the platform used.",
            "Cross-platform Rating Spread",
            "Risk",
            "High",
        )

    target_price = target_summary.get("cost_for_two") if target_summary else None
    price_spread = cross_source_metrics.get("price_spread")
    if price_spread is not None and target_price:
        spread_pct = price_spread / target_price * 100
        if spread_pct >= 12:
            score = 58 + min(32, spread_pct * 0.9)
            _add(
                signals,
                "Platform divergence",
                "Public price perception is fragmented",
                f"₹{price_spread:,.0f} spread across sources · {spread_pct:.0f}% of District price",
                "Watch",
                score,
                "The same restaurant presents a materially different cost expectation depending on the public source a diner sees.",
                "Cross-platform Price Spread",
                "Risk",
                "High",
            )

    available_summaries = [summary for summary in source_summaries.values() if summary]
    review_counts = [
        (source, summary.get("review_count"))
        for source, summary in source_summaries.items()
        if summary and summary.get("review_count") not in (None, 0)
    ]
    if len(review_counts) >= 2:
        smallest = min(review_counts, key=lambda row: row[1])
        largest = max(review_counts, key=lambda row: row[1])
        pool_ratio = largest[1] / smallest[1] if smallest[1] else None
        if pool_ratio is not None and pool_ratio >= 1.75:
            score = 60 + min(28, (pool_ratio - 1) * 18)
            _add(
                signals,
                "Platform divergence",
                "Platforms reflect very different review universes",
                f"{largest[0]} {largest[1]:,.0f} vs {smallest[0]} {smallest[1]:,.0f} · {pool_ratio:.1f}x pool gap",
                "Watch",
                score,
                "Review/rating counts are not directly interchangeable across platforms; the gap itself is worth monitoring for review acquisition and audience mix.",
                "Cross-platform review-pool ratio",
                "Neutral",
                "High",
            )

    platform_discounts = [
        (source, summary.get("discount_percent"))
        for source, summary in source_summaries.items()
        if summary and summary.get("discount_percent") is not None
    ]
    if len(platform_discounts) >= 2:
        low = min(platform_discounts, key=lambda row: row[1])
        high = max(platform_discounts, key=lambda row: row[1])
        gap = high[1] - low[1]
        if gap >= 10:
            score = 61 + min(28, gap * 1.3)
            _add(
                signals,
                "Platform divergence",
                "Promotion exposure changes by platform",
                f"{low[0]} {low[1]:.0f}% vs {high[0]} {high[1]:.0f}% · {gap:.0f}pp gap",
                "Watch",
                score,
                "The public deal story is materially different depending on where the diner discovers the restaurant.",
                "Cross-platform visible-offer gap",
                "Risk",
                "Medium",
            )

    district = source_summaries.get("District")
    dineout = source_summaries.get("Swiggy Dineout")
    if district and dineout:
        left = {value.lower() for value in district.get("cuisines", [])}
        right = {value.lower() for value in dineout.get("cuisines", [])}
        union = left | right
        if union:
            overlap = len(left & right) / len(union)
            if overlap <= 0.30 and len(union) >= 4:
                score = 58 + min(25, (0.30 - overlap) * 60 + len(union))
                _add(
                    signals,
                    "Platform divergence",
                    "Cuisine framing changes across dining platforms",
                    "District: " + (", ".join(district.get("cuisines", [])[:4]) or "—") + " · Dineout: " + (", ".join(dineout.get("cuisines", [])[:4]) or "—"),
                    "Opportunity",
                    score,
                    "The restaurant is being categorized differently across major dine-in discovery surfaces, which can change what search occasions it is eligible to appear for.",
                    "Cuisine-label overlap across District and Swiggy Dineout",
                    "Neutral",
                    "High",
                )

    # OFFER PRESSURE VS COMPETITIVE COHORT
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
                "Offer Pressure",
                "Risk",
                "High",
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
                "Offer Pressure",
                "Positive",
                "High",
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
            f"Customer voice sample ({customer_voice.get('sample_size', 0)} usable snippets)",
            "Risk",
            customer_voice.get("confidence", "Low"),
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
            f"Customer voice sample ({customer_voice.get('sample_size', 0)} usable snippets)",
            "Positive",
            customer_voice.get("confidence", "Low"),
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
                "Search Discovery Share",
                "Risk",
                "Medium",
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
                "Search Discovery Share",
                "Positive",
                "Medium",
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
                "Creator Visible Lift",
                "Positive",
                "Medium",
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
                "Creator Visible Lift",
                "Risk",
                "Medium",
            )

    themes = content_summary.get("themes", [])
    sample_size = content_summary.get("sample_size", 0)
    if themes and sample_size >= 5:
        top_theme = max(themes, key=lambda row: row.get("posts", row.get("count", 0)))
        top_posts = top_theme.get("posts", top_theme.get("count", 0))
        concentration = top_posts / sample_size if sample_size else 0
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
                "Medium",
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
                "Owned proposition vs earned-media themes",
                "Neutral",
                "Medium",
            )

    # POSITIONING WHITE SPACE / CROWDING
    competitor_tag_sets = [
        set(item.get("metrics", {}).get("positioning_tags", []))
        for item in competitors or []
    ]
    if target_tags and competitor_tag_sets:
        unique_tags = [
            tag
            for tag in target_tags
            if sum(tag in tags for tags in competitor_tag_sets) <= 1
        ]
        crowded_tags = [
            tag
            for tag in target_tags
            if sum(tag in tags for tags in competitor_tag_sets)
            >= max(2, len(competitor_tag_sets) // 2)
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
                "Medium",
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
                "Medium",
            )

    # INSTAGRAM FRESHNESS / VERSIONING
    instagram_snapshots = instagram_snapshots or []
    follower_values = [
        row.get("Followers")
        for row in instagram_snapshots
        if row.get("Followers") is not None
    ]
    selected_followers = instagram_metrics.get("followers")
    if selected_followers and len(follower_values) >= 2:
        spread = max(follower_values) - min(follower_values)
        spread_pct = spread / selected_followers * 100
        if spread_pct >= 5:
            score = 52 + min(26, spread_pct * 1.5)
            _add(
                signals,
                "Data freshness",
                "Instagram search snapshots are not equally fresh",
                f"{min(follower_values):,.0f} → {max(follower_values):,.0f} followers across indexed observations",
                "Watch",
                score,
                "Profile, reels and story snippets can be crawled at different times; the canonical profile observation is used while older snapshots remain visible for audit.",
                "Instagram public-search snapshot spread",
                "Neutral",
                "Medium",
            )

    # SOCIAL SCALE CONTEXT
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
            "Canonical public Instagram profile",
            "Positive",
            "High",
        )

    severity_order = {
        "Critical": 4,
        "Watch": 3,
        "Opportunity": 2,
        "Advantage": 1,
    }
    signals.sort(
        key=lambda item: (
            item["score"],
            severity_order.get(item["severity"], 0),
        ),
        reverse=True,
    )

    for index, item in enumerate(signals, start=1):
        item["rank"] = index

    return signals


def build_conversation_starters(signals, platform_tensions=None, limit=6):
    starters = []
    platform_tensions = platform_tensions or []

    for tension in platform_tensions[:2]:
        starters.append(tension.get("question"))

    for item in signals:
        if len(starters) >= limit:
            break
        if item["category"] == "Platform divergence":
            question = f"What explains this platform gap: {item['signal']}?"
        elif item["category"] == "Competitive":
            question = f"What is driving {item['signal'].lower()}, and has that relationship changed recently?"
        elif item["category"] == "Customer voice":
            question = f"Does internal feedback show the same pattern as this public signal: {item['signal']}?"
        elif item["category"] == "Discovery":
            question = f"Which discovery occasions matter most commercially, and does the current {item['signal'].lower()} match internal booking-source data?"
        elif item["severity"] == "Advantage":
            question = f"Is this advantage deliberate or accidental: {item['signal']}?"
        else:
            question = f"What changed that could explain this signal: {item['signal']}?"
        if question not in starters:
            starters.append(question)

    return starters[:limit]
