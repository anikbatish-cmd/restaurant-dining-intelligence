from functools import lru_cache
from difflib import SequenceMatcher

from ddgs import DDGS


EXCLUDED_PRODUCT_DOMAINS = ["zomato.com"]


@lru_cache(maxsize=256)
def search_web(query, max_results=10):
    """Free web-search helper with in-process caching."""
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

    except Exception as exc:
        return {"results": [], "error": str(exc)}


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


def filter_out_domains(results, domains):
    filtered = []

    for result in results:
        url = result.get("url", "").lower()
        if any(domain.lower() in url for domain in domains):
            continue
        filtered.append(result)

    return filtered


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


def search_tagged(queries, max_results=10):
    tagged = []
    errors = []

    for query in queries:
        response = search_web(query, max_results=max_results)

        for result in response["results"]:
            item = dict(result)
            item["query"] = query
            tagged.append(item)

        if response["error"]:
            errors.append({"query": query, "error": response["error"]})

    return {
        "results": tagged,
        "errors": errors,
    }


def clean_name(text):
    return (
        (text or "")
        .lower()
        .replace("-", " ")
        .replace("|", " ")
        .replace(",", " ")
        .replace("–", " ")
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
    candidates = []

    for result in results:
        url = result.get("url", "").lower()
        title = result.get("title", "")
        snippet = result.get("snippet", "")

        if "instagram.com" not in url:
            continue

        if any(
            marker in url
            for marker in [
                "/popular/",
                "/reel/",
                "/reels/",
                "/p/",
                "/explore/",
                "/stories/",
            ]
        ):
            continue

        score = similarity(restaurant_name, title)

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
    """Resolve the target restaurant across the public dining ecosystem."""
    general_search = search_multiple(
        [
            f"{restaurant} restaurant {location}",
            f"{restaurant} {location} reviews dining",
        ],
        max_results=10,
    )
    general_results = filter_out_domains(
        general_search["results"],
        EXCLUDED_PRODUCT_DOMAINS,
    )

    district_search = search_multiple(
        [
            f"{restaurant} {location} District dining",
            f"site:district.in/dining {restaurant} {location}",
        ],
        max_results=7,
    )
    district_candidates = filter_out_domains(
        district_search["results"],
        EXCLUDED_PRODUCT_DOMAINS,
    )

    district = find_best_domain_result(
        district_candidates,
        ["district.in"],
        restaurant,
    )
    if not district:
        district = find_best_domain_result(
            general_results,
            ["district.in"],
            restaurant,
        )

    metric_search = search_multiple(
        [
            f'"{restaurant}" "{location}" cost for two offer',
            f'"{restaurant}" "{location}" rating reviews price',
            f'"{restaurant}" "{location}" cuisine date night rooftop',
        ],
        max_results=8,
    )
    metric_candidates = filter_out_domains(
        metric_search["results"],
        EXCLUDED_PRODUCT_DOMAINS,
    )

    dineout_search = search_multiple(
        [
            f"{restaurant} {location} Swiggy Dineout",
            f"{restaurant} Dineout {location}",
        ],
        max_results=6,
    )
    dineout_candidates = filter_out_domains(
        dineout_search["results"],
        EXCLUDED_PRODUCT_DOMAINS,
    )
    dineout = find_best_domain_result(
        dineout_candidates,
        ["swiggy.com"],
        restaurant,
    )

    instagram_search = search_multiple(
        [
            f"{restaurant} {location} Instagram",
            f"{restaurant} Instagram followers posts",
        ],
        max_results=8,
    )
    instagram_candidates = filter_out_domains(
        instagram_search["results"],
        EXCLUDED_PRODUCT_DOMAINS,
    )
    instagram = find_best_instagram_profile(
        instagram_candidates,
        restaurant,
    )

    website_search = search_multiple(
        [f"{restaurant} {location} official website"],
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
        "district_errors": district_search["errors"],
        "metric_errors": metric_search["errors"],
        "dineout_errors": dineout_search["errors"],
        "instagram_errors": instagram_search["errors"],
        "website_errors": website_search["errors"],
        "district_candidates": district_candidates,
        "metric_candidates": metric_candidates,
        "dineout_candidates": dineout_candidates,
        "instagram_candidates": instagram_candidates,
    }

    return {
        "restaurant": restaurant,
        "location": location,
        "district": district,
        "dineout": dineout,
        "instagram": instagram,
        "website": website,
        "general_results": general_results,
        "debug": debug,
    }


def collect_public_intelligence(
    restaurant,
    location,
    instagram_handle=None,
    competitor_names=None,
):
    """Collect review, creator, earned-media, paid-signal and discovery evidence."""
    competitor_names = competitor_names or []

    review_search = search_multiple(
        [
            f'"{restaurant}" "{location}" reviews ambience service food value',
            f'"{restaurant}" "{location}" customer review slow service ambience',
            f'"{restaurant}" "{location}" reviews date night drinks rooftop',
        ],
        max_results=8,
    )

    creator_queries = [
        f'"{restaurant}" "{location}" Instagram reel review',
        f'"{restaurant}" "{location}" creator food blogger',
    ]
    if instagram_handle:
        creator_queries.append(f'"@{instagram_handle}" review reel')

    creator_search = search_multiple(
        creator_queries,
        max_results=8,
    )

    earned_search = search_multiple(
        [
            f'"{restaurant}" "{location}" restaurant review magazine',
            f'"{restaurant}" "{location}" food publication nightlife rooftop',
        ],
        max_results=8,
    )

    paid_search = search_multiple(
        [
            f'"{restaurant}" Meta Ad Library',
            f'"{restaurant}" sponsored Instagram ad',
        ],
        max_results=6,
    )

    discovery_queries = [
        f"best restaurants {location}",
        f"date night restaurants {location}",
        f"romantic restaurants {location}",
        f"best bars {location}",
        f"rooftop restaurants {location}",
    ]

    discovery = search_tagged(
        discovery_queries,
        max_results=10,
    )

    return {
        "reviews": filter_out_domains(
            review_search["results"],
            EXCLUDED_PRODUCT_DOMAINS,
        ),
        "creators": filter_out_domains(
            creator_search["results"],
            EXCLUDED_PRODUCT_DOMAINS,
        ),
        "earned": filter_out_domains(
            earned_search["results"],
            EXCLUDED_PRODUCT_DOMAINS,
        ),
        "paid": filter_out_domains(
            paid_search["results"],
            EXCLUDED_PRODUCT_DOMAINS,
        ),
        "discovery": filter_out_domains(
            discovery["results"],
            EXCLUDED_PRODUCT_DOMAINS,
        ),
        "competitor_names": competitor_names,
        "errors": (
            review_search["errors"]
            + creator_search["errors"]
            + earned_search["errors"]
            + paid_search["errors"]
            + discovery["errors"]
        ),
    }
