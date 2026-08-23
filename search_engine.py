from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from difflib import SequenceMatcher
from time import perf_counter

from ddgs import DDGS


EXCLUDED_PRODUCT_DOMAINS = ["zomato.com"]
LOW_VALUE_INSTAGRAM_DOMAINS = [
    "igtrackr.com",
    "igdetective.com",
    "inflact.com",
    "igtrackers.com",
]
MAX_SEARCH_WORKERS = 6


@lru_cache(maxsize=512)
def search_web(query, max_results=10):
    """Free public-web search with process-level caching."""
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


def _parallel_query_responses(query_specs, max_workers=MAX_SEARCH_WORKERS):
    """Execute independent search queries concurrently and return keyed responses."""
    responses = {}
    if not query_specs:
        return responses

    workers = min(max_workers, len(query_specs))
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        future_map = {
            executor.submit(search_web, query, max_results): key
            for key, query, max_results in query_specs
        }
        for future in as_completed(future_map):
            key = future_map[future]
            try:
                responses[key] = future.result()
            except Exception as exc:
                responses[key] = {"results": [], "error": str(exc)}

    return responses


def search_multiple(queries, max_results=5):
    """Run a group of searches concurrently while preserving query order."""
    started = perf_counter()
    specs = [
        (index, query, max_results)
        for index, query in enumerate(queries)
    ]
    responses = _parallel_query_responses(specs)

    combined = []
    errors = []
    for index, query in enumerate(queries):
        response = responses.get(index, {"results": [], "error": "Search did not return."})
        combined.extend(response["results"])
        if response["error"]:
            errors.append({"query": query, "error": response["error"]})

    return {
        "results": deduplicate_results(combined),
        "errors": errors,
        "elapsed_ms": round((perf_counter() - started) * 1000),
    }


def search_tagged(queries, max_results=10):
    """Run searches concurrently and retain the query that produced each result."""
    started = perf_counter()
    specs = [
        (index, query, max_results)
        for index, query in enumerate(queries)
    ]
    responses = _parallel_query_responses(specs)

    tagged = []
    errors = []
    for index, query in enumerate(queries):
        response = responses.get(index, {"results": [], "error": "Search did not return."})
        for result in response["results"]:
            item = dict(result)
            item["query"] = query
            tagged.append(item)
        if response["error"]:
            errors.append({"query": query, "error": response["error"]})

    return {
        "results": tagged,
        "errors": errors,
        "elapsed_ms": round((perf_counter() - started) * 1000),
    }


def search_grouped(query_groups, max_results_by_group=None, default_max_results=8):
    """Execute a complete multi-category search plan in one concurrent pool."""
    started = perf_counter()
    max_results_by_group = max_results_by_group or {}

    specs = []
    ordered_keys = []
    for group, queries in query_groups.items():
        for index, query in enumerate(queries):
            key = (group, index)
            ordered_keys.append((key, group, query))
            specs.append(
                (
                    key,
                    query,
                    max_results_by_group.get(group, default_max_results),
                )
            )

    responses = _parallel_query_responses(specs)
    output = {
        group: {"results": [], "errors": []}
        for group in query_groups
    }

    for key, group, query in ordered_keys:
        response = responses.get(key, {"results": [], "error": "Search did not return."})
        output[group]["results"].extend(response["results"])
        if response["error"]:
            output[group]["errors"].append(
                {"query": query, "error": response["error"]}
            )

    for group in output:
        output[group]["results"] = deduplicate_results(output[group]["results"])

    output["elapsed_ms"] = round((perf_counter() - started) * 1000)
    return output


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

        # Prefer restaurant-detail pages over category/home/book-only pages.
        if "/dining/" in url and not url.rstrip("/").endswith("/dining"):
            score += 0.08
        if url.rstrip("/").endswith("/book"):
            score -= 0.08

        candidates.append((score, result))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def annotate_domain_candidates(results, restaurant_name, domain):
    """Expose resolver scoring so the Data Lab can show why a result was chosen."""
    annotated = []
    for result in results:
        url = result.get("url", "")
        if domain.lower() not in url.lower():
            continue
        score = similarity(restaurant_name, result.get("title", ""))
        detail_page = "/dining/" in url.lower() and not url.lower().rstrip("/").endswith("/dining")
        book_only = url.lower().rstrip("/").endswith("/book")
        adjusted = score + (0.08 if detail_page else 0) - (0.08 if book_only else 0)
        annotated.append(
            {
                **result,
                "name_similarity": round(score, 3),
                "resolver_score": round(max(0, min(1, adjusted)), 3),
                "detail_page": detail_page,
                "book_only": book_only,
            }
        )
    annotated.sort(key=lambda item: item["resolver_score"], reverse=True)
    return annotated


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
    query_groups = {
        "general": [
            f"{restaurant} restaurant {location}",
            f"{restaurant} {location} reviews dining",
        ],
        "district": [
            f"{restaurant} {location} District dining",
            f"site:district.in/dining {restaurant} {location}",
        ],
        "metric": [
            f'"{restaurant}" "{location}" cost for two offer',
            f'"{restaurant}" "{location}" rating reviews price',
            f'"{restaurant}" "{location}" cuisine date night rooftop',
        ],
        "dineout": [
            f"{restaurant} {location} Swiggy Dineout",
            f"{restaurant} Dineout {location}",
        ],
        "instagram": [
            f"{restaurant} {location} Instagram",
            f"{restaurant} Instagram followers posts",
        ],
        "website": [
            f"{restaurant} {location} official website",
        ],
    }

    plan = search_grouped(
        query_groups,
        max_results_by_group={
            "general": 8,
            "district": 7,
            "metric": 7,
            "dineout": 6,
            "instagram": 8,
            "website": 8,
        },
    )

    general_results = filter_out_domains(
        plan["general"]["results"],
        EXCLUDED_PRODUCT_DOMAINS,
    )

    district_candidates = filter_out_domains(
        plan["district"]["results"],
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

    metric_candidates = filter_out_domains(
        plan["metric"]["results"],
        EXCLUDED_PRODUCT_DOMAINS,
    )

    dineout_candidates = filter_out_domains(
        plan["dineout"]["results"],
        EXCLUDED_PRODUCT_DOMAINS,
    )
    dineout = find_best_domain_result(
        dineout_candidates,
        ["swiggy.com"],
        restaurant,
    )

    instagram_candidates = filter_out_domains(
        plan["instagram"]["results"],
        EXCLUDED_PRODUCT_DOMAINS + LOW_VALUE_INSTAGRAM_DOMAINS,
    )
    instagram = find_best_instagram_profile(
        instagram_candidates,
        restaurant,
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
    for result in plan["website"]["results"]:
        url = result.get("url", "").lower()
        if not any(domain in url for domain in excluded_domains):
            website = result
            break

    debug = {
        "general_errors": plan["general"]["errors"],
        "district_errors": plan["district"]["errors"],
        "metric_errors": plan["metric"]["errors"],
        "dineout_errors": plan["dineout"]["errors"],
        "instagram_errors": plan["instagram"]["errors"],
        "website_errors": plan["website"]["errors"],
        "district_candidates": district_candidates,
        "district_candidate_scores": annotate_domain_candidates(
            district_candidates,
            restaurant,
            "district.in",
        ),
        "metric_candidates": metric_candidates,
        "dineout_candidates": dineout_candidates,
        "instagram_candidates": instagram_candidates,
        "search_elapsed_ms": plan["elapsed_ms"],
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
    positioning_tags=None,
):
    """Collect the highest-value public evidence without serial search blocking."""
    competitor_names = competitor_names or []
    positioning_tags = positioning_tags or []

    discovery_queries = [
        f"best restaurants {location}",
        f"date night restaurants {location}",
        f"romantic restaurants {location}",
    ]
    lowered_tags = {tag.lower() for tag in positioning_tags}
    if lowered_tags & {"rooftop", "views", "outdoor"}:
        discovery_queries.append(f"rooftop restaurants {location}")
    elif lowered_tags & {"nightlife", "bar", "cocktails", "brewery"}:
        discovery_queries.append(f"best bars {location}")
    else:
        discovery_queries.append(f"popular restaurants {location}")

    creator_queries = [
        f'"{restaurant}" "{location}" Instagram reel review',
    ]
    if instagram_handle:
        creator_queries.append(f'"@{instagram_handle}" review reel')
    else:
        creator_queries.append(f'"{restaurant}" "{location}" creator review')

    query_groups = {
        "reviews": [
            f'"{restaurant}" "{location}" reviews ambience service food value',
            f'"{restaurant}" "{location}" review slow service date night drinks',
        ],
        "creators": creator_queries,
        "earned": [
            f'"{restaurant}" "{location}" restaurant review nightlife rooftop',
        ],
        "paid": [
            f'"{restaurant}" Meta Ad Library',
        ],
        "discovery": discovery_queries,
    }

    plan = search_grouped(
        query_groups,
        max_results_by_group={
            "reviews": 8,
            "creators": 8,
            "earned": 8,
            "paid": 5,
            "discovery": 8,
        },
    )

    discovery_results = []
    for query in discovery_queries:
        # Tag each result with the exact discovery query that surfaced it.
        response = search_web(query, 8)
        for result in response["results"]:
            item = dict(result)
            item["query"] = query
            discovery_results.append(item)

    all_errors = []
    for group in ["reviews", "creators", "earned", "paid", "discovery"]:
        for error in plan[group]["errors"]:
            all_errors.append({"group": group, **error})

    return {
        "reviews": filter_out_domains(
            plan["reviews"]["results"],
            EXCLUDED_PRODUCT_DOMAINS,
        ),
        "creators": filter_out_domains(
            plan["creators"]["results"],
            EXCLUDED_PRODUCT_DOMAINS,
        ),
        "earned": filter_out_domains(
            plan["earned"]["results"],
            EXCLUDED_PRODUCT_DOMAINS,
        ),
        "paid": filter_out_domains(
            plan["paid"]["results"],
            EXCLUDED_PRODUCT_DOMAINS,
        ),
        "discovery": filter_out_domains(
            discovery_results,
            EXCLUDED_PRODUCT_DOMAINS,
        ),
        "competitor_names": competitor_names,
        "errors": all_errors,
        "elapsed_ms": plan["elapsed_ms"],
    }
