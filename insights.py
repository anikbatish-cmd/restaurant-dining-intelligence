from collections import Counter


TOPIC_MAP = {
    "Food": ["food", "dish", "menu", "taste", "flavour", "flavor", "sushi", "chicken"],
    "Ambience": ["ambience", "ambiance", "vibe", "interior", "rooftop", "view"],
    "Service": ["service", "server", "staff", "hospitality", "waiter"],
    "Value": ["value", "price", "expensive", "overpriced", "worth", "cost"],
    "Waiting": ["wait", "waiting", "slow", "delay"],
    "Drinks": ["drink", "cocktail", "beer", "bar", "brew"],
    "Music": ["music", "dj", "loud"],
    "Parking": ["parking", "valet"],
    "Hygiene": ["hygiene", "clean", "dirty"],
    "Experience": ["experience", "date", "romantic", "night", "friends"],
}

POSITIVE_WORDS = [
    "great", "good", "amazing", "excellent", "perfect", "beautiful", "loved",
    "love", "pretty", "attentive", "delicious", "best", "unique", "impressive",
    "nice", "wonderful",
]

NEGATIVE_WORDS = [
    "bad", "poor", "slow", "worst", "disappoint", "overpriced", "expensive",
    "dirty", "rude", "not good", "average", "delay", "old", "not maintained",
]


def _result_text(result):
    return f"{result.get('title', '')} {result.get('snippet', '')}".strip()


def _sentiment(text):
    lower = text.lower()
    positive = sum(word in lower for word in POSITIVE_WORDS)
    negative = sum(word in lower for word in NEGATIVE_WORDS)
    if positive > negative:
        return "Positive"
    if negative > positive:
        return "Negative"
    return "Mixed / Neutral"


def analyze_customer_voice(results):
    topic_stats = {
        topic: {"topic": topic, "mentions": 0, "positive": 0, "negative": 0, "mixed": 0, "examples": []}
        for topic in TOPIC_MAP
    }
    usable_results = []

    for result in results or []:
        text = _result_text(result)
        lower = text.lower()
        if not text:
            continue
        matched = [topic for topic, keywords in TOPIC_MAP.items() if any(keyword in lower for keyword in keywords)]
        if not matched:
            continue
        sentiment = _sentiment(text)
        usable_results.append(result)
        for topic in matched:
            bucket = topic_stats[topic]
            bucket["mentions"] += 1
            if sentiment == "Positive":
                bucket["positive"] += 1
            elif sentiment == "Negative":
                bucket["negative"] += 1
            else:
                bucket["mixed"] += 1
            if len(bucket["examples"]) < 3:
                bucket["examples"].append({
                    "snippet": result.get("snippet", ""),
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "sentiment": sentiment,
                })

    topics = []
    for bucket in topic_stats.values():
        if not bucket["mentions"]:
            continue
        scored = dict(bucket)
        scored["net_sentiment"] = (scored["positive"] - scored["negative"]) / scored["mentions"]
        topics.append(scored)

    topics.sort(key=lambda row: (row["mentions"], abs(row["net_sentiment"])), reverse=True)
    strengths = sorted([row for row in topics if row["net_sentiment"] > 0], key=lambda row: (row["net_sentiment"], row["mentions"]), reverse=True)
    concerns = sorted([row for row in topics if row["net_sentiment"] < 0], key=lambda row: (row["net_sentiment"], -row["mentions"]))

    sample_size = len(usable_results)
    confidence = "High" if sample_size >= 10 else "Medium" if sample_size >= 5 else "Low"
    return {"sample_size": sample_size, "confidence": confidence, "topics": topics, "strengths": strengths[:3], "concerns": concerns[:3], "evidence": usable_results}


def _occasion_themes(text):
    lower = (text or "").lower()
    mapping = {
        "Date night": ["date night", "romantic", "couple"],
        "Nightlife": ["nightlife", "party", "dj", "late night"],
        "Rooftop": ["rooftop", "roof top", "terrace"],
        "Drinks": ["cocktail", "bar", "beer", "drink"],
        "Food-led": ["food", "menu", "dish", "cuisine"],
        "Experience-led": ["experience", "immersive", "themed", "vibe"],
        "Friends": ["friends", "hangout", "group"],
    }
    return [theme for theme, keywords in mapping.items() if any(keyword in lower for keyword in keywords)]


def analyze_earned_attention(results):
    directory_domains = ["district.in", "swiggy.com", "eazydiner.com", "justdial.com", "instagram.com", "facebook.com"]
    earned = []
    for result in results or []:
        url = result.get("url", "").lower()
        if any(domain in url for domain in directory_domains):
            continue
        text = _result_text(result)
        earned.append({"title": result.get("title", ""), "url": result.get("url", ""), "snippet": result.get("snippet", ""), "themes": _occasion_themes(text)})
    theme_counter = Counter()
    for item in earned:
        theme_counter.update(item["themes"])
    return {"count": len(earned), "top_themes": theme_counter.most_common(5), "evidence": earned[:10]}


def analyze_discovery(results, restaurant, competitor_names):
    names = [restaurant] + list(competitor_names or [])
    counts = {name: 0 for name in names}
    query_rows = {}
    for result in results or []:
        query = result.get("query", "Public search")
        text = _result_text(result).lower()
        row = query_rows.setdefault(query, {"query": query, "target_found": False, "competitors_found": []})
        for index, name in enumerate(names):
            clean = name.lower().strip()
            if clean and clean in text:
                counts[name] += 1
                if index == 0:
                    row["target_found"] = True
                elif name not in row["competitors_found"]:
                    row["competitors_found"].append(name)
    total_mentions = sum(counts.values())
    target_mentions = counts.get(restaurant, 0)
    share = target_mentions / total_mentions if total_mentions else None
    return {
        "target_mentions": target_mentions,
        "share_of_observed_mentions": share,
        "counts": counts,
        "queries": list(query_rows.values()),
        "methodology": "Standardized public-search snapshot. Results can vary by time, location and search engine; this is not a universal rank.",
    }


def detect_paid_signal(results, restaurant):
    evidence = []
    for result in results or []:
        text = _result_text(result).lower()
        url = result.get("url", "").lower()
        if "ads/library" in url or "sponsored" in text or "meta ad" in text or "advertisement" in text:
            evidence.append(result)
    return {
        "status": "Observable public signal found" if evidence else "No reliable public signal detected",
        "evidence": evidence[:5],
        "claim_limit": "Public search can indicate visible advertising activity, but cannot establish spend, ROAS or booking impact.",
    }


def generate_core_insights(competitive_metrics, cross_source_metrics, customer_voice, content_summary, discovery, target_summary):
    insights = []
    price_index = competitive_metrics.get("price_index")
    rating_gap = competitive_metrics.get("rating_gap")
    rating_volume_index = competitive_metrics.get("rating_volume_index")
    premium_gap = competitive_metrics.get("premium_justification_gap")

    if price_index is not None and rating_gap is not None and price_index > 1.10 and rating_gap < -0.10:
        insights.append({
            "type": "Gap",
            "title": "Premium price without a reputation premium",
            "observation": f"Price is {round((price_index - 1) * 100)}% above the competitive median while rating trails it by {abs(rating_gap):.1f}.",
            "implication": "The public proposition is asking customers to pay a premium that is not yet matched by relative reputation.",
            "recommendation": "Prioritise experience/value fixes and premium proof points before pushing the price narrative harder.",
            "confidence": "High",
        })

    if rating_volume_index is not None and rating_gap is not None and rating_volume_index > 1.10 and rating_gap < 0:
        insights.append({
            "type": "Opportunity",
            "title": "Public interaction is stronger than relative satisfaction",
            "observation": f"Rating/review volume is {rating_volume_index:.1f}x the competitive median, while rating is below the cohort.",
            "implication": "The restaurant appears to attract meaningful public interaction; the bigger opportunity is converting that interaction into stronger advocacy.",
            "recommendation": "Use review themes to isolate the experience moments suppressing rating before investing primarily in more awareness.",
            "confidence": "Medium",
        })

    if premium_gap is not None and premium_gap >= 20:
        insights.append({
            "type": "Strength",
            "title": "Reputation is supporting the price position",
            "observation": f"Reputation percentile exceeds price percentile by {premium_gap:.0f} points within the cohort.",
            "implication": "There is observable room to communicate premium value more confidently.",
            "recommendation": "Make the highest-rated experience attributes more explicit in owned content, creator briefs and booking-page merchandising.",
            "confidence": "High",
        })

    rating_spread = cross_source_metrics.get("rating_spread")
    if rating_spread is not None and rating_spread >= 0.3:
        insights.append({
            "type": "Gap",
            "title": "Cross-platform reputation is inconsistent",
            "observation": f"Public ratings differ by {rating_spread:.1f} points across observed platforms.",
            "implication": "Different platforms may be capturing different customer pools or review histories.",
            "recommendation": "Track platform-level review velocity and recurring complaints separately instead of relying on a single blended reputation number.",
            "confidence": "High",
        })

    if customer_voice.get("concerns"):
        concern = customer_voice["concerns"][0]
        insights.append({
            "type": "Gap",
            "title": f"{concern['topic']} is the clearest negative public theme",
            "observation": f"{concern['topic']} appears in {concern['mentions']} search-visible review snippets with a negative directional skew.",
            "implication": "This is a hypothesis worth validating with internal feedback and on-ground audits.",
            "recommendation": f"Audit the {concern['topic'].lower()} journey and compare the issue against the restaurant's strongest positive experience drivers.",
            "confidence": customer_voice.get("confidence", "Low"),
        })

    creator_lift = content_summary.get("creator_lift")
    if creator_lift is not None and creator_lift >= 1.25:
        insights.append({
            "type": "Opportunity",
            "title": "Creator content shows stronger visible engagement",
            "observation": f"Median visible creator/UGC engagement is {creator_lift:.1f}x the owned-content sample.",
            "implication": "Third-party distribution may be a stronger public attention lever than the current owned-content sample.",
            "recommendation": "Build repeatable creator briefs around the themes already earning visible interaction; do not interpret this as booking lift without internal data.",
            "confidence": "Medium",
        })

    share = discovery.get("share_of_observed_mentions")
    if share is not None and share < 0.20:
        insights.append({
            "type": "Opportunity",
            "title": "Search discovery share is weak versus the observed cohort",
            "observation": f"The restaurant captures about {share:.0%} of observed mentions across the standardized discovery snapshot.",
            "implication": "The restaurant may be underrepresented in generic high-intent discovery journeys.",
            "recommendation": "Strengthen occasion-led discoverability through listing hygiene, earned coverage and content aligned to the highest-fit search occasions.",
            "confidence": "Medium",
        })

    tags = target_summary.get("positioning_tags", []) if target_summary else []
    if len(tags) >= 2:
        insights.append({
            "type": "Strength",
            "title": "The public proposition has clear experiential hooks",
            "observation": "Observable positioning includes " + ", ".join(tags[:4]) + ".",
            "implication": "Distinctive experience cues give marketing a stronger story than generic food-only messaging.",
            "recommendation": "Measure which experiential cue earns the strongest visible engagement and make that the lead creative territory.",
            "confidence": "High",
        })
    return insights[:8]


def consultant_workspace(insights, customer_voice, target_summary):
    strengths = [insight for insight in insights if insight["type"] == "Strength"][:3]
    gaps = [insight for insight in insights if insight["type"] == "Gap"][:3]
    opportunities = [insight for insight in insights if insight["type"] == "Opportunity"][:3]

    while len(strengths) < 3:
        fallback = target_summary.get("positioning_tags", []) if target_summary else []
        if not fallback:
            break
        tag = fallback[min(len(strengths), len(fallback) - 1)]
        strengths.append({
            "title": f"{tag} gives the brand a recognizable public cue",
            "observation": "This cue is repeatedly visible in public positioning evidence.",
            "recommendation": "Test it consistently across listings, creators and owned content.",
            "confidence": "Medium",
        })

    questions = [
        "Which customer occasion do you most want to own over the next 90 days?",
        "Which experience issue shows up most often in your internal feedback, and does it match the public review pattern?",
        "What percentage of dine-in bookings currently come from organic discovery, creators, paid media and repeat customers?",
        "Which visible offer drives incremental bookings versus simply discounting customers who would have visited anyway?",
        "Which content or creator collaboration has produced the strongest booking-quality signal internally, not just engagement?",
    ]
    if customer_voice.get("concerns"):
        concern = customer_voice["concerns"][0]["topic"].lower()
        questions.insert(0, f"What is your internal view on the public {concern} concern, and has it changed recently?")

    return {"strengths": strengths[:3], "gaps": gaps[:3], "opportunities": opportunities[:3], "owner_questions": questions[:5]}
