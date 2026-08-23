from time import perf_counter

import streamlit as st

from collectors import (
    enrich_dining_metrics_with_pages,
    extract_dining_metrics,
    extract_instagram_content_items,
    extract_instagram_metrics,
    extract_instagram_snapshots,
    summarize_content_items,
    summarize_source_results,
)
from competitors import discover_competitors
from data_lab import (
    build_metric_dictionary,
    build_platform_comparison,
    build_platform_tensions,
    build_scan_summary,
    classify_search_errors,
)
from insights import (
    analyze_customer_voice,
    analyze_discovery,
    analyze_earned_attention,
    detect_paid_signal,
)
from metrics import (
    build_competitive_metrics,
    build_cross_source_metrics,
    external_health_score,
)
from radar import build_conversation_starters, build_signal_radar
from search_engine import collect_public_intelligence, resolve_restaurant
from strategy_layer import (
    build_executive_story,
    build_gap_metrics,
    build_market_position,
    build_positioning_white_space,
)


def _search_error_rows(debug_data, public_intel):
    rows = list(public_intel.get("errors", []))
    mapping = {
        "general_errors": "Resolver · general",
        "district_errors": "Resolver · District",
        "metric_errors": "Resolver · metrics",
        "dineout_errors": "Resolver · Dineout",
        "instagram_errors": "Resolver · Instagram",
        "website_errors": "Resolver · website",
    }
    for key, label in mapping.items():
        for item in debug_data.get(key, []):
            rows.append({"group": label, **item})
    return classify_search_errors(rows)


@st.cache_data(ttl=900, show_spinner=False)
def build_report(restaurant, location):
    started = perf_counter()

    data = resolve_restaurant(restaurant, location)
    debug_data = data.get("debug", {})

    all_dining_candidates = (
        debug_data.get("district_candidates", [])
        + debug_data.get("dineout_candidates", [])
        + debug_data.get("metric_candidates", [])
        + data.get("general_results", [])
    )

    dining_metrics = extract_dining_metrics(
        primary_result=data.get("district"),
        supporting_results=all_dining_candidates,
    )

    direct_urls = []
    if data.get("district") and data["district"].get("url"):
        direct_urls.append(data["district"]["url"])
    if data.get("dineout") and data["dineout"].get("url"):
        direct_urls.append(data["dineout"]["url"])

    dining_metrics = enrich_dining_metrics_with_pages(dining_metrics, direct_urls)

    source_summaries = {
        source: summarize_source_results(
            dining_metrics.get("by_source", {}).get(source, [])
        )
        for source in [
            "District",
            "Swiggy Dineout",
            "EazyDiner",
            "Justdial",
            "Web",
        ]
    }

    district_summary = source_summaries.get("District")
    benchmark_target = (
        district_summary
        or source_summaries.get("Swiggy Dineout")
        or source_summaries.get("Web")
        or {}
    )

    instagram_metrics = extract_instagram_metrics(data.get("instagram"))
    instagram_snapshots = extract_instagram_snapshots(
        debug_data.get("instagram_candidates", []),
        canonical_url=(data.get("instagram") or {}).get("url"),
    )

    target_context = " ".join(
        [
            instagram_metrics.get("bio") or "",
            " ".join(
                result.get("snippet", "")
                for result in data.get("general_results", [])[:6]
            ),
        ]
    )

    competitor_result = discover_competitors(
        restaurant=restaurant,
        location=location,
        target_summary=benchmark_target,
        target_context=target_context,
        limit=5,
    )
    competitors = competitor_result.get("competitors", [])
    competitor_names = [
        item.get("name") for item in competitors if item.get("name")
    ]

    public_intel = collect_public_intelligence(
        restaurant=restaurant,
        location=location,
        instagram_handle=instagram_metrics.get("handle"),
        competitor_names=competitor_names,
        positioning_tags=benchmark_target.get("positioning_tags", []),
    )

    content_items = extract_instagram_content_items(
        debug_data.get("instagram_candidates", [])
        + public_intel.get("creators", []),
        restaurant_handle=instagram_metrics.get("handle"),
    )
    content_summary = summarize_content_items(content_items)
    customer_voice = analyze_customer_voice(public_intel.get("reviews", []))
    earned = analyze_earned_attention(public_intel.get("earned", []))
    discovery = analyze_discovery(
        public_intel.get("discovery", []),
        restaurant,
        competitor_names,
    )
    paid_signal = detect_paid_signal(public_intel.get("paid", []), restaurant)

    competitive_metrics = build_competitive_metrics(benchmark_target, competitors)
    cross_source_metrics = build_cross_source_metrics(source_summaries)
    health = external_health_score(
        benchmark_target,
        competitive_metrics,
        instagram_metrics,
        content_summary,
    )

    platform_comparison = build_platform_comparison(source_summaries)
    platform_tensions = build_platform_tensions(source_summaries)
    metric_dictionary = build_metric_dictionary(
        benchmark_target,
        competitive_metrics,
        cross_source_metrics,
        competitors,
        content_summary,
        discovery,
    )

    signals = build_signal_radar(
        competitive_metrics=competitive_metrics,
        cross_source_metrics=cross_source_metrics,
        customer_voice=customer_voice,
        content_summary=content_summary,
        discovery=discovery,
        earned=earned,
        target_summary=benchmark_target,
        source_summaries=source_summaries,
        competitors=competitors,
        instagram_metrics=instagram_metrics,
        instagram_snapshots=instagram_snapshots,
    )
    conversation_starters = build_conversation_starters(
        signals,
        platform_tensions=platform_tensions,
        limit=6,
    )

    market_position = build_market_position(
        benchmark_target,
        competitive_metrics,
    )
    gap_metrics = build_gap_metrics(
        benchmark_target,
        competitive_metrics,
        cross_source_metrics,
        discovery,
        customer_voice,
        content_summary,
        competitors,
        source_summaries,
    )
    white_space = build_positioning_white_space(
        benchmark_target,
        competitors,
        customer_voice,
        earned,
    )
    executive_story = build_executive_story(
        market_position,
        gap_metrics,
        white_space,
    )

    total_elapsed_ms = round((perf_counter() - started) * 1000)
    scan_summary = build_scan_summary(
        debug_data,
        public_intel,
        competitor_result,
        dining_metrics,
        total_elapsed_ms=total_elapsed_ms,
    )

    return {
        "restaurant": restaurant,
        "location": location,
        "data": data,
        "debug_data": debug_data,
        "dining_metrics": dining_metrics,
        "source_summaries": source_summaries,
        "district_summary": district_summary,
        "benchmark_target": benchmark_target,
        "instagram_metrics": instagram_metrics,
        "instagram_snapshots": instagram_snapshots,
        "competitor_result": competitor_result,
        "competitors": competitors,
        "public_intel": public_intel,
        "content_items": content_items,
        "content_summary": content_summary,
        "customer_voice": customer_voice,
        "earned": earned,
        "discovery": discovery,
        "paid_signal": paid_signal,
        "competitive_metrics": competitive_metrics,
        "cross_source_metrics": cross_source_metrics,
        "health": health,
        "platform_comparison": platform_comparison,
        "platform_tensions": platform_tensions,
        "metric_dictionary": metric_dictionary,
        "signals": signals,
        "conversation_starters": conversation_starters,
        "market_position": market_position,
        "gap_metrics": gap_metrics,
        "white_space": white_space,
        "executive_story": executive_story,
        "scan_summary": scan_summary,
        "search_errors": _search_error_rows(debug_data, public_intel),
        "scan_seconds": total_elapsed_ms / 1000,
    }
