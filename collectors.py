import json
import re
from datetime import datetime, timezone
from statistics import median
from urllib.parse import urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}


def identify_source(url):
    url = (url or "").lower()
    if "district.in" in url:
        return "District"
    if "swiggy.com" in url:
        return "Swiggy Dineout"
    if "eazydiner.com" in url:
        return "EazyDiner"
    if "justdial.com" in url:
        return "Justdial"
    if "instagram.com" in url:
        return "Instagram"
    if "facebook.com" in url:
        return "Facebook"
    return "Web"


def canonicalize_restaurant_url(url):
    if not url:
        return url
    parts = urlsplit(url)
    path = parts.path.rstrip("/")
    if "swiggy.com" in parts.netloc.lower():
        path = re.sub(r"/(photos|menu)$", "", path, flags=re.IGNORECASE)
    if "district.in" in parts.netloc.lower():
        path = re.sub(r"/(menu|reviews|photos)$", "", path, flags=re.IGNORECASE)
    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def get_text(result):
    if not result:
        return ""
    return " ".join([result.get("title", ""), result.get("snippet", "")])


def extract_rating(text):
    patterns = [
        r"rated\s+([1-5]\.\d)",
        r"\b([1-5]\.\d)\s+(?:rating|ratings|reviews)",
        r"(?:rating|ratingValue)[\"'\s:=]+([1-5](?:\.\d)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                value = float(match.group(1))
                if 1 <= value <= 5:
                    return value
            except ValueError:
                pass
    return None


def extract_review_count(text):
    patterns = [
        r"based on\s+([\d,]+)\s+(?:customer\s+)?reviews",
        r"([\d,]+)\s+(?:dining\s+)?ratings",
        r"([\d,]+)\s+reviews",
        r"(?:ratingCount|reviewCount)[\"'\s:=]+([\d,]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1).replace(",", ""))
            except ValueError:
                pass
    return None


def extract_cost_for_two(text):
    patterns = [
        r"₹\s*([\d,]+)\s*(?:for two|for 2)",
        r"Rs\.?\s*([\d,]+)\s*(?:for two|for 2)",
        r"(?:cost|price)\s*(?:for)?\s*(?:two|2)\D{0,12}₹?\s*([\d,]+)",
        r"₹\s*([\d,]+)\s*(?:approx(?:\.|imately)?\s*)?(?:for two|for 2)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                value = int(match.group(1).replace(",", ""))
                if 100 <= value <= 50000:
                    return value
            except ValueError:
                pass
    return None


def normalize_offer(offer):
    if not offer:
        return None
    clean = re.sub(r"\s+", " ", offer).strip()
    clean = re.sub(r"\bUPTO\b", "Up to", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bFLAT\b", "Flat", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bOFF\b", "OFF", clean, flags=re.IGNORECASE)
    return clean


def extract_offers(text):
    patterns = [
        r"(flat\s+\d+%\s+off)",
        r"(up\s+to\s+\d+%\s+off)",
        r"(upto\s+\d+%\s+off)",
        r"(\d+%\s+discount)",
    ]
    offers = []
    seen = set()
    for pattern in patterns:
        for match in re.findall(pattern, text, re.IGNORECASE):
            clean = normalize_offer(match)
            if clean and clean.lower() not in seen:
                seen.add(clean.lower())
                offers.append(clean)
    return offers


def extract_discount_percent(offers):
    values = []
    for offer in offers or []:
        match = re.search(r"(\d+)%", offer)
        if match:
            values.append(int(match.group(1)))
    return max(values) if values else None


def extract_cuisines(text):
    known = [
        "North Indian", "Chinese", "Italian", "Continental", "Asian",
        "Japanese", "Mediterranean", "Thai", "Sushi", "Mexican",
        "Lebanese", "Mughlai", "Desserts", "Beverages", "Cafe",
        "Bar Food", "Fusion", "Multi Cuisine", "South Indian",
        "European", "Modern Indian", "Pan Asian",
    ]
    return [cuisine for cuisine in known if cuisine.lower() in text.lower()]


def extract_positioning_tags(text):
    text = (text or "").lower()
    tag_map = {
        "Rooftop": ["rooftop", "roof top", "terrace"],
        "Romantic": ["romantic", "date night", "date-night"],
        "Nightlife": ["nightlife", "night life", "party vibe", "late night"],
        "Cocktails": ["cocktail", "mixology"],
        "Bar": ["bar", "resto-bar", "restobar"],
        "Live Music": ["live music", "live performance"],
        "Outdoor": ["outdoor", "open air", "open-air"],
        "Brewery": ["brewery", "craft beer", "fresh brew"],
        "Fine Dining": ["fine dining", "fine-dining"],
        "Casual Dining": ["casual dining", "casual-dining"],
        "Family": ["family dining", "family restaurant"],
        "Experience-led": ["immersive", "themed", "theme restaurant", "experience-led"],
        "Views": ["view", "skyline", "sunset"],
    }
    return [tag for tag, keywords in tag_map.items() if any(k in text for k in keywords)]


def parse_result(result):
    text = get_text(result)
    offers = extract_offers(text)
    return {
        "source": identify_source(result.get("url", "")),
        "rating": extract_rating(text),
        "review_count": extract_review_count(text),
        "cost_for_two": extract_cost_for_two(text),
        "offers": offers,
        "discount_percent": extract_discount_percent(offers),
        "cuisines": extract_cuisines(text),
        "positioning_tags": extract_positioning_tags(text),
        "title": result.get("title", ""),
        "snippet": result.get("snippet", ""),
        "url": result.get("url", ""),
        "extraction_method": "search_snippet",
        "confidence": "Medium",
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }


def extract_dining_metrics(primary_result=None, supporting_results=None):
    supporting_results = supporting_results or []
    results = []
    if primary_result:
        results.append(primary_result)
    results.extend(supporting_results)
    unique = {}
    for result in results:
        url = result.get("url", "")
        if url and "zomato.com" not in url.lower():
            unique[url] = result
    parsed = [parse_result(result) for result in unique.values()]
    by_source = {}
    for item in parsed:
        by_source.setdefault(item["source"], []).append(item)
    return {"by_source": by_source, "all_results": parsed, "direct_page_debug": []}


def summarize_source_results(source_results):
    if not source_results:
        return None
    ranked = sorted(
        source_results,
        key=lambda item: (
            item.get("confidence") == "High",
            item.get("extraction_method") == "direct_public_page",
            sum(v is not None for v in [item.get("rating"), item.get("review_count"), item.get("cost_for_two")]),
        ),
        reverse=True,
    )
    summary = {
        "rating": None, "review_count": None, "cost_for_two": None,
        "offers": [], "discount_percent": None, "cuisines": [],
        "positioning_tags": [], "confidence": "Medium",
        "method": "search_snippet", "url": None, "title": None,
    }
    for item in ranked:
        if item.get("confidence") == "High":
            summary["confidence"] = "High"
        if item.get("extraction_method") == "direct_public_page":
            summary["method"] = "direct_public_page"
        if summary["rating"] is None and item.get("rating") is not None:
            summary["rating"] = item["rating"]
        if summary["review_count"] is None and item.get("review_count") is not None:
            summary["review_count"] = item["review_count"]
        if summary["cost_for_two"] is None and item.get("cost_for_two") is not None:
            summary["cost_for_two"] = item["cost_for_two"]
        if summary["url"] is None and item.get("url"):
            summary["url"] = item["url"]
        if summary["title"] is None and item.get("title"):
            summary["title"] = item["title"]
        for offer in item.get("offers", []):
            normalized = normalize_offer(offer)
            if normalized and normalized.lower() not in [x.lower() for x in summary["offers"]]:
                summary["offers"].append(normalized)
        for cuisine in item.get("cuisines", []):
            if cuisine not in summary["cuisines"]:
                summary["cuisines"].append(cuisine)
        for tag in item.get("positioning_tags", []):
            if tag not in summary["positioning_tags"]:
                summary["positioning_tags"].append(tag)
    summary["discount_percent"] = extract_discount_percent(summary["offers"])
    return summary


def _walk_json(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _jsonld_metrics(soup):
    output = {"rating": None, "review_count": None, "cost_for_two": None, "cuisines": [], "address": None, "name": None}
    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    for script in scripts:
        raw = script.string or script.get_text(" ", strip=True)
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue
        for obj in _walk_json(payload):
            if output["name"] is None and isinstance(obj.get("name"), str):
                output["name"] = obj.get("name")
            aggregate = obj.get("aggregateRating")
            if isinstance(aggregate, dict):
                if output["rating"] is None:
                    try:
                        possible = float(aggregate.get("ratingValue"))
                        if 1 <= possible <= 5:
                            output["rating"] = possible
                    except (TypeError, ValueError):
                        pass
                if output["review_count"] is None:
                    raw_count = aggregate.get("ratingCount") or aggregate.get("reviewCount")
                    try:
                        output["review_count"] = int(str(raw_count).replace(",", ""))
                    except (TypeError, ValueError):
                        pass
            cuisine_value = obj.get("servesCuisine")
            if isinstance(cuisine_value, str):
                for cuisine in re.split(r"[,/]", cuisine_value):
                    cuisine = cuisine.strip()
                    if cuisine and cuisine not in output["cuisines"]:
                        output["cuisines"].append(cuisine)
            elif isinstance(cuisine_value, list):
                for cuisine in cuisine_value:
                    if isinstance(cuisine, str) and cuisine not in output["cuisines"]:
                        output["cuisines"].append(cuisine)
            price_range = obj.get("priceRange")
            if output["cost_for_two"] is None and isinstance(price_range, str):
                output["cost_for_two"] = extract_cost_for_two(price_range)
            address_value = obj.get("address")
            if output["address"] is None and isinstance(address_value, dict):
                parts = [address_value.get("streetAddress"), address_value.get("addressLocality"), address_value.get("addressRegion")]
                output["address"] = ", ".join([part for part in parts if part])
    return output


def extract_direct_page_metrics(url, timeout=8):
    url = canonicalize_restaurant_url(url)
    source = identify_source(url)
    debug = {"source": source, "url": url, "status_code": None, "error": None}
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        debug["status_code"] = response.status_code
        if response.status_code != 200:
            debug["error"] = f"HTTP {response.status_code}"
            return None, debug
        soup = BeautifulSoup(response.text, "html.parser")
        json_metrics = _jsonld_metrics(soup)
        visible_text = soup.get_text(" ", strip=True)
        combined_text = f"{visible_text} {response.text}"
        rating = json_metrics["rating"] or extract_rating(combined_text)
        review_count = json_metrics["review_count"] or extract_review_count(combined_text)
        cost_for_two = json_metrics["cost_for_two"] or extract_cost_for_two(combined_text)
        offers = extract_offers(visible_text)
        cuisines = list(json_metrics["cuisines"])
        for cuisine in extract_cuisines(visible_text):
            if cuisine not in cuisines:
                cuisines.append(cuisine)
        positioning_tags = extract_positioning_tags(visible_text)
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        found_any = any([rating is not None, review_count is not None, cost_for_two is not None, bool(offers), bool(cuisines), bool(positioning_tags)])
        if not found_any:
            debug["error"] = "Page loaded, but no supported dining metrics were detected."
            return None, debug
        result = {
            "source": source, "rating": rating, "review_count": review_count,
            "cost_for_two": cost_for_two, "offers": offers[:6],
            "discount_percent": extract_discount_percent(offers),
            "cuisines": cuisines[:12], "positioning_tags": positioning_tags[:12],
            "address": json_metrics["address"], "name": json_metrics["name"],
            "title": title or f"{source} public page",
            "snippet": "Metrics extracted directly from the publicly accessible restaurant page.",
            "url": canonicalize_restaurant_url(response.url),
            "extraction_method": "direct_public_page", "confidence": "High",
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }
        return result, debug
    except requests.RequestException as exc:
        debug["error"] = str(exc)
        return None, debug
    except Exception as exc:
        debug["error"] = f"Parser error: {exc}"
        return None, debug


def enrich_dining_metrics_with_pages(dining_metrics, urls):
    seen = set()
    for url in urls:
        canonical_url = canonicalize_restaurant_url(url)
        if not canonical_url or canonical_url in seen:
            continue
        seen.add(canonical_url)
        result, debug = extract_direct_page_metrics(canonical_url)
        dining_metrics.setdefault("direct_page_debug", []).append(debug)
        if not result:
            continue
        source_results = dining_metrics.setdefault("by_source", {}).setdefault(result["source"], [])
        source_results.insert(0, result)
        dining_metrics.setdefault("all_results", []).insert(0, result)
    return dining_metrics


def parse_social_number(value):
    if not value:
        return None
    value = value.replace(",", "").strip()
    multiplier = 1
    suffix = value[-1:].upper()
    if suffix == "K":
        multiplier = 1_000; value = value[:-1]
    elif suffix == "M":
        multiplier = 1_000_000; value = value[:-1]
    elif suffix == "B":
        multiplier = 1_000_000_000; value = value[:-1]
    try:
        return int(float(value) * multiplier)
    except ValueError:
        return None


def extract_instagram_metrics(result):
    if not result:
        return {"followers": None, "following": None, "posts": None, "handle": None, "bio": None, "url": None}
    title = result.get("title", "")
    snippet = result.get("snippet", "")
    url = result.get("url", "")
    text = f"{title} {snippet}"
    follower_match = re.search(r"([\d,.]+[KMB]?)\s+Followers", text, re.IGNORECASE)
    following_match = re.search(r"([\d,.]+[KMB]?)\s+Following", text, re.IGNORECASE)
    posts_match = re.search(r"([\d,]+)\s+Posts", text, re.IGNORECASE)
    handle_match = re.search(r"\(@([A-Za-z0-9._]+)\)", title)
    return {
        "followers": parse_social_number(follower_match.group(1)) if follower_match else None,
        "following": parse_social_number(following_match.group(1)) if following_match else None,
        "posts": parse_social_number(posts_match.group(1)) if posts_match else None,
        "handle": handle_match.group(1) if handle_match else None,
        "bio": snippet or None,
        "url": url or None,
    }


CONTENT_THEME_MAP = {
    "Food": ["food", "dish", "menu", "chicken", "pizza", "sushi", "dessert", "bite"],
    "Ambience": ["ambience", "ambiance", "rooftop", "interior", "view", "sunset", "vibe"],
    "Drinks": ["cocktail", "beer", "brew", "drink", "bar", "pour"],
    "People": ["people", "team", "staff", "friends", "couple"],
    "Behind the scenes": ["behindthescenes", "behind the scenes", "staff fun", "chaos", "episode"],
    "Offers": ["offer", "discount", "% off", "deal"],
    "Events": ["event", "dj", "live music", "gig", "performance"],
    "Experience": ["date night", "nightlife", "experience", "romantic", "evening"],
}


def classify_content_theme(text):
    lower = (text or "").lower()
    scores = []
    for theme, keywords in CONTENT_THEME_MAP.items():
        score = sum(keyword in lower for keyword in keywords)
        if score:
            scores.append((score, theme))
    if not scores:
        return "Other"
    scores.sort(reverse=True)
    return scores[0][1]


def extract_instagram_content_items(results, restaurant_handle=None):
    items = []
    restaurant_handle = (restaurant_handle or "").lower()
    for result in results or []:
        url = result.get("url", "")
        lower_url = url.lower()
        if "instagram.com" not in lower_url or not any(marker in lower_url for marker in ["/reel/", "/p/"]):
            continue
        snippet = result.get("snippet", "")
        title = result.get("title", "")
        text = f"{title} {snippet}"
        likes_match = re.search(r"([\d,]+)\s+likes", text, re.IGNORECASE)
        comments_match = re.search(r"([\d,]+)\s+comments", text, re.IGNORECASE)
        author_match = re.search(r"-\s*([A-Za-z0-9._]+)\s+on\s+[A-Z][a-z]+\s+\d{1,2},\s+\d{4}", snippet)
        likes = int(likes_match.group(1).replace(",", "")) if likes_match else None
        comments = int(comments_match.group(1).replace(",", "")) if comments_match else None
        author = author_match.group(1) if author_match else None
        owned = bool(restaurant_handle and (restaurant_handle in (author or "").lower() or restaurant_handle in title.lower()))
        items.append({
            "title": title, "url": url, "snippet": snippet, "likes": likes,
            "comments": comments,
            "engagement": (likes or 0) + (comments or 0) if likes is not None or comments is not None else None,
            "author": author, "type": "Owned" if owned else "Creator / UGC",
            "theme": classify_content_theme(text),
        })
    return items


def summarize_content_items(items):
    if not items:
        return {"sample_size": 0, "owned_count": 0, "creator_count": 0, "median_owned_engagement": None, "median_creator_engagement": None, "creator_lift": None, "themes": []}
    owned = [x for x in items if x["type"] == "Owned"]
    creator = [x for x in items if x["type"] != "Owned"]
    owned_engagement = [x["engagement"] for x in owned if x["engagement"] is not None]
    creator_engagement = [x["engagement"] for x in creator if x["engagement"] is not None]
    theme_data = {}
    for item in items:
        bucket = theme_data.setdefault(item["theme"], {"theme": item["theme"], "posts": 0, "engagement_values": []})
        bucket["posts"] += 1
        if item["engagement"] is not None:
            bucket["engagement_values"].append(item["engagement"])
    themes = []
    for bucket in theme_data.values():
        values = bucket.pop("engagement_values")
        bucket["median_visible_engagement"] = median(values) if values else None
        themes.append(bucket)
    themes.sort(key=lambda row: (row["median_visible_engagement"] is not None, row["median_visible_engagement"] or 0, row["posts"]), reverse=True)
    owned_median = median(owned_engagement) if owned_engagement else None
    creator_median = median(creator_engagement) if creator_engagement else None
    creator_lift = creator_median / owned_median if owned_median and creator_median is not None else None
    return {
        "sample_size": len(items), "owned_count": len(owned), "creator_count": len(creator),
        "median_owned_engagement": owned_median, "median_creator_engagement": creator_median,
        "creator_lift": creator_lift, "themes": themes,
    }
