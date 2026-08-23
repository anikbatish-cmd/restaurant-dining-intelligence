import re


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


def get_text(result):
    if not result:
        return ""

    return " ".join([
        result.get("title", ""),
        result.get("snippet", "")
    ])


def extract_rating(text):
    patterns = [
        r"rated\s+([1-5]\.\d)",
        r"\b([1-5]\.\d)\s+(?:rating|ratings|reviews)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return float(match.group(1))

    return None


def extract_review_count(text):
    patterns = [
        r"based on\s+([\d,]+)\s+(?:customer\s+)?reviews",
        r"([\d,]+)\s+ratings",
        r"([\d,]+)\s+reviews",
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
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            try:
                return int(match.group(1).replace(",", ""))
            except ValueError:
                pass

    return None


def extract_offers(text):
    patterns = [
        r"(flat\s+\d+%\s+off)",
        r"(up\s+to\s+\d+%\s+off)",
        r"(upto\s+\d+%\s+off)",
        r"(\d+%\s+discount)",
    ]

    offers = []

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)

        for match in matches:
            clean = match.strip()

            if clean.lower() not in [x.lower() for x in offers]:
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
    }


def extract_dining_metrics(
    primary_result=None,
    supporting_results=None,
):
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

        if source not in by_source:
            by_source[source] = []

        by_source[source].append(item)

    return {
        "by_source": by_source,
        "all_results": parsed,
    }


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
    """Extract basic public Instagram account metrics from search-result snippets."""
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
