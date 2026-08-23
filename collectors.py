import json
import re
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

    if "zomato.com" in url:
        return "Zomato"
    if "district.in" in url:
        return "District"
    if "swiggy.com" in url:
        return "Swiggy Dineout"
    if "eazydiner.com" in url:
        return "EazyDiner"
    if "justdial.com" in url:
        return "Justdial"

    return "Web"


def canonicalize_restaurant_url(url):
    if not url:
        return url

    parts = urlsplit(url)
    path = parts.path.rstrip("/")

    if "swiggy.com" in parts.netloc.lower():
        path = re.sub(r"/(photos|menu)$", "", path, flags=re.IGNORECASE)

    if "zomato.com" in parts.netloc.lower():
        path = re.sub(r"/(menu|reviews)$", "", path, flags=re.IGNORECASE)

    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def get_text(result):
    if not result:
        return ""

    return " ".join(
        [
            result.get("title", ""),
            result.get("snippet", ""),
        ]
    )


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
        r"([\d,]+)\s+ratings",
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
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            clean = normalize_offer(match)
            if not clean:
                continue

            key = clean.lower()
            if key not in seen:
                seen.add(key)
                offers.append(clean)

    return offers


def extract_cuisines(text):
    known = [
        "North Indian",
        "Chinese",
        "Italian",
        "Continental",
        "Asian",
        "Japanese",
        "Mediterranean",
        "Thai",
        "Sushi",
        "Mexican",
        "Lebanese",
        "Mughlai",
        "Desserts",
        "Beverages",
        "Cafe",
        "Bar Food",
        "Fusion",
        "Multi Cuisine",
    ]

    return [
        cuisine
        for cuisine in known
        if cuisine.lower() in text.lower()
    ]


def parse_result(result):
    text = get_text(result)

    return {
        "source": identify_source(result.get("url", "")),
        "rating": extract_rating(text),
        "review_count": extract_review_count(text),
        "cost_for_two": extract_cost_for_two(text),
        "offers": extract_offers(text),
        "cuisines": extract_cuisines(text),
        "title": result.get("title", ""),
        "snippet": result.get("snippet", ""),
        "url": result.get("url", ""),
        "extraction_method": "search_snippet",
        "confidence": "Medium",
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
        if url:
            unique[url] = result

    parsed = [parse_result(result) for result in unique.values()]
    by_source = {}

    for item in parsed:
        source = item["source"]
        by_source.setdefault(source, []).append(item)

    return {
        "by_source": by_source,
        "all_results": parsed,
        "direct_page_debug": [],
    }


def summarize_source_results(source_results):
    if not source_results:
        return None

    ranked = sorted(
        source_results,
        key=lambda item: (
            item.get("confidence") == "High",
            item.get("extraction_method") == "direct_public_page",
        ),
        reverse=True,
    )

    summary = {
        "rating": None,
        "review_count": None,
        "cost_for_two": None,
        "offers": [],
        "cuisines": [],
        "confidence": "Medium",
        "method": "search_snippet",
        "url": None,
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

        for offer in item.get("offers", []):
            normalized = normalize_offer(offer)
            if normalized and normalized.lower() not in [x.lower() for x in summary["offers"]]:
                summary["offers"].append(normalized)

        for cuisine in item.get("cuisines", []):
            if cuisine not in summary["cuisines"]:
                summary["cuisines"].append(cuisine)

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
    rating = None
    review_count = None
    cost_for_two = None
    cuisines = []

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
            aggregate = obj.get("aggregateRating")
            if isinstance(aggregate, dict):
                if rating is None:
                    try:
                        possible = float(aggregate.get("ratingValue"))
                        if 1 <= possible <= 5:
                            rating = possible
                    except (TypeError, ValueError):
                        pass

                if review_count is None:
                    raw_count = aggregate.get("ratingCount") or aggregate.get("reviewCount")
                    try:
                        review_count = int(str(raw_count).replace(",", ""))
                    except (TypeError, ValueError):
                        pass

            cuisine_value = obj.get("servesCuisine")
            if isinstance(cuisine_value, str):
                for cuisine in re.split(r"[,/]", cuisine_value):
                    cuisine = cuisine.strip()
                    if cuisine and cuisine not in cuisines:
                        cuisines.append(cuisine)
            elif isinstance(cuisine_value, list):
                for cuisine in cuisine_value:
                    if isinstance(cuisine, str) and cuisine not in cuisines:
                        cuisines.append(cuisine)

            price_range = obj.get("priceRange")
            if cost_for_two is None and isinstance(price_range, str):
                cost_for_two = extract_cost_for_two(price_range)

    return rating, review_count, cost_for_two, cuisines


def extract_direct_page_metrics(url, timeout=7):
    url = canonicalize_restaurant_url(url)
    source = identify_source(url)

    debug = {
        "source": source,
        "url": url,
        "status_code": None,
        "error": None,
    }

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=timeout,
            allow_redirects=True,
        )
        debug["status_code"] = response.status_code

        if response.status_code != 200:
            debug["error"] = f"HTTP {response.status_code}"
            return None, debug

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            if tag.name != "script" or tag.get("type") != "application/ld+json":
                tag.decompose()

        visible_text = soup.get_text(" ", strip=True)
        html_text = response.text
        combined_text = f"{visible_text} {html_text}"

        json_rating, json_reviews, json_price, json_cuisines = _jsonld_metrics(soup)

        rating = json_rating or extract_rating(combined_text)
        review_count = json_reviews or extract_review_count(combined_text)
        cost_for_two = json_price or extract_cost_for_two(combined_text)
        offers = extract_offers(visible_text)

        cuisines = list(json_cuisines)
        for cuisine in extract_cuisines(visible_text):
            if cuisine not in cuisines:
                cuisines.append(cuisine)

        title = ""
        if soup.title:
            title = soup.title.get_text(" ", strip=True)

        found_any = any(
            [
                rating is not None,
                review_count is not None,
                cost_for_two is not None,
                bool(offers),
                bool(cuisines),
            ]
        )

        if not found_any:
            debug["error"] = "Page loaded, but no supported dining metrics were detected."
            return None, debug

        result = {
            "source": source,
            "rating": rating,
            "review_count": review_count,
            "cost_for_two": cost_for_two,
            "offers": offers[:5],
            "cuisines": cuisines[:12],
            "title": title or f"{source} public page",
            "snippet": "Metrics extracted directly from the publicly accessible restaurant page.",
            "url": canonicalize_restaurant_url(response.url),
            "extraction_method": "direct_public_page",
            "confidence": "High",
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

        source = result["source"]
        source_results = dining_metrics.setdefault("by_source", {}).setdefault(source, [])
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
        multiplier = 1_000
        value = value[:-1]
    elif suffix == "M":
        multiplier = 1_000_000
        value = value[:-1]
    elif suffix == "B":
        multiplier = 1_000_000_000
        value = value[:-1]

    try:
        return int(float(value) * multiplier)
    except ValueError:
        return None


def extract_instagram_metrics(result):
    if not result:
        return {
            "followers": None,
            "following": None,
            "posts": None,
            "handle": None,
            "bio": None,
            "url": None,
        }

    title = result.get("title", "")
    snippet = result.get("snippet", "")
    url = result.get("url", "")
    text = f"{title} {snippet}"

    follower_match = re.search(
        r"([\d,.]+[KMB]?)\s+Followers",
        text,
        re.IGNORECASE,
    )
    following_match = re.search(
        r"([\d,.]+[KMB]?)\s+Following",
        text,
        re.IGNORECASE,
    )
    posts_match = re.search(
        r"([\d,]+)\s+Posts",
        text,
        re.IGNORECASE,
    )
    handle_match = re.search(
        r"\(@([A-Za-z0-9._]+)\)",
        title,
    )

    return {
        "followers": parse_social_number(follower_match.group(1)) if follower_match else None,
        "following": parse_social_number(following_match.group(1)) if following_match else None,
        "posts": parse_social_number(posts_match.group(1)) if posts_match else None,
        "handle": handle_match.group(1) if handle_match else None,
        "bio": snippet or None,
        "url": url or None,
    }
