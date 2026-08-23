import html

import pandas as pd
import streamlit as st

from collectors import (
    enrich_dining_metrics_with_pages,
    extract_dining_metrics,
    extract_instagram_content_items,
    extract_instagram_metrics,
    summarize_content_items,
    summarize_source_results,
)
from competitors import discover_competitors
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
        .stApp {
            background:
                radial-gradient(circle at 8% 0%, rgba(124, 58, 237, .08), transparent 28%),
                radial-gradient(circle at 95% 8%, rgba(14, 165, 233, .07), transparent 24%);
        }
        .block-container {
            max-width: 1500px;
            padding-top: 1.25rem;
            padding-bottom: 5rem;
        }
        .di-hero {
            position: relative;
            overflow: hidden;
            padding: 1.6rem 1.7rem;
            border-radius: 24px;
            border: 1px solid rgba(127,127,127,.18);
            background: linear-gradient(135deg, rgba(20,20,28,.96), rgba(40,31,64,.92));
            color: #f8fafc;
            margin-bottom: 1rem;
            box-shadow: 0 16px 48px rgba(0,0,0,.16);
        }
        .di-hero:after {
            content: "";
            position: absolute;
            width: 340px;
            height: 340px;
            border-radius: 999px;
            right: -120px;
            top: -180px;
            background: radial-gradient(circle, rgba(168,85,247,.30), rgba(59,130,246,.02) 70%);
        }
        .di-kicker {
            text-transform: uppercase;
            letter-spacing: .16em;
            font-weight: 800;
            font-size: .68rem;
            opacity: .72;
        }
        .di-hero h1 {
            font-size: clamp(2rem, 4vw, 3.45rem);
            line-height: 1.02;
            letter-spacing: -.045em;
            margin: .38rem 0 .55rem 0;
        }
        .di-hero p {
            max-width: 850px;
            font-size: 1rem;
            line-height: 1.55;
            color: rgba(248,250,252,.76);
            margin: 0;
        }
        .di-section-label {
            text-transform: uppercase;
            letter-spacing: .14em;
            font-size: .68rem;
            opacity: .58;
            font-weight: 800;
            margin-bottom: .15rem;
        }
        div[data-testid="stMetric"] {
            border: 1px solid rgba(127,127,127,.17);
            border-radius: 18px;
            padding: .9rem 1rem;
            background: rgba(127,127,127,.035);
            min-height: 120px;
        }
        div[data-testid="stMetricLabel"] p {
            font-weight: 700;
            letter-spacing: -.01em;
        }
        div[data-testid="stMetricValue"] {
            font-weight: 800;
            letter-spacing: -.035em;
        }
        .di-signal {
            border-radius: 18px;
            padding: 1rem 1.05rem 1rem 1.15rem;
            margin-bottom: .75rem;
            border: 1px solid rgba(127,127,127,.17);
            background: rgba(127,127,127,.035);
            min-height: 190px;
        }
        .di-signal.critical {
            border-left: 5px solid #ef4444;
            background: linear-gradient(90deg, rgba(239,68,68,.09), rgba(127,127,127,.025));
        }
        .di-signal.watch {
            border-left: 5px solid #f59e0b;
            background: linear-gradient(90deg, rgba(245,158,11,.09), rgba(127,127,127,.025));
        }
        .di-signal.opportunity {
            border-left: 5px solid #3b82f6;
            background: linear-gradient(90deg, rgba(59,130,246,.09), rgba(127,127,127,.025));
        }
        .di-signal.advantage {
            border-left: 5px solid #10b981;
            background: linear-gradient(90deg, rgba(16,185,129,.09), rgba(127,127,127,.025));
        }
        .di-signal-top {
            display:flex;
            justify-content:space-between;
            gap:.75rem;
            align-items:center;
            margin-bottom:.55rem;
        }
        .di-badge {
            display:inline-block;
            padding:.22rem .5rem;
            border-radius:999px;
            border:1px solid rgba(127,127,127,.22);
            font-size:.68rem;
            font-weight:800;
            letter-spacing:.04em;
            text-transform:uppercase;
        }
        .di-score {
            font-size:.72rem;
            opacity:.65;
            font-weight:800;
        }
        .di-signal h4 {
            margin:.15rem 0 .45rem 0;
            letter-spacing:-.02em;
            font-size:1.04rem;
        }
        .di-readout {
            font-size:.93rem;
            font-weight:800;
            margin-bottom:.45rem;
        }
        .di-why {
            font-size:.87rem;
            line-height:1.45;
            opacity:.76;
        }
        .di-proof {
            font-size:.72rem;
            opacity:.55;
            margin-top:.6rem;
        }
        .di-mini {
            padding:.85rem .95rem;
            border:1px solid rgba(127,127,127,.16);
            border-radius:16px;
            background:rgba(127,127,127,.025);
            margin-bottom:.55rem;
        }
        .di-mini strong {font-size:.94rem;}
        .di-mini p {font-size:.82rem; opacity:.72; margin:.3rem 0 0 0; line-height:1.4;}
        .stTabs [data-baseweb="tab-list"] {
            gap: .35rem;
            padding: .25rem;
            border-radius: 14px;
            background: rgba(127,127,127,.045);
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            padding-left: .9rem;
            padding-right: .9rem;
        }
        .stTabs [aria-selected="true"] {
            background: rgba(124,58,237,.11);
        }
        [data-testid="stDataFrame"] {
            border: 1px solid rgba(127,127,127,.14);
            border-radius: 14px;
            overflow: hidden;
        }
        .di-note {
            border:1px solid rgba(127,127,127,.16);
            border-radius:14px;
            padding:.85rem 1rem;
            font-size:.84rem;
            opacity:.78;
            margin-top:.75rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def fmt_money(value):
    return f"₹{value:,.0f}" if value is not None else "—"


def fmt_num(value):
    return f"{value:,.0f}" if value is not None else "—"


def fmt_pct(value):
    return f"{value:.0f}%" if value is not None else "—"


def safe(value):
    return html.escape(str(value or ""))


def render_signal_card(item):
    css_class = item.get("severity", "Watch").lower()
    st.markdown(
        f"""
        <div class="di-signal {css_class}">
            <div class="di-signal-top">
                <span class="di-badge">#{item.get('rank', '—')} · {safe(item.get('severity'))} · {safe(item.get('category'))}</span>
                <span class="di-score">Priority {item.get('score', 0)}/100</span>
            </div>
            <h4>{safe(item.get('title'))}</h4>
            <div class="di-readout">{safe(item.get('signal'))}</div>
            <div class="di-why">{safe(item.get('why'))}</div>
            <div class="di-proof">Proof: {safe(item.get('proof'))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_mini(title, body):
    st.markdown(
        f"""
        <div class="di-mini">
            <strong>{safe(title)}</strong>
            <p>{safe(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# HERO + SEARCH
# -----------------------------------------------------------------------------

st.markdown(
    """
    <div class="di-hero">
        <div class="di-kicker">Restaurant Market Intelligence</div>
        <h1>Find the signal hiding in the noise.</h1>
        <p>
            A public-data intelligence dashboard built to surface competitive anomalies,
            reputation tensions, customer frictions, discovery gaps, positioning white space
            and marketing signals — with evidence behind every readout.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("restaurant_search"):
    left, right = st.columns([1.45, 1])
    with left:
        restaurant = st.text_input(
            "Restaurant",
            placeholder="Kijiji - On The Roof",
        )
    with right:
        location = st.text_input(
            "Location",
            placeholder="Gurgaon",
        )
    submitted = st.form_submit_button(
        "Run Intelligence Scan",
        type="primary",
        use_container_width=True,
    )


if not submitted:
    st.markdown(
        """
        <div class="di-note">
            The scan prioritises anomalies rather than generic recommendations. District is used
            for the primary dine-in benchmark where available, while Swiggy Dineout, Instagram,
            creator/UGC, earned web attention, search discovery and other public sources provide
            cross-checks and additional intelligence.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

if not restaurant or not location:
    st.warning("Please enter both restaurant name and location.")
    st.stop()


# -----------------------------------------------------------------------------
# INTELLIGENCE PIPELINE
# -----------------------------------------------------------------------------

with st.status("Scanning the public market...", expanded=True) as status:
    st.write("Resolving dining, social and web identities...")
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

    st.write("Extracting high-confidence dining metrics...")
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
    benchmark_target = district_summary or source_summaries.get("Swiggy Dineout") or {}

    instagram_metrics = extract_instagram_metrics(data.get("instagram"))

    target_context = " ".join(
        [
            instagram_metrics.get("bio") or "",
            " ".join(
                result.get("snippet", "")
                for result in data.get("general_results", [])[:8]
            ),
        ]
    )

    st.write("Building the competitive cohort and benchmarking the restaurant...")
    competitor_result = discover_competitors(
        restaurant=restaurant,
        location=location,
        target_summary=benchmark_target,
        target_context=target_context,
        limit=5,
    )
    competitors = competitor_result.get("competitors", [])
    competitor_names = [item["name"] for item in competitors]

    st.write("Reading customer voice, content, creators, earned attention and discovery...")
    public_intel = collect_public_intelligence(
        restaurant=restaurant,
        location=location,
        instagram_handle=instagram_metrics.get("handle"),
        competitor_names=competitor_names,
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
    )
    conversation_starters = build_conversation_starters(signals)

    status.update(label="Intelligence scan complete", state="complete")


# -----------------------------------------------------------------------------
# REPORT HEADER
# -----------------------------------------------------------------------------

st.markdown("---")
header_left, header_right = st.columns([3.4, 1])
with header_left:
    st.markdown('<div class="di-section-label">Live public-market read</div>', unsafe_allow_html=True)
    st.header(restaurant)
    st.caption(location)
with header_right:
    st.metric("Evidence coverage", f"{health.get('coverage', 0)}%")

if not district_summary:
    st.warning(
        "District did not return a high-confidence primary snapshot. The dashboard is using "
        "the strongest available dining source directionally and keeps the evidence labelled."
    )

critical_count = sum(item["severity"] == "Critical" for item in signals)
watch_count = sum(item["severity"] == "Watch" for item in signals)
opportunity_count = sum(item["severity"] == "Opportunity" for item in signals)
advantage_count = sum(item["severity"] == "Advantage" for item in signals)

summary_cols = st.columns(4)
summary_cols[0].metric("Critical anomalies", critical_count)
summary_cols[1].metric("Watch signals", watch_count)
summary_cols[2].metric("Opportunity signals", opportunity_count)
summary_cols[3].metric("Visible advantages", advantage_count)


tabs = st.tabs(
    [
        "📡 Signal Radar",
        "🥊 Competitive Battlefield",
        "💬 Customer Friction",
        "📣 Marketing & Discovery",
        "🧭 Proposition & Sources",
        "🧪 Evidence Lab",
    ]
)


# -----------------------------------------------------------------------------
# TAB 1 — SIGNAL RADAR
# -----------------------------------------------------------------------------

with tabs[0]:
    st.markdown('<div class="di-section-label">Priority intelligence</div>', unsafe_allow_html=True)
    st.subheader("What deserves attention first")
    st.caption(
        "Priority scores rank the unusualness and decision relevance of observable public signals. "
        "They are not business-performance scores."
    )

    price_index = competitive_metrics.get("price_index")
    rating_gap = competitive_metrics.get("rating_gap")
    volume_index = competitive_metrics.get("rating_volume_index")
    search_share = discovery.get("share_of_observed_mentions")

    pulse_cols = st.columns(5)
    pulse_cols[0].metric(
        "Price vs cohort",
        f"{price_index:.2f}x" if price_index is not None else "—",
        delta=f"{(price_index - 1) * 100:+.0f}%" if price_index is not None else None,
    )
    pulse_cols[1].metric(
        "Rating gap",
        f"{rating_gap:+.1f}" if rating_gap is not None else "—",
    )
    pulse_cols[2].metric(
        "Interaction vs cohort",
        f"{volume_index:.2f}x" if volume_index is not None else "—",
    )
    pulse_cols[3].metric(
        "Search share",
        f"{search_share:.0%}" if search_share is not None else "—",
    )
    pulse_cols[4].metric(
        "External health context",
        f"{health['score']:.0f}/100" if health.get("score") is not None else "—",
    )

    st.markdown("#### Ranked signal wall")
    if signals:
        card_columns = st.columns(2)
        for index, item in enumerate(signals[:8]):
            with card_columns[index % 2]:
                render_signal_card(item)
    else:
        st.info("The scan did not find a sufficiently strong anomaly in the current public sample.")

    st.markdown("#### Full signal board")
    if signals:
        signal_df = pd.DataFrame(
            [
                {
                    "Rank": item["rank"],
                    "Priority": item["score"],
                    "Status": item["severity"],
                    "Category": item["category"],
                    "Signal": item["title"],
                    "Readout": item["signal"],
                    "Why it matters": item["why"],
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

    left, right = st.columns([1.15, 1])
    with left:
        st.markdown("#### Conversation ammo")
        st.caption("Questions created by the anomalies — not generic consulting prompts.")
        for index, question in enumerate(conversation_starters, start=1):
            render_mini(f"0{index}", question)

    with right:
        st.markdown("#### Cross-source contradiction check")
        render_mini(
            "Rating spread",
            f"{cross_source_metrics.get('rating_spread'):.1f} points across observed platforms"
            if cross_source_metrics.get("rating_spread") is not None
            else "Insufficient comparable public ratings across platforms.",
        )
        render_mini(
            "Price spread",
            f"{fmt_money(cross_source_metrics.get('price_spread'))} across observed cost-for-two signals"
            if cross_source_metrics.get("price_spread") is not None
            else "Insufficient comparable public price signals across platforms.",
        )
        render_mini(
            "Largest public review base",
            fmt_num(cross_source_metrics.get("max_public_review_count")),
        )
        render_mini(
            "Customer voice confidence",
            f"{customer_voice.get('confidence', 'Low')} · {customer_voice.get('sample_size', 0)} usable public review snippets",
        )


# -----------------------------------------------------------------------------
# TAB 2 — COMPETITIVE BATTLEFIELD
# -----------------------------------------------------------------------------

with tabs[1]:
    st.markdown('<div class="di-section-label">Competitive intelligence</div>', unsafe_allow_html=True)
    st.subheader("Where the restaurant sits in the battlefield")
    st.caption(
        "The cohort is selected using public District similarity signals including cuisine, price, "
        "location and positioning. Match score represents comparability, not performance."
    )

    rows = []
    if benchmark_target:
        rows.append(
            {
                "Restaurant": restaurant,
                "Role": "TARGET",
                "Match %": 100.0,
                "Rating": benchmark_target.get("rating"),
                "Ratings / Reviews": benchmark_target.get("review_count"),
                "Cost for Two": benchmark_target.get("cost_for_two"),
                "Offer %": benchmark_target.get("discount_percent"),
                "Positioning": ", ".join(benchmark_target.get("positioning_tags", [])[:4]),
            }
        )

    for item in competitors:
        metric = item.get("metrics", {})
        rows.append(
            {
                "Restaurant": item.get("name"),
                "Role": "COMPETITOR",
                "Match %": item.get("match_score", 0) * 100,
                "Rating": metric.get("rating"),
                "Ratings / Reviews": metric.get("review_count"),
                "Cost for Two": metric.get("cost_for_two"),
                "Offer %": metric.get("discount_percent"),
                "Positioning": ", ".join(metric.get("positioning_tags", [])[:4]),
            }
        )

    comp_df = pd.DataFrame(rows)
    if not comp_df.empty:
        st.dataframe(
            comp_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Match %": st.column_config.ProgressColumn(
                    "Cohort Match",
                    min_value=0,
                    max_value=100,
                    format="%.0f%%",
                ),
                "Rating": st.column_config.NumberColumn(format="%.1f"),
                "Ratings / Reviews": st.column_config.NumberColumn(format="%d"),
                "Cost for Two": st.column_config.NumberColumn(format="₹%d"),
                "Offer %": st.column_config.NumberColumn(format="%d%%"),
            },
        )

        chart_df = comp_df[
            comp_df["Rating"].notna() & comp_df["Cost for Two"].notna()
        ][["Restaurant", "Rating", "Cost for Two", "Ratings / Reviews"]].copy()
        if len(chart_df) >= 2:
            chart_df["Ratings / Reviews"] = chart_df["Ratings / Reviews"].fillna(1).clip(lower=1)
            st.markdown("#### Price × reputation map")
            st.scatter_chart(
                chart_df,
                x="Cost for Two",
                y="Rating",
                size="Ratings / Reviews",
            )

    b1, b2, b3, b4, b5 = st.columns(5)
    b1.metric(
        "Cohort rating median",
        f"{competitive_metrics['cohort_rating_median']:.1f}"
        if competitive_metrics.get("cohort_rating_median") is not None else "—",
    )
    b2.metric("Cohort price median", fmt_money(competitive_metrics.get("cohort_price_median")))
    b3.metric("Reputation percentile", fmt_pct(competitive_metrics.get("reputation_percentile")))
    b4.metric("Price percentile", fmt_pct(competitive_metrics.get("price_percentile")))
    b5.metric(
        "Premium justification gap",
        f"{competitive_metrics['premium_justification_gap']:+.0f} pts"
        if competitive_metrics.get("premium_justification_gap") is not None else "—",
    )

    st.markdown("#### Closest competitive matches")
    for item in competitors:
        parts = item.get("match_components", {})
        render_mini(
            f"{item.get('name')} · {item.get('match_score', 0):.0%} match",
            "Cuisine {0:.0%} · Price {1:.0%} · Positioning {2:.0%}".format(
                parts.get("cuisine_similarity", 0),
                parts.get("price_similarity", 0),
                parts.get("positioning_similarity", 0),
            ),
        )


# -----------------------------------------------------------------------------
# TAB 3 — CUSTOMER FRICTION
# -----------------------------------------------------------------------------

with tabs[2]:
    st.markdown('<div class="di-section-label">Customer intelligence</div>', unsafe_allow_html=True)
    st.subheader("What customers reward — and where experience leaks")
    st.caption(
        "Directional topic analysis from search-visible public review snippets. The sample is deliberately "
        "shown with confidence rather than presented as a complete review census."
    )

    v1, v2, v3, v4 = st.columns(4)
    v1.metric("Usable snippets", customer_voice.get("sample_size", 0))
    v2.metric("Confidence", customer_voice.get("confidence", "Low"))
    strongest = customer_voice.get("strengths", [{}])[0].get("topic") if customer_voice.get("strengths") else None
    riskiest = customer_voice.get("concerns", [{}])[0].get("topic") if customer_voice.get("concerns") else None
    v3.metric("Strongest advocacy", strongest or "—")
    v4.metric("Clearest friction", riskiest or "—")

    topic_rows = []
    for row in customer_voice.get("topics", []):
        mentions = row.get("mentions", 0)
        topic_rows.append(
            {
                "Topic": row.get("topic"),
                "Mentions": mentions,
                "Positive %": (row.get("positive", 0) / mentions * 100) if mentions else 0,
                "Negative %": (row.get("negative", 0) / mentions * 100) if mentions else 0,
                "Net sentiment": row.get("net_sentiment", 0),
            }
        )

    if topic_rows:
        topic_df = pd.DataFrame(topic_rows).sort_values(
            ["Negative %", "Mentions"],
            ascending=[False, False],
        )
        st.dataframe(
            topic_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Positive %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f%%"),
                "Negative %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f%%"),
                "Net sentiment": st.column_config.NumberColumn(format="%.2f"),
            },
        )

        st.markdown("#### Topic intensity")
        st.bar_chart(topic_df.set_index("Topic")[["Mentions"]])

    praise_col, friction_col = st.columns(2)
    with praise_col:
        st.markdown("#### Advocacy pockets")
        if customer_voice.get("strengths"):
            for item in customer_voice["strengths"]:
                mentions = item.get("mentions", 0)
                positive_share = item.get("positive", 0) / mentions if mentions else 0
                render_mini(
                    item.get("topic"),
                    f"{mentions} observed mentions · {positive_share:.0%} positive skew",
                )
        else:
            st.info("No clear positive pattern in the current observable sample.")

    with friction_col:
        st.markdown("#### Friction pockets")
        if customer_voice.get("concerns"):
            for item in customer_voice["concerns"]:
                mentions = item.get("mentions", 0)
                negative_share = item.get("negative", 0) / mentions if mentions else 0
                render_mini(
                    item.get("topic"),
                    f"{mentions} observed mentions · {negative_share:.0%} negative skew",
                )
        else:
            st.info("No clear negative pattern in the current observable sample.")

    with st.expander("Open review evidence"):
        for result in customer_voice.get("evidence", [])[:20]:
            st.markdown(f"**{result.get('title', '')}**")
            st.write(result.get("snippet", ""))
            if result.get("url"):
                st.markdown(result["url"])
            st.divider()


# -----------------------------------------------------------------------------
# TAB 4 — MARKETING & DISCOVERY
# -----------------------------------------------------------------------------

with tabs[3]:
    st.markdown('<div class="di-section-label">Attention intelligence</div>', unsafe_allow_html=True)
    st.subheader("How the brand earns and loses attention")
    st.caption("Visible public signals only — no spend, bookings, ROAS or causal impact is inferred.")

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Instagram followers", fmt_num(instagram_metrics.get("followers")))
    m2.metric("Instagram posts", fmt_num(instagram_metrics.get("posts")))
    m3.metric("Content sample", content_summary.get("sample_size", 0))
    lift = content_summary.get("creator_lift")
    m4.metric("Creator lift", f"{lift:.1f}x" if lift is not None else "—")
    m5.metric("Earned mentions", earned.get("count", 0))
    m6.metric("Search share", f"{search_share:.0%}" if search_share is not None else "—")

    if instagram_metrics.get("bio"):
        st.markdown("#### Owned brand promise")
        st.info(instagram_metrics.get("bio"))

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("#### Content mix")
        theme_rows = content_summary.get("themes", [])
        if theme_rows:
            theme_df = pd.DataFrame(theme_rows)
            st.dataframe(theme_df, use_container_width=True, hide_index=True)
        else:
            st.info("Not enough observable content evidence to classify the mix.")

        st.markdown("#### Creator / UGC evidence")
        creator_items = [item for item in content_items if item.get("type") != "Owned"]
        if creator_items:
            for item in creator_items[:6]:
                engagement = item.get("engagement")
                suffix = f" · {engagement:,} visible engagements" if engagement is not None else ""
                render_mini(
                    f"{item.get('type')} · {item.get('theme')}{suffix}",
                    item.get("snippet", "")[:280],
                )
        else:
            st.info("No reliable creator/UGC sample was observed in this scan.")

    with right:
        st.markdown("#### Earned positioning")
        if earned.get("top_themes"):
            for theme, count in earned.get("top_themes", []):
                render_mini(theme, f"{count} observable earned mentions")
        else:
            st.info("No strong earned-positioning theme detected.")

        st.markdown("#### Paid activity signal")
        if paid_signal.get("status") == "Observable public signal found":
            st.success(paid_signal.get("status"))
        else:
            st.info(paid_signal.get("status"))
        st.caption(paid_signal.get("claim_limit", ""))

    st.markdown("#### Generic discovery battlefield")
    discovery_rows = []
    for row in discovery.get("queries", []):
        discovery_rows.append(
            {
                "Search": row.get("query"),
                "Target surfaced": "YES" if row.get("target_found") else "NO",
                "Competitors surfaced": ", ".join(row.get("competitors_found", [])) or "—",
            }
        )
    if discovery_rows:
        st.dataframe(pd.DataFrame(discovery_rows), use_container_width=True, hide_index=True)
    st.caption(discovery.get("methodology", ""))


# -----------------------------------------------------------------------------
# TAB 5 — PROPOSITION & SOURCES
# -----------------------------------------------------------------------------

with tabs[4]:
    st.markdown('<div class="di-section-label">Proposition intelligence</div>', unsafe_allow_html=True)
    st.subheader("What the market is being asked to believe")

    if benchmark_target:
        p1, p2, p3, p4, p5 = st.columns(5)
        p1.metric(
            "Primary rating",
            f"{benchmark_target.get('rating'):.1f}" if benchmark_target.get("rating") is not None else "—",
        )
        p2.metric("Cost for two", fmt_money(benchmark_target.get("cost_for_two")))
        p3.metric(
            "Visible offer",
            benchmark_target.get("offers", [None])[0] if benchmark_target.get("offers") else "—",
        )
        p4.metric("Price percentile", fmt_pct(competitive_metrics.get("price_percentile")))
        p5.metric("Reputation percentile", fmt_pct(competitive_metrics.get("reputation_percentile")))

        pos_left, pos_right = st.columns(2)
        with pos_left:
            st.markdown("#### Public proposition")
            tags = benchmark_target.get("positioning_tags", [])
            cuisines = benchmark_target.get("cuisines", [])
            render_mini("Experience / occasion", " · ".join(tags) if tags else "No strong occasion tag detected")
            render_mini("Cuisine", " · ".join(cuisines) if cuisines else "No strong cuisine signal detected")
            render_mini("Visible offers", " · ".join(benchmark_target.get("offers", [])) or "No visible offer extracted")

        with pos_right:
            st.markdown("#### Customer reality")
            positive_topics = [item.get("topic") for item in customer_voice.get("strengths", [])]
            concern_topics = [item.get("topic") for item in customer_voice.get("concerns", [])]
            render_mini("What public customers visibly prove", ", ".join(positive_topics) or "No strong proof theme in sample")
            render_mini("Execution risk signals", ", ".join(concern_topics) or "No clear negative theme in sample")
            render_mini(
                "Earned memory",
                ", ".join(theme for theme, _count in earned.get("top_themes", [])[:4]) or "No strong earned-memory theme",
            )

    st.markdown("#### Cross-source lens")
    source_rows = []
    for source, summary in source_summaries.items():
        if not summary:
            continue
        source_rows.append(
            {
                "Source": source,
                "Rating": summary.get("rating"),
                "Ratings / Reviews": summary.get("review_count"),
                "Cost for Two": summary.get("cost_for_two"),
                "Top Offer": summary.get("offers", [None])[0] if summary.get("offers") else None,
                "Confidence": summary.get("confidence"),
                "Method": summary.get("method", "").replace("_", " ").title(),
            }
        )
    if source_rows:
        st.dataframe(pd.DataFrame(source_rows), use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# TAB 6 — EVIDENCE LAB
# -----------------------------------------------------------------------------

with tabs[5]:
    st.markdown('<div class="di-section-label">Evidence layer</div>', unsafe_allow_html=True)
    st.subheader("Challenge any signal")
    st.caption(
        "Use this area when a restaurant owner pushes back. Direct public-page values, search observations, "
        "cohort selection and raw evidence remain visible rather than hidden behind the dashboard."
    )

    profiles = [
        ("District", data.get("district")),
        ("Swiggy Dineout", data.get("dineout")),
        ("Instagram", data.get("instagram")),
        ("Official Website", data.get("website")),
    ]
    profile_cols = st.columns(4)
    for col, (name, result) in zip(profile_cols, profiles):
        with col:
            st.markdown(f"**{name}**")
            if result and result.get("url"):
                st.success("Identified")
                st.link_button("Open source", result["url"])
            else:
                st.warning("Not confidently identified")

    st.markdown("#### Direct extraction audit")
    direct_debug = dining_metrics.get("direct_page_debug", [])
    if direct_debug:
        st.dataframe(pd.DataFrame(direct_debug), use_container_width=True, hide_index=True)

    with st.expander("Dining evidence by source"):
        for source, items in dining_metrics.get("by_source", {}).items():
            st.markdown(f"### {source}")
            for item in items:
                st.markdown(f"**{item.get('title', '')}**")
                st.caption(
                    f"{item.get('extraction_method', 'search_snippet').replace('_', ' ').title()} · "
                    f"{item.get('confidence', 'Medium')} confidence"
                )
                if item.get("snippet"):
                    st.write(item.get("snippet"))
                if item.get("url"):
                    st.markdown(item.get("url"))
                st.divider()

    with st.expander("Competitive cohort logic"):
        st.json(competitor_result)

    with st.expander("Customer voice evidence"):
        for result in customer_voice.get("evidence", [])[:25]:
            st.markdown(f"**{result.get('title', '')}**")
            st.write(result.get("snippet", ""))
            if result.get("url"):
                st.markdown(result.get("url"))
            st.divider()

    with st.expander("Earned and paid-signal evidence"):
        st.markdown("### Earned")
        for item in earned.get("evidence", []):
            st.markdown(f"**{item.get('title', '')}**")
            st.write(item.get("snippet", ""))
            if item.get("url"):
                st.markdown(item.get("url"))
            st.divider()
        st.markdown("### Paid-signal observations")
        for item in paid_signal.get("evidence", []):
            st.markdown(f"**{item.get('title', '')}**")
            st.write(item.get("snippet", ""))
            if item.get("url"):
                st.markdown(item.get("url"))
            st.divider()

    with st.expander("Developer debug"):
        st.write("District candidates")
        st.json(debug_data.get("district_candidates", []))
        st.write("Instagram candidates")
        st.json(debug_data.get("instagram_candidates", []))
        st.write("Public intelligence errors")
        st.json(public_intel.get("errors", []))


st.markdown("---")
st.caption(
    "Claim boundary: the dashboard surfaces observable public-market signals and anomalies. "
    "It does not infer footfall, bookings, revenue, profitability, paid spend, ROAS or causal impact without internal restaurant data."
)
