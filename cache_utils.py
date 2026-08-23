from collectors import extract_direct_page_metrics
from search_engine import clear_search_cache


def clear_runtime_caches():
    """Clear low-level network caches for an explicit user-requested refresh."""
    clear_search_cache()
    extract_direct_page_metrics.cache_clear()
