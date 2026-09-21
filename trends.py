from datetime import datetime, timezone
import json
import os

import requests
import streamlit as st


def _config():
    """Optional zero-cost persistence via Supabase REST."""
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
    except Exception:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
    return (url.rstrip("/") if url else None), key


def persistence_ready():
    url, key = _config()
    return bool(url and key)


def _headers(key, prefer=None):
    h = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def build_monthly_snapshot(report):
    target = report.get("benchmark_target") or {}
    cm = report.get("competitive_metrics") or {}
    cross = report.get("cross_source_metrics") or {}
    ig = report.get("instagram_metrics") or {}
    discovery = report.get("discovery") or {}
    customer = report.get("customer_voice") or {}
    content = report.get("content_summary") or {}
    now = datetime.now(timezone.utc)
    restaurant_key = f"{report.get('restaurant','')}|{report.get('location','')}".strip().lower()
    strengths = customer.get("strengths") or []
    concerns = customer.get("concerns") or []
    return {
        "restaurant_key": restaurant_key,
        "restaurant": report.get("restaurant"),
        "location": report.get("location"),
        "month": now.strftime("%Y-%m-01"),
        "captured_at": now.isoformat(),
        "rating": target.get("rating"),
        "review_count": target.get("review_count"),
        "cost_for_two": target.get("cost_for_two"),
        "discount_percent": target.get("discount_percent"),
        "cohort_rating_median": cm.get("cohort_rating_median"),
        "cohort_price_median": cm.get("cohort_price_median"),
        "rating_gap": cm.get("rating_gap"),
        "price_index": cm.get("price_index"),
        "reputation_percentile": cm.get("reputation_percentile"),
        "volume_percentile": cm.get("volume_percentile"),
        "rating_spread": cross.get("rating_spread"),
        "price_spread": cross.get("price_spread"),
        "instagram_followers": ig.get("followers"),
        "instagram_posts": ig.get("posts"),
        "discovery_share": discovery.get("share_of_observed_mentions"),
        "creator_lift": content.get("creator_lift"),
        "review_sample_size": customer.get("sample_size"),
        "top_strength": strengths[0].get("topic") if strengths and isinstance(strengths[0], dict) else (strengths[0] if strengths else None),
        "top_concern": concerns[0].get("topic") if concerns and isinstance(concerns[0], dict) else (concerns[0] if concerns else None),
    }


def save_monthly_snapshot(report):
    """Upsert one observation per restaurant/month. Returns status, never blocks report."""
    url, key = _config()
    if not url or not key:
        return {"saved": False, "reason": "Persistence not configured"}
    row = build_monthly_snapshot(report)
    endpoint = f"{url}/rest/v1/restaurant_monthly_snapshots?on_conflict=restaurant_key,month"
    try:
        response = requests.post(
            endpoint,
            headers=_headers(key, "resolution=merge-duplicates,return=minimal"),
            data=json.dumps(row),
            timeout=7,
        )
        return {"saved": response.ok, "reason": None if response.ok else f"HTTP {response.status_code}"}
    except requests.RequestException as exc:
        return {"saved": False, "reason": str(exc)}


def load_monthly_history(restaurant, location, limit=18):
    url, key = _config()
    if not url or not key:
        return []
    restaurant_key = f"{restaurant}|{location}".strip().lower()
    endpoint = f"{url}/rest/v1/restaurant_monthly_snapshots"
    params = {
        "restaurant_key": f"eq.{restaurant_key}",
        "select": "*",
        "order": "month.asc",
        "limit": str(limit),
    }
    try:
        response = requests.get(endpoint, headers=_headers(key), params=params, timeout=7)
        if response.ok:
            return response.json()
    except requests.RequestException:
        pass
    return []


def delta(current, previous):
    if current is None or previous is None:
        return None
    try:
        return current - previous
    except TypeError:
        return None


def latest_changes(history):
    if len(history) < 2:
        return {}
    current, previous = history[-1], history[-2]
    fields = [
        "rating", "review_count", "cost_for_two", "discount_percent",
        "rating_gap", "price_index", "reputation_percentile",
        "instagram_followers", "instagram_posts", "discovery_share",
        "creator_lift",
    ]
    return {field: delta(current.get(field), previous.get(field)) for field in fields}
