import re


def combine_result_text(result):
    if not result:
        return ""

    return " ".join(
        [
            result.get("title", ""),
            result.get("snippet", ""),
        ]
    )


def extract_rating(text):
    """
    Find rating such as 4.3.
    """

    patterns = [
        r"\brated\s+([1-5]\.\d)\b",
        r"\b([1-5]\.\d)\s+(?:based on|rating|ratings|reviews)",
        r"\b([1-5]\.\d)\b",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass

    return None


def extract_cost_for_two(text):
    """
    Extract ₹2500 for two / Rs 2500 for two.
    """

    patterns = [
        r"₹\s*([\d,]+)\s*(?:for two|for 2)",
        r"Rs\.?\s*([\d,]+)\s*(?:for two|for 2)",
        r"([\d,]+)\s*(?:for two|for 2)",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            value = (
                match
                .group(1)
                .replace(",", "")
            )

            try:
                return int(value)
            except ValueError:
                pass

    return None


def extract_offer(text):
    """
    Extract visible dining offer.
    """

    patterns = [
        r"(flat\s+\d+%\s+off)",
        r"(up to\s+\d+%\s+off)",
        r"(upto\s+\d+%\s+off)",
        r"(\d+%\s+off)",
    ]

    offers = []

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE,
        )

        for match in matches:
            clean = match.strip()

            if clean not in offers:
                offers.append(clean)

    return offers


def extract_review_count(text):
    """
    Extract counts from sentences like:
    'Rated 4.3 based on 3956 Customer Reviews'
    """

    patterns = [
        r"based on\s+([\d,]+)\s+(?:customer\s+)?reviews",
        r"([\d,]+)\s+reviews",
        r"([\d,]+)\s+ratings",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:

            value = (
                match
                .group(1)
                .replace(",", "")
            )

            try:
                return int(value)
            except ValueError:
                pass

    return None


def extract_cuisine_candidates(text):
    """
    Lightweight cuisine extraction.
    We will improve this later.
    """

    known_cuisines = [
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
    ]

    found = []

    for cuisine in known_cuisines:

        if cuisine.lower() in text.lower():
            found.append(cuisine)

    return found


def extract_dining_metrics(
    primary_result=None,
    supporting_results=None,
):
    """
    Combine multiple public search results into one
    best-effort dining snapshot.
    """

    supporting_results = supporting_results or []

    all_results = []

    if primary_result:
        all_results.append(primary_result)

    all_results.extend(supporting_results)

    rating = None
    cost_for_two = None
    review_count = None
    offers = []
    cuisines = []
    evidence = []

    for result in all_results:

        text = combine_result_text(result)

        if not rating:
            rating = extract_rating(text)

        if not cost_for_two:
            cost_for_two = extract_cost_for_two(text)

        if not review_count:
            review_count = extract_review_count(text)

        for offer in extract_offer(text):

            if offer not in offers:
                offers.append(offer)

        for cuisine in extract_cuisine_candidates(text):

            if cuisine not in cuisines:
                cuisines.append(cuisine)

        evidence.append(
            {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", ""),
            }
        )

    return {
        "rating": rating,
        "review_count": review_count,
        "cost_for_two": cost_for_two,
        "offers": offers,
        "cuisines": cuisines,
        "evidence": evidence,
    }
