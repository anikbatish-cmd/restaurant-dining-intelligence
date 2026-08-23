from ddgs import DDGS
from urllib.parse import urlparse


def search_web(query, max_results=10):
    """
    Free web-search helper.
    Returns title, URL and snippet.
    """
    try:
        results = DDGS().text(
            query,
            region="in-en",
            safesearch="moderate",
            max_results=max_results,
        )

        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in results
        ]

    except Exception as e:
        return []


def find_domain_result(results, domains):
    """
    Returns the first result matching one of the supplied domains.
    """
    for result in results:
        url = result.get("url", "").lower()

        for domain in domains:
            if domain.lower() in url:
                return result

    return None


def resolve_restaurant(restaurant, location):
    """
    Finds likely public profiles for a restaurant.
    """

    base_query = f'"{restaurant}" "{location}" restaurant'

    general_results = search_web(base_query, max_results=10)

    zomato_results = search_web(
        f'"{restaurant}" "{location}" site:zomato.com',
        max_results=5,
    )

    dineout_results = search_web(
        f'"{restaurant}" "{location}" site:swiggy.com dineout',
        max_results=5,
    )

    instagram_results = search_web(
        f'"{restaurant}" "{location}" Instagram',
        max_results=5,
    )

    website_results = search_web(
        f'"{restaurant}" "{location}" official website',
        max_results=10,
    )

    zomato = find_domain_result(
        zomato_results,
        ["zomato.com"],
    )

    dineout = find_domain_result(
        dineout_results,
        ["swiggy.com"],
    )

    instagram = find_domain_result(
        instagram_results,
        ["instagram.com"],
    )

    # Find likely official website while excluding platforms
    excluded_domains = [
        "zomato.com",
        "swiggy.com",
        "instagram.com",
        "facebook.com",
        "youtube.com",
        "tripadvisor",
        "magicpin",
        "eazydiner",
    ]

    website = None

    for result in website_results:
        url = result.get("url", "").lower()

        if not any(domain in url for domain in excluded_domains):
            website = result
            break

    return {
        "restaurant": restaurant,
        "location": location,
        "zomato": zomato,
        "dineout": dineout,
        "instagram": instagram,
        "website": website,
        "general_results": general_results,
    }
