from ddgs import DDGS


def search_web(query, max_results=10):
    """
    Free search helper.
    Returns structured results instead of silently failing.
    """

    try:
        results = DDGS().text(
            query,
            region="in-en",
            safesearch="moderate",
            max_results=max_results,
        )

        output = []

        for r in results or []:
            output.append(
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                }
            )

        return {
            "results": output,
            "error": None,
        }

    except Exception as e:
        return {
            "results": [],
            "error": str(e),
        }


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
    """
    Run multiple search variants and combine them.
    """

    combined = []
    errors = []

    for query in queries:

        response = search_web(
            query,
            max_results=max_results,
        )

        combined.extend(response["results"])

        if response["error"]:
            errors.append(
                {
                    "query": query,
                    "error": response["error"],
                }
            )

    return {
        "results": deduplicate_results(combined),
        "errors": errors,
    }


def find_domain_result(results, domains):
    """
    Find first search result matching one of the domains.
    """

    for result in results:

        url = result.get("url", "").lower()

        if any(
            domain.lower() in url
            for domain in domains
        ):
            return result

    return None


def resolve_restaurant(restaurant, location):

    # --------------------
    # GENERAL SEARCH
    # --------------------

    general_search = search_multiple(
        [
            f"{restaurant} {location}",
            f"{restaurant} restaurant {location}",
            f"{restaurant} Gurgaon restaurant"
            if "gurgaon" in location.lower()
            or "gurugram" in location.lower()
            else f"{restaurant} {location} restaurant",
        ],
        max_results=10,
    )

    general_results = general_search["results"]

    # --------------------
    # ZOMATO / DISTRICT
    # --------------------

    zomato_search = search_multiple(
        [
            f"{restaurant} {location} Zomato",
            f"{restaurant} Zomato {location}",
            f"{restaurant} {location} District dining",
            f"site:zomato.com {restaurant} {location}",
            f"site:district.in {restaurant} {location}",
        ],
        max_results=5,
    )

    # Search dedicated results first,
    # then general results as fallback.

    zomato = find_domain_result(
        zomato_search["results"],
        [
            "zomato.com",
            "district.in",
        ],
    )

    if not zomato:
        zomato = find_domain_result(
            general_results,
            [
                "zomato.com",
                "district.in",
            ],
        )

    # --------------------
    # SWIGGY DINEOUT
    # --------------------

    dineout_search = search_multiple(
        [
            f"{restaurant} {location} Swiggy Dineout",
            f"{restaurant} Dineout {location}",
            f"site:swiggy.com {restaurant} {location} dineout",
        ],
        max_results=5,
    )

    dineout = find_domain_result(
        dineout_search["results"],
        ["swiggy.com"],
    )

    if not dineout:
        dineout = find_domain_result(
            general_results,
            ["swiggy.com"],
        )

    # --------------------
    # INSTAGRAM
    # --------------------

    instagram_search = search_multiple(
        [
            f"{restaurant} {location} Instagram",
            f"{restaurant} official Instagram",
            f"site:instagram.com {restaurant}",
        ],
        max_results=5,
    )

    instagram = find_domain_result(
        instagram_search["results"],
        ["instagram.com"],
    )

    # --------------------
    # WEBSITE
    # --------------------

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
    ]

    website = None

    for result in website_search["results"]:

        url = result.get(
            "url",
            "",
        ).lower()

        if not any(
            domain in url
            for domain in excluded_domains
        ):
            website = result
            break

    # --------------------
    # DEBUG INFO
    # --------------------

    debug = {
        "general_errors":
            general_search["errors"],

        "zomato_errors":
            zomato_search["errors"],

        "dineout_errors":
            dineout_search["errors"],

        "instagram_errors":
            instagram_search["errors"],

        "website_errors":
            website_search["errors"],

        "zomato_candidates":
            zomato_search["results"],

        "dineout_candidates":
            dineout_search["results"],
    }

    return {
        "restaurant": restaurant,
        "location": location,

        "zomato": zomato,
        "dineout": dineout,
        "instagram": instagram,
        "website": website,

        "general_results":
            general_results,

        "debug":
            debug,
    }
