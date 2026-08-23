import html
from time import perf_counter

import pandas as pd
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
    PLATFORM_NOTES,
    PLATFORM_ROLES,
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


st.set_page_config(
    page_title="Dining Intelligence",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# -----------------------------------------------------------------------------
# VISUAL SYSTEM
# -----------------------------------------------------------------------------

st.markdown(
    """
    <style>
        :root {
            --ink: #f4f7f5;
            --muted: #94a39c;
            --panel: rgba(18, 27, 25, .76);
            --panel-strong: rgba(22, 34, 31, .94);
            --border: rgba(166, 205, 188, .14);
            --green: #8ff0bd;
            --green-2: #42c98d;
            --amber: #f5c96a;
            --red: #ff7f88;
            --blue: #85b9ff;
            --purple: #c5a6ff;
        }

        .stApp {
            background:
                radial-gradient(circle at 8% 0%, rgba(50, 132, 97, .15), transparent 28rem),
                radial-gradient(circle at 95% 8%, rgba(55, 88, 132, .12), transparent 26rem),
                #070b0a;
            color: var(--ink);
        }

        [data-testid="stHeader"] {background: transparent;}
        [data-testid="stToolbar"] {right: 1rem;}
        .block-container {
            max-width: 1480px;
            padding-top: 1.25rem;
            padding-bottom: 5rem;
        }

        h1, h2, h3, h4 {letter-spacing: -.025em;}
        p, label, .stCaption {color: #cbd5d0;}

        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: .7rem;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: .7rem;
            font-weight: 800;
            letter-spacing: -.02em;
            font-size: 1.05rem;
        }
        .brand-mark {
            width: 34px;
            height: 34px;
            border-radius: 11px;
            background: linear-gradient(135deg, #8ff0bd, #3d9f78);
            box-shadow: 0 0 30px rgba(92, 219, 158, .18);
        }
        .mini-label {
            color: var(--muted);
            font-size: .72rem;
            letter-spacing: .13em;
            font-weight: 800;
            text-transform: uppercase;
        }

        .hero {
            position: relative;
            overflow: hidden;
            border: 1px solid var(--border);
            border-radius: 26px;
            background:
                linear-gradient(120deg, rgba(21, 40, 34, .98), rgba(11, 18, 17, .92)),
                #0b1210;
            padding: 2rem 2.2rem;
            margin: .4rem 0 1.15rem 0;
            box-shadow: 0 24px 80px rgba(0, 0, 0, .22);
        }
        .hero:after {
            content: "";
            position: absolute;
            width: 340px;
            height: 340px;
            border-radius: 50%;
            right: -110px;
            top: -175px;
            background: radial-gradient(circle, rgba(126, 234, 178, .22), rgba(126, 234, 178, 0));
            pointer-events: none;
        }
        .hero h1 {
            font-size: clamp(2rem, 4vw, 3.8rem);
            line-height: .98;
            max-width: 840px;
            margin: .45rem 0 .75rem 0;
            color: #f7fbf8;
        }
        .hero-copy {
            max-width: 780px;
            font-size: 1rem;
            color: #aebdb6;
            line-height: 1.6;
        }
        .hero-pills {
            display: flex;
            flex-wrap: wrap;
            gap: .5rem;
            margin-top: 1.25rem;
        }
        .hero-pill {
            border: 1px solid rgba(151, 216, 183, .16);
            background: rgba(116, 194, 155, .07);
            color: #cce7d8;
            border-radius: 999px;
            padding: .42rem .72rem;
            font-size: .78rem;
            font-weight: 650;
        }

        .section-kicker {
            color: #77d9a5;
            font-size: .72rem;
            text-transform: uppercase;
            letter-spacing: .14em;
            font-weight: 850;
            margin-bottom: .2rem;
        }
        .section-copy {
            color: #92a29a;
            font-size: .9rem;
            margin-top: -.35rem;
            margin-bottom: 1rem;
        }

        .kpi-card {
            min-height: 118px;
            padding: 1rem 1.05rem;
            border: 1px solid var(--border);
            border-radius: 18px;
            background: linear-gradient(180deg, rgba(24, 35, 32, .88), rgba(14, 21, 19, .88));
            box-shadow: inset 0 1px 0 rgba(255,255,255,.025);
        }
        .kpi-label {
            color: #8fa099;
            font-size: .73rem;
            text-transform: uppercase;
            letter-spacing: .09em;
            font-weight: 760;
        }
        .kpi-value {
            color: #f6faf7;
            font-size: 1.75rem;
            line-height: 1.05;
            font-weight: 850;
            margin-top: .45rem;
        }
        .kpi-sub {
            color: #8fa099;
            font-size: .77rem;
            margin-top: .48rem;
            line-height: 1.35;
        }
        .kpi-card.positive {border-color: rgba(86, 219, 153, .28);}
        .kpi-card.risk {border-color: rgba(255, 127, 136, .26);}
        .kpi-card.watch {border-color: rgba(245, 201, 106, .25);}

        .signal-card {
            min-height: 228px;
            padding: 1.15rem 1.15rem 1rem;
            border-radius: 19px;
            border: 1px solid var(--border);
            background: linear-gradient(180deg, rgba(22, 31, 29, .95), rgba(12, 18, 17, .95));
            margin-bottom: .8rem;
        }
        .signal-card.critical {border-color: rgba(255, 116, 126, .36);}
        .signal-card.watch {border-color: rgba(245, 201, 106, .30);}
        .signal-card.opportunity {border-color: rgba(133, 185, 255, .30);}
        .signal-card.advantage {border-color: rgba(92, 222, 155, .31);}
        .signal-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: .8rem;
        }
        .signal-badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: .3rem .57rem;
            font-size: .68rem;
            font-weight: 850;
            letter-spacing: .06em;
            text-transform: uppercase;
            background: rgba(255,255,255,.055);
            color: #d6e2dc;
        }
        .signal-score {
            color: #899b93;
            font-size: .74rem;
            font-weight: 760;
        }
        .signal-title {
            color: #f5f9f6;
            font-size: 1.15rem;
            line-height: 1.2;
            font-weight: 820;
            margin: .72rem 0 .5rem 0;
        }
        .signal-value {
            color: #a9e7c5;
            font-size: .88rem;
            font-weight: 710;
            margin-bottom: .65rem;
        }
        .signal-why {
            color: #a0afa8;
            font-size: .83rem;
            line-height: 1.48;
        }
        .signal-proof {
            border-top: 1px solid rgba(255,255,255,.06);
            margin-top: .8rem;
            padding-top: .65rem;
            color: #75877f;
            font-size: .72rem;
        }
        .priority-track {
            width: 100%;
            height: 4px;
            background: rgba(255,255,255,.055);
            border-radius: 999px;
            overflow: hidden;
            margin-top: .75rem;
        }
        .priority-fill {
            height: 100%;
            background: linear-gradient(90deg, #5dd39c, #dcce76);
            border-radius: 999px;
        }

        .tension-card {
            padding: .95rem 1rem;
            border-radius: 16px;
            border: 1px solid rgba(133, 185, 255, .18);
            background: rgba(55, 84, 112, .09);
            margin-bottom: .7rem;
        }
        .tension-title {font-weight: 800; color: #eaf1ee;}
        .tension-signal {color: #9fc6ff; margin-top: .32rem; font-size: .86rem;}
        .tension-question {color: #9aa9a2; margin-top: .4rem; font-size: .82rem; line-height: 1.45;}

        .topic-row {
            padding: .75rem 0;
            border-bottom: 1px solid rgba(255,255,255,.055);
        }
        .topic-head {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            font-size: .82rem;
            margin-bottom: .45rem;
        }
        .topic-name {font-weight: 760; color: #e9f0ec;}
        .topic-count {color: #7f9188;}
        .sentiment-bar {
            display: flex;
            height: 8px;
            overflow: hidden;
            border-radius: 999px;
            background: rgba(255,255,255,.06);
        }
        .bar-positive {background: #54cf91;}
        .bar-neutral {background: #6f7f78;}
        .bar-negative {background: #e87981;}

        .formula-box {
            border: 1px solid rgba(143, 240, 189, .15);
            background: linear-gradient(180deg, rgba(25, 43, 36, .62), rgba(16, 24, 21, .62));
            border-radius: 18px;
            padding: 1.15rem 1.2rem;
        }
        .formula {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            color: #a5ecc5;
            background: rgba(0,0,0,.18);
            border-radius: 10px;
            padding: .62rem .7rem;
            font-size: .83rem;
            margin: .7rem 0;
        }

        .platform-role {
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: .95rem 1rem;
            min-height: 145px;
            background: rgba(17, 25, 23, .75);
        }
        .platform-role h4 {margin: .2rem 0 .42rem; font-size: 1rem;}
        .platform-role p {font-size: .78rem; color: #87988f; line-height: 1.45;}

        div[data-baseweb="tab-list"] {
            gap: .35rem;
            background: rgba(13, 19, 18, .7);
            padding: .33rem;
            border: 1px solid rgba(255,255,255,.055);
            border-radius: 14px;
        }
        button[data-baseweb="tab"] {
            border-radius: 10px;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        [data-testid="stForm"] {
            background: rgba(15, 23, 21, .72);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: .9rem 1rem .25rem;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid rgba(255,255,255,.06);
            border-radius: 14px;
            overflow: hidden;
        }
        [data-testid="stExpander"] {
            border-color: rgba(255,255,255,.07);
            border-radius: 14px;
            background: rgba(13, 20, 18, .42);
        }
        .stButton > button, .stFormSubmitButton > button {
            border-radius: 12px;
            min-height: 44px;
            font-weight: 760;
        }

        @media (max-width: 720px) {
            .hero {padding: 1.35rem; border-radius: 20px;}
            .hero h1 {font-size: 2.2rem;}
            .signal-card {min-height: auto;}
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def esc(value):
    return html.escape(str(value if value is not None else "—"))


def fmt_money(value):
    return f"₹{value:,.0f}" if value is not None else "—"


def fmt_num(value):
    return f"{value:,.0f}" if value is not None else "—"


def render_kpi(label, value, sub="", tone="neutral"):
    st.markdown(
        f"""
        <div class="kpi-card {esc(tone)}">
            <div class="kpi-label">{esc(label)}</div>
            <div class="kpi-value">{esc(value)}</div>
            <div class="kpi-sub">{esc(sub)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_signal(signal):
    severity = signal.get("severity", "Watch")
    css_class = severity.lower()
    st.markdown(
        f"""
        <div class="signal-card {esc(css_class)}">
            <div class="signal-top">
                <span class="signal-badge">#{signal.get('rank', '—')} · {esc(severity)} · {esc(signal.get('category', 'Signal'))}</span>
                <span class="signal-score">Priority {signal.get('score', 0)}/100</span>
            </div>
            <div class="signal-title">{esc(signal.get('title', ''))}</div>
            <div class="signal-value">{esc(signal.get('signal', ''))}</div>
            <div class="signal-why">{esc(signal.get('why', ''))}</div>
            <div class="priority-track"><div class="priority-fill" style="width:{max(0, min(100, signal.get('score', 0)))}%"></div></div>
            <div class="signal-proof">Metric: {esc(signal.get('proof', ''))} · {esc(signal.get('confidence', 'Medium'))} confidence</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tension(tension):
    st.markdown(
        f"""
        <div class="tension-card">
            <div class="tension-title">{esc(tension.get('title', ''))}</div>
            <div class="tension-signal">{esc(tension.get('signal', ''))}</div>
            <div class="tension-question">{esc(tension.get('question', ''))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_topic_row(row):
    mentions = row.get("mentions", 0) or 0
    positive = row.get("positive", 0) or 0
    negative = row.get("negative", 0) or 0
    mixed = row.get("mixed", 0) or 0
    denominator = max(mentions, 1)
    positive_pct = positive / denominator * 100
    negative_pct = negative / denominator * 100
    neutral_pct = max(0, 100 - positive_pct - negative_pct)
    st.markdown(
        f"""
        <div class="topic-row">
            <div class="topic-head">
                <span class="topic-name">{esc(row.get('topic', ''))}</span>
                <span class="topic-count">{mentions} mentions · +{positive} / −{negative} / ~{mixed}</span>
            </div>
            <div class="sentiment-bar">
                <div class="bar-positive" style="width:{positive_pct:.1f}%"></div>
                <div class="bar-neutral" style="width:{neutral_pct:.1f}%"></div>
                <div class="bar-negative" style="width:{negative_pct:.1f}%"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def search_error_rows(debug_data, public_intel):
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

    dining_metrics = enrich_dining_metrics_with_pages(
        dining_metrics,
        direct_urls,
    )

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
    benchmark_target = district_summary or source_summaries.get("Swiggy Dineout") or source_summaries.get("Web") or {}

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
    competitor_names = [item.get("name") for item in competitors if item.get("name")]

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

    competitive_metrics = build_competitive_metrics(
        benchmark_target,
        competitors,
    )
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
        "scan_summary": scan_summary,
        "search_errors": search_error_rows(debug_data, public_intel),
        "scan_seconds": total_elapsed_ms / 1000,
    }


# -----------------------------------------------------------------------------
# HEADER + SEARCH
# -----------------------------------------------------------------------------

st.markdown(
    """
    <div class="topbar">
        <div class="brand"><span class="brand-mark"></span><span>Dining Intelligence</span></div>
        <div class="mini-label">Public-market signal OS · dine-in only</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <div class="mini-label">Restaurant intelligence, not another listing dashboard</div>
        <h1>Find the signal hiding inside the noise.</h1>
        <div class="hero-copy">
            Scan dining platforms, competitors, review themes, Instagram, creators, earned attention and generic discovery — then rank the anomalies that are actually worth discussing with an owner.
        </div>
        <div class="hero-pills">
            <span class="hero-pill">District-led cohorting</span>
            <span class="hero-pill">Cross-platform contradictions</span>
            <span class="hero-pill">Customer-friction radar</span>
            <span class="hero-pill">Creator & discovery signals</span>
            <span class="hero-pill">Auditable formulas</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("restaurant_search"):
    search_col, location_col, button_col = st.columns([1.45, .9, .65])
    with search_col:
        restaurant_input = st.text_input(
            "Restaurant",
            value=st.session_state.get("last_restaurant", ""),
            placeholder="Kijiji - On The Roof",
        )
    with location_col:
        location_input = st.text_input(
            "Location",
            value=st.session_state.get("last_location", ""),
            placeholder="Gurgaon",
        )
    with button_col:
        st.write("")
        submitted = st.form_submit_button(
            "Run intelligence scan",
            type="primary",
            use_container_width=True,
        )

if submitted:
    restaurant_input = restaurant_input.strip()
    location_input = location_input.strip()
    if not restaurant_input or not location_input:
        st.warning("Enter both restaurant name and location.")
    else:
        st.session_state["last_restaurant"] = restaurant_input
        st.session_state["last_location"] = location_input
        with st.status("Scanning the public market and ranking anomalies…", expanded=False) as status:
            report = build_report(restaurant_input, location_input)
            st.session_state["report"] = report
            status.update(label="Intelligence scan complete", state="complete")

report = st.session_state.get("report")

if not report:
    st.markdown("### What appears after a scan")
    preview_cols = st.columns(4)
    preview = [
        ("01", "Signal Radar", "Prioritised anomalies instead of generic recommendations."),
        ("02", "Competitive Battlefield", "Price, reputation, review volume, offers and positioning versus a selected cohort."),
        ("03", "Platform Intelligence", "Exactly how District, Dineout and other sources disagree — and why that matters."),
        ("04", "Data Lab", "Every formula, input, source, resolver decision and failed query exposed for audit."),
    ]
    for col, (number, title, copy) in zip(preview_cols, preview):
        with col:
            st.markdown(
                f"""
                <div class="platform-role">
                    <div class="mini-label">{number}</div>
                    <h4>{esc(title)}</h4>
                    <p>{esc(copy)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.stop()


# -----------------------------------------------------------------------------
# REPORT CONTEXT
# -----------------------------------------------------------------------------

restaurant = report["restaurant"]
location = report["location"]
benchmark_target = report["benchmark_target"]
district_summary = report["district_summary"]
source_summaries = report["source_summaries"]
competitive_metrics = report["competitive_metrics"]
cross_source_metrics = report["cross_source_metrics"]
instagram_metrics = report["instagram_metrics"]
competitors = report["competitors"]
customer_voice = report["customer_voice"]
content_summary = report["content_summary"]
content_items = report["content_items"]
earned = report["earned"]
discovery = report["discovery"]
paid_signal = report["paid_signal"]
signals = report["signals"]
platform_tensions = report["platform_tensions"]

context_left, context_right = st.columns([4, 1])
with context_left:
    st.markdown(f"## {restaurant}")
    primary_label = "District" if district_summary else "Best available public dining source"
    st.caption(f"{location} · Primary benchmark: {primary_label} · {len(competitors)}-restaurant competitive cohort")
with context_right:
    if st.button("↻ Refresh public data", use_container_width=True):
        build_report.clear()
        with st.status("Refreshing the public scan…", expanded=False) as status:
            refreshed = build_report(restaurant, location)
            st.session_state["report"] = refreshed
            status.update(label="Public data refreshed", state="complete")
        st.rerun()

if not district_summary:
    st.warning(
        "District could not be extracted with high confidence for this restaurant. Cohort analysis uses the strongest available public dining source and is labelled accordingly."
    )

severity_counts = {
    severity: sum(item.get("severity") == severity for item in signals)
    for severity in ["Critical", "Watch", "Opportunity", "Advantage"]
}

summary_cols = st.columns(5)
with summary_cols[0]:
    render_kpi(
        "Signals found",
        str(len(signals)),
        f"{severity_counts['Critical']} critical · {severity_counts['Watch']} watch",
        "risk" if severity_counts["Critical"] else "neutral",
    )
with summary_cols[1]:
    render_kpi(
        "Price vs cohort",
        f"{competitive_metrics.get('price_index'):.2f}x" if competitive_metrics.get("price_index") is not None else "—",
        "District-led competitive median",
        "watch" if competitive_metrics.get("price_index") and competitive_metrics.get("price_index") > 1.1 else "neutral",
    )
with summary_cols[2]:
    render_kpi(
        "Rating gap",
        f"{competitive_metrics.get('rating_gap'):+.1f}" if competitive_metrics.get("rating_gap") is not None else "—",
        "vs selected cohort median",
        "risk" if competitive_metrics.get("rating_gap") is not None and competitive_metrics.get("rating_gap") < 0 else "positive",
    )
with summary_cols[3]:
    render_kpi(
        "Platform rating spread",
        f"{cross_source_metrics.get('rating_spread'):.1f}" if cross_source_metrics.get("rating_spread") is not None else "—",
        "highest observed rating − lowest",
        "watch" if cross_source_metrics.get("rating_spread") and cross_source_metrics.get("rating_spread") >= .25 else "neutral",
    )
with summary_cols[4]:
    render_kpi(
        "Source scan",
        f"{report.get('scan_seconds', 0):.1f}s",
        f"{report['health'].get('coverage', 0)}% derived-metric coverage · cached 15m",
        "neutral",
    )

st.write("")

# -----------------------------------------------------------------------------
# PRIMARY NAVIGATION
# -----------------------------------------------------------------------------

tabs = st.tabs(
    [
        "📡 Signal Radar",
        "🥊 Competitive Battlefield",
        "💬 Customer Experience",
        "📣 Marketing & Discovery",
        "🔀 Platform Intelligence",
        "🧬 Data Lab",
    ]
)


# -----------------------------------------------------------------------------
# SIGNAL RADAR
# -----------------------------------------------------------------------------

with tabs[0]:
    st.markdown('<div class="section-kicker">Priority layer</div>', unsafe_allow_html=True)
    st.subheader("What deserves attention first")
    st.markdown(
        '<div class="section-copy">Priority scores rank unusual public-market patterns inside this report. They are not restaurant health scores.</div>',
        unsafe_allow_html=True,
    )

    if signals:
        top_signals = signals[:4]
        for start in range(0, len(top_signals), 2):
            cols = st.columns(2)
            for col, signal in zip(cols, top_signals[start:start + 2]):
                with col:
                    render_signal(signal)
    else:
        st.info("No strong anomaly crossed the radar thresholds in the current public sample.")

    if platform_tensions:
        st.markdown("### Cross-platform tensions")
        tension_cols = st.columns(2)
        for index, tension in enumerate(platform_tensions[:4]):
            with tension_cols[index % 2]:
                render_tension(tension)

    st.markdown("### Questions the data raises")
    starter_cols = st.columns(2)
    for index, question in enumerate(report.get("conversation_starters", []), start=1):
        with starter_cols[(index - 1) % 2]:
            st.markdown(f"**{index:02d}.** {question}")

    st.markdown("### Full signal board")
    if signals:
        signal_df = pd.DataFrame(
            [
                {
                    "Rank": item.get("rank"),
                    "Priority": item.get("score"),
                    "Severity": item.get("severity"),
                    "Category": item.get("category"),
                    "Signal": item.get("title"),
                    "Observed value": item.get("signal"),
                    "Metric": item.get("proof"),
                    "Confidence": item.get("confidence"),
                }
                for item in signals
            ]
        )
        st.dataframe(
            signal_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Priority": st.column_config.ProgressColumn(
                    "Priority",
                    min_value=0,
                    max_value=100,
                    format="%d",
                ),
            },
        )


# -----------------------------------------------------------------------------
# COMPETITIVE BATTLEFIELD
# -----------------------------------------------------------------------------

with tabs[1]:
    st.markdown('<div class="section-kicker">Relative position</div>', unsafe_allow_html=True)
    st.subheader("Competitive battlefield")
    st.markdown(
        '<div class="section-copy">The cohort is not “restaurants nearby.” It is ranked using cuisine, price, positioning and location comparability, then enriched from District.</div>',
        unsafe_allow_html=True,
    )

    comp_kpis = st.columns(4)
    with comp_kpis[0]:
        render_kpi(
            "Cohort median rating",
            f"{competitive_metrics.get('cohort_rating_median'):.1f}" if competitive_metrics.get("cohort_rating_median") is not None else "—",
            "selected comparable restaurants",
        )
    with comp_kpis[1]:
        render_kpi(
            "Cohort median price",
            fmt_money(competitive_metrics.get("cohort_price_median")),
            "cost for two",
        )
    with comp_kpis[2]:
        render_kpi(
            "Reputation percentile",
            f"{competitive_metrics.get('reputation_percentile'):.0f}th" if competitive_metrics.get("reputation_percentile") is not None else "—",
            "inside this cohort only",
        )
    with comp_kpis[3]:
        render_kpi(
            "Premium justification gap",
            f"{competitive_metrics.get('premium_justification_gap'):+.0f} pts" if competitive_metrics.get("premium_justification_gap") is not None else "—",
            "reputation percentile − price percentile",
            "risk" if competitive_metrics.get("premium_justification_gap") is not None and competitive_metrics.get("premium_justification_gap") < -20 else "positive",
        )

    rows = []
    if benchmark_target:
        rows.append(
            {
                "Restaurant": restaurant,
                "Role": "TARGET",
                "Cohort Match %": 100.0,
                "Rating": benchmark_target.get("rating"),
                "Ratings / Reviews": benchmark_target.get("review_count"),
                "Cost for Two": benchmark_target.get("cost_for_two"),
                "Top Offer %": benchmark_target.get("discount_percent"),
                "Cuisines": ", ".join(benchmark_target.get("cuisines", [])[:5]),
                "Positioning": ", ".join(benchmark_target.get("positioning_tags", [])[:5]),
            }
        )

    for item in competitors:
        metric = item.get("metrics", {})
        rows.append(
            {
                "Restaurant": item.get("name"),
                "Role": "Competitor",
                "Cohort Match %": item.get("match_score", 0) * 100,
                "Rating": metric.get("rating"),
                "Ratings / Reviews": metric.get("review_count"),
                "Cost for Two": metric.get("cost_for_two"),
                "Top Offer %": metric.get("discount_percent"),
                "Cuisines": ", ".join(metric.get("cuisines", [])[:5]),
                "Positioning": ", ".join(metric.get("positioning_tags", [])[:5]),
            }
        )

    comp_df = pd.DataFrame(rows)
    if not comp_df.empty:
        st.dataframe(
            comp_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Cohort Match %": st.column_config.ProgressColumn(
                    "Cohort Match",
                    min_value=0,
                    max_value=100,
                    format="%.0f%%",
                ),
                "Rating": st.column_config.NumberColumn(format="%.1f"),
                "Ratings / Reviews": st.column_config.NumberColumn(format="%d"),
                "Cost for Two": st.column_config.NumberColumn(format="₹%d"),
                "Top Offer %": st.column_config.NumberColumn(format="%d%%"),
            },
        )

        chart_df = comp_df[
            comp_df["Rating"].notna()
            & comp_df["Cost for Two"].notna()
        ][["Restaurant", "Rating", "Cost for Two", "Ratings / Reviews"]].copy()
        if len(chart_df) >= 2:
            chart_df["Ratings / Reviews"] = chart_df["Ratings / Reviews"].fillna(1).clip(lower=1)
            st.markdown("### Price × reputation map")
            st.scatter_chart(
                chart_df,
                x="Cost for Two",
                y="Rating",
                size="Ratings / Reviews",
            )

    st.markdown("### Why each competitor made the cohort")
    for item in competitors:
        parts = item.get("match_components", {})
        with st.expander(
            f"{item.get('name', 'Competitor')} · {item.get('match_score', 0):.0%} match"
        ):
            explain_cols = st.columns(4)
            explain_values = [
                ("Cuisine", parts.get("cuisine_similarity", 0)),
                ("Price", parts.get("price_similarity", 0)),
                ("Positioning", parts.get("positioning_similarity", 0)),
                ("Location", parts.get("location_score", 0)),
            ]
            for col, (label, value) in zip(explain_cols, explain_values):
                with col:
                    st.metric(label, f"{value:.0%}")
            st.caption(
                "Final match = 35% cuisine + 30% price + 25% positioning + 10% location, with small fallback adjustments when a public page does not expose cuisine or positioning."
            )
            if item.get("url"):
                st.link_button("Open District listing", item["url"])


# -----------------------------------------------------------------------------
# CUSTOMER EXPERIENCE
# -----------------------------------------------------------------------------

with tabs[2]:
    st.markdown('<div class="section-kicker">Voice of customer</div>', unsafe_allow_html=True)
    st.subheader("Customer experience signals")
    st.markdown(
        '<div class="section-copy">Directional topic analysis from search-visible public review snippets. The dashboard shows sample size and evidence because this is not a complete review census.</div>',
        unsafe_allow_html=True,
    )

    strongest = customer_voice.get("strengths", [])
    concerns = customer_voice.get("concerns", [])
    customer_kpis = st.columns(4)
    with customer_kpis[0]:
        render_kpi("Usable review snippets", customer_voice.get("sample_size", 0), "search-visible sample")
    with customer_kpis[1]:
        render_kpi("Voice confidence", customer_voice.get("confidence", "Low"), "based on usable sample size")
    with customer_kpis[2]:
        render_kpi("Strongest advocacy", strongest[0]["topic"] if strongest else "—", "highest positive directional theme", "positive")
    with customer_kpis[3]:
        render_kpi("Biggest friction", concerns[0]["topic"] if concerns else "—", "strongest negative directional theme", "risk" if concerns else "neutral")

    st.markdown("### Experience heatmap")
    for row in customer_voice.get("topics", []):
        render_topic_row(row)

    if customer_voice.get("topics"):
        topic_df = pd.DataFrame(
            [
                {
                    "Topic": row["topic"],
                    "Mentions": row["mentions"],
                    "Positive": row["positive"],
                    "Negative": row["negative"],
                    "Net sentiment": row["net_sentiment"],
                }
                for row in customer_voice["topics"]
            ]
        )
        st.dataframe(topic_df, use_container_width=True, hide_index=True)

    st.markdown("### Drill into the evidence")
    for row in customer_voice.get("topics", [])[:8]:
        examples = row.get("examples", [])
        if not examples:
            continue
        with st.expander(
            f"{row['topic']} · {row['mentions']} mentions · net {row['net_sentiment']:+.2f}"
        ):
            for example in examples:
                st.markdown(f"**{example.get('sentiment', 'Mixed')}** · {example.get('title', '')}")
                st.write(example.get("snippet", ""))
                if example.get("url"):
                    st.markdown(example["url"])
                st.divider()


# -----------------------------------------------------------------------------
# MARKETING & DISCOVERY
# -----------------------------------------------------------------------------

with tabs[3]:
    st.markdown('<div class="section-kicker">Attention layer</div>', unsafe_allow_html=True)
    st.subheader("Marketing, creators & discovery")
    st.markdown(
        '<div class="section-copy">Visible public attention only. No paid spend, bookings, revenue or ROAS are inferred.</div>',
        unsafe_allow_html=True,
    )

    marketing_kpis = st.columns(5)
    with marketing_kpis[0]:
        render_kpi("Instagram followers", fmt_num(instagram_metrics.get("followers")), "canonical public profile")
    with marketing_kpis[1]:
        render_kpi("Instagram posts", fmt_num(instagram_metrics.get("posts")), "public profile count")
    with marketing_kpis[2]:
        render_kpi("Content sample", content_summary.get("sample_size", 0), "owned + creator/UGC")
    with marketing_kpis[3]:
        render_kpi(
            "Creator visible lift",
            f"{content_summary.get('creator_lift'):.2f}x" if content_summary.get("creator_lift") is not None else "—",
            "median creator engagement ÷ owned",
            "positive" if content_summary.get("creator_lift") and content_summary.get("creator_lift") > 1.2 else "neutral",
        )
    with marketing_kpis[4]:
        share = discovery.get("share_of_observed_mentions")
        render_kpi(
            "Discovery share",
            f"{share:.0%}" if share is not None else "—",
            "target share of observed cohort mentions",
            "risk" if share is not None and share < .15 else "neutral",
        )

    if instagram_metrics.get("bio"):
        st.markdown("### Owned brand promise")
        st.info(instagram_metrics["bio"])

    left, right = st.columns([1.15, .85])
    with left:
        st.markdown("### Observable content territories")
        themes = content_summary.get("themes", [])
        if themes:
            st.dataframe(
                pd.DataFrame(themes),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "posts": st.column_config.NumberColumn("Observed items", format="%d"),
                    "median_visible_engagement": st.column_config.NumberColumn("Median visible engagement", format="%d"),
                },
            )
        else:
            st.write("Not enough search-visible content to build a theme comparison.")

        if content_items:
            with st.expander("Content / creator evidence"):
                for item in content_items[:15]:
                    st.markdown(f"**{item.get('type')} · {item.get('theme')}**")
                    if item.get("engagement") is not None:
                        st.caption(f"Visible engagement: {item['engagement']:,}")
                    st.write(item.get("snippet", ""))
                    if item.get("url"):
                        st.markdown(item["url"])
                    st.divider()

    with right:
        st.markdown("### Earned attention")
        if earned.get("top_themes"):
            for theme, count in earned["top_themes"]:
                st.write(f"**{theme}** · {count} observed mentions")
        else:
            st.write("No strong earned-positioning theme surfaced in the current scan.")

        st.markdown("### Paid activity signal")
        if paid_signal.get("status") == "Observable public signal found":
            st.success(paid_signal["status"])
        else:
            st.info(paid_signal.get("status", "No reliable public signal detected"))
        st.caption(paid_signal.get("claim_limit", ""))

    st.markdown("### Generic discovery matrix")
    discovery_rows = []
    for row in discovery.get("queries", []):
        discovery_rows.append(
            {
                "Search occasion": row.get("query"),
                restaurant: "Surfaced" if row.get("target_found") else "Absent",
                "Competitors surfaced": ", ".join(row.get("competitors_found", [])) or "—",
            }
        )
    if discovery_rows:
        st.dataframe(
            pd.DataFrame(discovery_rows),
            use_container_width=True,
            hide_index=True,
        )
    st.caption(discovery.get("methodology", ""))


# -----------------------------------------------------------------------------
# PLATFORM INTELLIGENCE
# -----------------------------------------------------------------------------

with tabs[4]:
    st.markdown('<div class="section-kicker">Source divergence</div>', unsafe_allow_html=True)
    st.subheader("Platform intelligence")
    st.markdown(
        '<div class="section-copy">Platforms are deliberately not averaged together. Their differences are often the insight: separate review universes, different merchandising, different price expectations and different category framing.</div>',
        unsafe_allow_html=True,
    )

    if platform_tensions:
        st.markdown("### What is materially different")
        tension_cols = st.columns(2)
        for index, tension in enumerate(platform_tensions):
            with tension_cols[index % 2]:
                render_tension(tension)

    st.markdown("### Platform-by-platform comparison")
    comparison_df = pd.DataFrame(report.get("platform_comparison", []))
    if not comparison_df.empty:
        compact_columns = [
            "Platform",
            "Role",
            "Rating",
            "Δ rating vs District",
            "Ratings / Reviews",
            "Δ review pool vs District %",
            "Cost for Two",
            "Δ price vs District %",
            "Top Offer %",
            "Δ offer vs District pp",
            "Confidence",
            "Method",
        ]
        compact_df = comparison_df[[col for col in compact_columns if col in comparison_df.columns]]
        st.dataframe(
            compact_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rating": st.column_config.NumberColumn(format="%.1f"),
                "Δ rating vs District": st.column_config.NumberColumn(format="%+.1f"),
                "Ratings / Reviews": st.column_config.NumberColumn(format="%d"),
                "Δ review pool vs District %": st.column_config.NumberColumn(format="%+.0f%%"),
                "Cost for Two": st.column_config.NumberColumn(format="₹%d"),
                "Δ price vs District %": st.column_config.NumberColumn(format="%+.0f%%"),
                "Top Offer %": st.column_config.NumberColumn(format="%d%%"),
                "Δ offer vs District pp": st.column_config.NumberColumn(format="%+.0fpp"),
            },
        )

    st.markdown("### What each source is allowed to influence")
    role_cols = st.columns(5)
    for col, source in zip(
        role_cols,
        ["District", "Swiggy Dineout", "EazyDiner", "Justdial", "Web"],
    ):
        with col:
            st.markdown(
                f"""
                <div class="platform-role">
                    <div class="mini-label">{esc(PLATFORM_ROLES[source])}</div>
                    <h4>{esc(source)}</h4>
                    <p>{esc(PLATFORM_NOTES[source])}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### Detailed source framing")
    if not comparison_df.empty:
        detail_columns = [
            "Platform",
            "Cuisine framing",
            "Positioning",
            "Coverage",
            "How dashboard uses it",
            "URL",
        ]
        st.dataframe(
            comparison_df[[col for col in detail_columns if col in comparison_df.columns]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "URL": st.column_config.LinkColumn("Source"),
            },
        )

    st.info(
        "Interpretation rule: District is the apples-to-apples benchmark for the competitive cohort when available. Dineout and other sources are used to identify divergence, validate direction, and reveal different public narratives—not to create a blended rating."
    )


# -----------------------------------------------------------------------------
# DATA LAB
# -----------------------------------------------------------------------------

with tabs[5]:
    st.markdown('<div class="section-kicker">Audit everything</div>', unsafe_allow_html=True)
    st.subheader("Data Lab")
    st.markdown(
        '<div class="section-copy">This is the debugger turned into a research surface: formulas, inputs, resolver logic, stale observations, network health and raw evidence are all inspectable.</div>',
        unsafe_allow_html=True,
    )

    st.markdown("### Metric logic explorer")
    metric_dictionary = report.get("metric_dictionary", [])
    metric_names = [item["Metric"] for item in metric_dictionary]
    if metric_names:
        selected_metric_name = st.selectbox(
            "Choose a derived metric",
            metric_names,
            index=0,
        )
        metric_item = next(
            item
            for item in metric_dictionary
            if item["Metric"] == selected_metric_name
        )
        st.markdown(
            f"""
            <div class="formula-box">
                <div class="mini-label">Current value</div>
                <div style="font-size:2rem;font-weight:850;color:#f5faf7;margin:.25rem 0 .25rem;">{esc(metric_item['Value'])}</div>
                <div class="formula">{esc(metric_item['Formula'])}</div>
                <div style="color:#b9c6c0;font-size:.88rem;"><b>Live calculation:</b> {esc(metric_item['Live calculation'])}</div>
                <div style="color:#95a69e;font-size:.83rem;margin-top:.55rem;"><b>Read it as:</b> {esc(metric_item['Interpretation'])}</div>
                <div style="color:#82938b;font-size:.79rem;margin-top:.45rem;"><b>Guardrail:</b> {esc(metric_item['Guardrail'])}</div>
                <div style="color:#6f8279;font-size:.74rem;margin-top:.5rem;">Source layer: {esc(metric_item['Source'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("View the full metric dictionary"):
            st.dataframe(
                pd.DataFrame(metric_dictionary),
                use_container_width=True,
                hide_index=True,
            )

    st.markdown("### Why District resolved to this restaurant")
    resolver_rows = report["debug_data"].get("district_candidate_scores", [])
    if resolver_rows:
        resolver_df = pd.DataFrame(
            [
                {
                    "Title": row.get("title"),
                    "Name similarity": row.get("name_similarity"),
                    "Resolver score": row.get("resolver_score"),
                    "Restaurant detail page": row.get("detail_page"),
                    "Book-only page": row.get("book_only"),
                    "URL": row.get("url"),
                }
                for row in resolver_rows
            ]
        )
        st.dataframe(
            resolver_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Name similarity": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f"),
                "Resolver score": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f"),
                "URL": st.column_config.LinkColumn("Source"),
            },
        )
        st.caption(
            "Resolver score starts with restaurant-name similarity, then slightly boosts real District restaurant-detail pages and penalises book-only pages. The highest matching District restaurant page is selected; other search results remain visible for audit."
        )

    st.markdown("### Instagram freshness / indexed snapshot audit")
    instagram_snapshots = report.get("instagram_snapshots", [])
    if instagram_snapshots:
        snapshot_df = pd.DataFrame(instagram_snapshots)
        st.dataframe(
            snapshot_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Follower delta %": st.column_config.NumberColumn(format="%+.1f%%"),
                "URL": st.column_config.LinkColumn("Observation"),
            },
        )
        st.caption(
            "Canonical profile metrics are used for the headline. Reels/profile and story observations are retained as freshness checks because search indexes can reflect different crawl times."
        )

    st.markdown("### Scan performance")
    scan = report.get("scan_summary", {})
    perf_cols = st.columns(5)
    with perf_cols[0]:
        render_kpi("Total", f"{(scan.get('Total scan ms') or 0)/1000:.1f}s", "full uncached report build")
    with perf_cols[1]:
        render_kpi("Resolver", f"{(scan.get('Resolver search ms') or 0)/1000:.1f}s", "parallel profile discovery")
    with perf_cols[2]:
        render_kpi("Competitors", f"{(scan.get('Competitor engine ms') or 0)/1000:.1f}s", "parallel shortlist enrichment")
    with perf_cols[3]:
        render_kpi("Public intel", f"{(scan.get('Public intelligence ms') or 0)/1000:.1f}s", "reviews + creators + discovery")
    with perf_cols[4]:
        render_kpi("Timeouts", scan.get("Timeouts", 0), f"{scan.get('Public search errors', 0)} public-intel search errors")

    st.markdown("### Search coverage / failures")
    error_rows = report.get("search_errors", [])
    if error_rows:
        error_df = pd.DataFrame(error_rows)
        st.dataframe(
            error_df,
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            "Timeouts reduce evidence coverage but do not invalidate successfully extracted platform metrics. 'No results' is treated differently from a timeout: it means the query returned no public evidence in that scan."
        )
    else:
        st.success("No search errors were recorded in this scan.")

    st.markdown("### Direct page extraction audit")
    direct_debug = report["dining_metrics"].get("direct_page_debug", [])
    if direct_debug:
        st.dataframe(
            pd.DataFrame(direct_debug),
            use_container_width=True,
            hide_index=True,
            column_config={
                "url": st.column_config.LinkColumn("URL"),
            },
        )

    with st.expander("Raw platform evidence"):
        for source, items in report["dining_metrics"].get("by_source", {}).items():
            st.markdown(f"### {source}")
            for item in items:
                st.markdown(f"**{item.get('title', '')}**")
                st.caption(
                    f"{item.get('extraction_method', 'search_snippet').replace('_', ' ').title()} · {item.get('confidence', 'Medium')} confidence"
                )
                if item.get("snippet"):
                    st.write(item["snippet"])
                if item.get("url"):
                    st.markdown(item["url"])
                st.divider()

    with st.expander("Raw search candidates / developer JSON"):
        st.markdown("#### District candidates")
        st.json(report["debug_data"].get("district_candidates", []))
        st.markdown("#### Instagram candidates")
        st.json(report["debug_data"].get("instagram_candidates", []))
        st.markdown("#### Competitor discovery")
        st.json(report["competitor_result"])
        st.markdown("#### Public intelligence errors")
        st.json(report["public_intel"].get("errors", []))


st.divider()
st.caption(
    "Claim boundary · Dining Intelligence describes observable public-market signals. It does not infer footfall, bookings, revenue, profitability, paid spend, ROAS or causal business impact without internal restaurant data."
)
