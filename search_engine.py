from ddgs import DDGS
from difflib import SequenceMatcher


def search_web(query, max_results=10):
    try:
        results = DDGS().text(
            query,
            region="in-en",
            safesearch="moderate",
            max_results=max_results,
        )

        output = []
        for result in results or []:
            output.append(
                {
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", ""),
                }
            )

        return {"results": output, "error": None}

    except Exception as e:
        return {"results": [], "error": str(e)}


def deduplicate_results(results):
    seen = set()
    clean = []

    for result in results:
        url = result.get("url", "")
        if not url or url in seen:
            continue
        seen.add(url)
        clean.append(result)

    return clean


def search_multiple(queries, max_results=5):
    combined = []
    errors = []

    for query in queries:
        response = search_web(query, max_results=max_results)
        combined.extend(response["results"])

        if response["error"]:
            errors.append({"query": query, "error": response["error"]})

    return {
        "results": deduplicate_results(combined),
        "errors": errors,
    }


def clean_name(text):
    return (
        text.lower()
        .replace("-", " ")
        .replace("|", " ")
        .replace(",", " ")
        .strip()
    )


def similarity(a, b):
    return SequenceMatcher(
        None,
        clean_name(a),
        clean_name(b),
    ).ratio()


def find_best_domain_result(results, domains, restaurant_name):
    candidates = []

    for result in results:
        url = result.get("url", "").lower()

        if not any(domain.lower() in url for domain in domains):
            continue

        title = result.get("title", "")
        score = similarity(restaurant_name, title)
        candidates.append((score, result))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def find_best_instagram_profile(results, restaurant_name):
    """Prefer an actual Instagram account profile over popular/reel/post URLs."""
    candidates = []

    for result in results:
        url = result.get("url", "").lower()
        title = result.get("title", "")
        snippet = result.get("snippet", "")

        if "instagram.com" not in url:
            continue

        # Ignore obvious content/discovery pages when choosing the restaurant profile.
        if any(
            marker in url
            for marker in [
                "/popular/",
                "/reel/",
                "/reels/",
                "/p/",
                "/explore/",
            ]
        ):
            continue

        score = similarity(restaurant_name, title)

        # Strongly prefer results that look like account-profile snippets.
        if "followers" in snippet.lower():
            score += 0.40
        if "posts" in snippet.lower():
            score += 0.20
        if "(@" in title:
            score += 0.20

        candidates.append((score, result))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def resolve_restaurant(restaurant, location):
    # GENERAL SEARCH
    general_search = search_multiple(
        [
            f"{restaurant} {location}",
            f"{restaurant} restaurant {location}",
        ],
        max_results=10,
    )
    general_results = general_search["results"]

    # ZOMATO / DISTRICT DISCOVERY
    zomato_search = search_multiple(
        [
            f"{restaurant} {location} Zomato",
            f"{restaurant} Zomato {location}",
            f"{restaurant} {location} District dining",
            f"{restaurant} {location} zomato restaurant",
        ],
        max_results=5,
    )

    zomato = find_best_domain_result(
        zomato_search["results"],
        ["zomato.com", "district.in"],
        restaurant,
    )

    if not zomato:
        zomato = find_best_domain_result(
            general_results,
            ["zomato.com", "district.in"],
            restaurant,
        )

    # TARGETED DINING-METRIC SEARCH
    # These queries often surface richer snippets containing rating, price,
    # cuisines or dining offers even when the canonical listing result does not.
    metric_search = search_multiple(
        [
            f'"{restaurant}" "{location}" rating "for two"',
            f'"{restaurant}" "{location}" dining rating price',
            f'"{restaurant}" "{location}" cost for two offer',
            f'"{restaurant}" "{location}" restaurant rating reviews price',
            f'"{restaurant}" "{location}" District rating offer',
            f'"{restaurant}" "{location}" Dineout rating offer',
        ],
        max_results=8,
    )

    # SWIGGY DINEOUT
    dineout_search = search_multiple(
        [
            f"{restaurant} {location} Swiggy Dineout",
            f"{restaurant} Dineout {location}",
            f"{restaurant} {location} Swiggy restaurant",
        ],
        max_results=5,
    )

    dineout = find_best_domain_result(
        dineout_search["results"],
        ["swiggy.com"],
        restaurant,
    )

    if not dineout:
        dineout = find_best_domain_result(
            general_results,
            ["swiggy.com"],
            restaurant,
        )

    # INSTAGRAM
    instagram_search = search_multiple(
        [
            f"{restaurant} {location} Instagram",
            f"{restaurant} official Instagram",
            f"{restaurant} Instagram followers posts",
        ],
        max_results=7,
    )

    instagram = find_best_instagram_profile(
        instagram_search["results"],
        restaurant,
    )

    # OFFICIAL WEBSITE
    website_search = search_multiple(
        [
            f"{restaurant} {location} official website",
            f"{restaurant} restaurant website",
        ],
        max_results=10,
    )

    excluded_domains = [
        "zomato.com",
        "district.in",
        "swiggy.com",
        "instagram.com",
        "facebook.com",
        "youtube.com",
        "tripadvisor",
        "magicpin",
        "eazydiner",
        "google.com",
        "justdial.com",
    ]

    website = None
    for result in website_search["results"]:
        url = result.get("url", "").lower()
        if not any(domain in url for domain in excluded_domains):
            website = result
            break

    debug = {
        "general_errors": general_search["errors"],
        "zomato_errors": zomato_search["errors"],
        "metric_errors": metric_search["errors"],
        "dineout_errors": dineout_search["errors"],
        "instagram_errors": instagram_search["errors"],
        "website_errors": website_search["errors"],
        "zomato_candidates": zomato_search["results"],
        "metric_candidates": metric_search["results"],
        "dineout_candidates": dineout_search["results"],
        "instagram_candidates": instagram_search["results"],
    }

    return {
        "restaurant": restaurant,
        "location": location,
        "zomato": zomato,
        "dineout": dineout,
        "instagram": instagram,
        "website": website,
        "general_results": general_results,
        "debug": debug,
    }
