from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter
from urllib.parse import urlsplit

from collectors import extract_direct_page_metrics
from search_engine import clean_name, search_multiple, similarity


FORMAT_KEYWORDS = {
    "Rooftop": ["rooftop", "roof top", "terrace"],
    "Romantic": ["romantic", "date night"],
    "Nightlife": ["nightlife", "bar", "cocktail", "party"],
    "Live Music": ["live music", "live performance"],
    "Brewery": ["brewery", "craft beer"],
    "Fine Dining": ["fine dining"],
    "Casual Dining": ["casual dining"],
    "Experience-led": ["themed", "immersive", "experience"],
}


def _restaurant_name_from_title(title):
    if not title:
        return ""
    for separator in [" | ", " - ", " – "]:
        if separator in title:
            candidate = title.split(separator)[0].strip()
            if candidate:
                return candidate
    return title.strip()


def _district_slug(url):
    try:
        path = urlsplit(url).path.rstrip("/")
        return path.split("/")[-1]
    except Exception:
        return ""


def _format_signals(text):
    lower = (text or "").lower()
    return [
        tag
        for tag, keywords in FORMAT_KEYWORDS.items()
        if any(keyword in lower for keyword in keywords)
    ]


def _overlap_score(left, right):
    left_set = {str(x).lower() for x in left or []}
    right_set = {str(x).lower() for x in right or []}
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def _price_similarity(target_price, competitor_price):
    if not target_price or not competitor_price:
        return 0.45
    ratio = min(target_price, competitor_price) / max(target_price, competitor_price)
    return max(0.0, min(1.0, ratio))


def _cheap_candidate_score(candidate, target_tags, location):
    text = f"{candidate.get('title', '')} {candidate.get('snippet', '')}"
    snippet_tags = _format_signals(text)
    positioning_similarity = _overlap_score(target_tags, snippet_tags)
    location_score = 1.0 if location.lower() in text.lower() else 0.65
    has_restaurant_detail = "/dining/" in candidate.get("url", "").lower()

    score = (
        0.50 * positioning_similarity
        + 0.30 * location_score
        + 0.20 * (1.0 if has_restaurant_detail else 0.0)
    )
    if not target_tags:
        score += 0.20
    return min(score, 1.0)


def discover_competitors(restaurant, location, target_summary, target_context="", limit=5):
    """Discover and rank a comparable District cohort with parallel enrichment."""
    started = perf_counter()
    target_cuisines = target_summary.get("cuisines", []) if target_summary else []
    target_tags = list(target_summary.get("positioning_tags", [])) if target_summary else []
    target_price = target_summary.get("cost_for_two") if target_summary else None

    for tag in _format_signals(target_context):
        if tag not in target_tags:
            target_tags.append(tag)

    cuisine_query = " ".join(target_cuisines[:2]) or "restaurants"
    format_query = " ".join(target_tags[:2]) or "dining"

    queries = [
        f"site:district.in/dining {location} {cuisine_query}",
        f"site:district.in/dining {location} {format_query}",
        f"best {cuisine_query} restaurants {location} District",
        f"{format_query} restaurants {location} District",
    ]

    search = search_multiple(queries, max_results=9)
    candidates = {}
    target_clean = clean_name(restaurant)

    for result in search["results"]:
        url = result.get("url", "")
        if "district.in/dining/" not in url.lower():
            continue

        name = _restaurant_name_from_title(result.get("title", ""))
        if not name or similarity(target_clean, clean_name(name)) >= 0.70:
            continue

        slug = _district_slug(url)
        if not slug:
            continue

        candidate = candidates.setdefault(
            slug,
            {
                "name": name,
                "url": url,
                "title": result.get("title", ""),
                "snippet": result.get("snippet", ""),
            },
        )
        candidate["pre_score"] = _cheap_candidate_score(
            candidate,
            target_tags,
            location,
        )

    # Only enrich the strongest shortlist. This is the expensive stage.
    shortlist = sorted(
        candidates.values(),
        key=lambda item: item.get("pre_score", 0),
        reverse=True,
    )[:8]

    fetched = {}
    if shortlist:
        with ThreadPoolExecutor(max_workers=min(5, len(shortlist))) as executor:
            future_map = {
                executor.submit(extract_direct_page_metrics, candidate["url"]): candidate
                for candidate in shortlist
            }
            for future in as_completed(future_map):
                candidate = future_map[future]
                try:
                    direct, debug = future.result()
                except Exception as exc:
                    direct = None
                    debug = {
                        "source": "District",
                        "url": candidate["url"],
                        "status_code": None,
                        "error": str(exc),
                        "elapsed_ms": None,
                    }
                fetched[candidate["url"]] = (direct, debug)

    enriched = []
    for candidate in shortlist:
        direct, debug = fetched.get(candidate["url"], (None, None))

        if direct:
            candidate["metrics"] = direct
            candidate["debug"] = debug
        else:
            candidate["metrics"] = {
                "rating": None,
                "review_count": None,
                "cost_for_two": None,
                "offers": [],
                "discount_percent": None,
                "cuisines": [],
                "positioning_tags": _format_signals(
                    f"{candidate['title']} {candidate['snippet']}"
                ),
                "confidence": "Medium",
                "url": candidate["url"],
            }
            candidate["debug"] = debug

        metrics = candidate["metrics"]
        cuisine_similarity = _overlap_score(
            target_cuisines,
            metrics.get("cuisines", []),
        )
        positioning_similarity = _overlap_score(
            target_tags,
            metrics.get("positioning_tags", []),
        )
        price_similarity = _price_similarity(
            target_price,
            metrics.get("cost_for_two"),
        )
        location_text = f"{candidate.get('title', '')} {candidate.get('snippet', '')}".lower()
        location_score = 1.0 if location.lower() in location_text else 0.65

        # Final competitor match prioritizes price band first, then cuisine,
        # positioning and location. Weights intentionally sum to 100%.
        score = (
            0.50 * price_similarity
            + 0.25 * cuisine_similarity
            + 0.15 * positioning_similarity
            + 0.10 * location_score
        )
        if not target_cuisines or not metrics.get("cuisines"):
            score += 0.08
        if not target_tags or not metrics.get("positioning_tags"):
            score += 0.07

        candidate["match_score"] = min(score, 1.0)
        candidate["match_components"] = {
            "price_similarity": price_similarity,
            "cuisine_similarity": cuisine_similarity,
            "positioning_similarity": positioning_similarity,
            "location_score": location_score,
        }
        enriched.append(candidate)

    enriched.sort(
        key=lambda item: (
            item["match_score"],
            item["metrics"].get("review_count") or 0,
        ),
        reverse=True,
    )

    return {
        "competitors": enriched[:limit],
        "candidate_count": len(candidates),
        "enriched_count": len(enriched),
        "queries": queries,
        "errors": search["errors"],
        "elapsed_ms": round((perf_counter() - started) * 1000),
    }
