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
    consultant_workspace,
    detect_paid_signal,
    generate_core_insights,
)
from metrics import (
    build_competitive_metrics,
    build_cross_source_metrics,
    external_health_score,
)
from search_engine import collect_public_intelligence, resolve_restaurant


st.set_page_config(page_title="Dining Intelligence", page_icon="🍽️", layout="wide")

st.markdown(
    """
    <style>
        .block-container {padding-top: 2rem; padding-bottom: 4rem;}
        .hero {padding: 1.25rem 1.5rem; border: 1px solid rgba(128,128,128,.22); border-radius: 18px; margin-bottom: 1rem;}
        .eyebrow {text-transform: uppercase; letter-spacing: .12em; font-size: .72rem; opacity: .65; font-weight: 700;}
        .insight-card {padding: 1rem 1.1rem; border: 1px solid rgba(128,128,128,.22); border-radius: 14px; margin-bottom: .8rem;}
        .muted {opacity: .7;}
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


def render_insight(insight):
    kind = insight.get("type", "Insight")
    icon = {"Strength": "✅", "Gap": "⚠️", "Opportunity": "🚀"}.get(kind, "💡")
    st.markdown(
        f"""
        <div class="insight-card">
            <div class="eyebrow">{icon} {kind} · {insight.get('confidence', 'Medium')} confidence</div>
            <h4 style="margin:.35rem 0 .5rem 0;">{insight.get('title', '')}</h4>
            <div><b>Observation:</b> {insight.get('observation', '')}</div>
            <div style="margin-top:.35rem;"><b>Why it matters:</b> {insight.get('implication', '')}</div>
            <div style="margin-top:.35rem;"><b>Action:</b> {insight.get('recommendation', '')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">Restaurant Consultant Intelligence Engine</div>
        <h1 style="margin:.25rem 0 .35rem 0;">🍽️ Dining Intelligence</h1>
        <div class="muted">Competitive position, customer voice, marketing traction and consultant-grade recommendations built from observable public dining data.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("restaurant_search"):
    col1, col2 = st.columns([1.4, 1])
    with col1:
        restaurant = st.text_input("Restaurant", placeholder="Kijiji - On The Roof")
    with col2:
        location = st.text_input("Location", placeholder="Gurgaon")
    submitted = st.form_submit_button("Generate Intelligence Report", type="primary", use_container_width=True)


if submitted:
    if not restaurant or not location:
        st.warning("Please enter both restaurant name and location.")
        st.stop()

    with st.status("Building consultant-grade public intelligence...", expanded=True) as status:
        st.write("Resolving the restaurant across dining and marketing platforms...")
        data = resolve_restaurant(restaurant, location)
        debug_data = data.get("debug", {})

        all_dining_candidates = (
            debug_data.get("district_candidates", [])
            + debug_data.get("dineout_candidates", [])
            + debug_data.get("metric_candidates", [])
            + data.get("general_results", [])
        )

        dining_metrics = extract_dining_metrics(primary_result=data.get("district"), supporting_results=all_dining_candidates)

        direct_urls = []
        if data.get("district") and data["district"].get("url"):
            direct_urls.append(data["district"]["url"])
        if data.get("dineout") and data["dineout"].get("url"):
            direct_urls.append(data["dineout"]["url"])

        st.write("Extracting high-confidence dining metrics from public restaurant pages...")
        dining_metrics = enrich_dining_metrics_with_pages(dining_metrics, direct_urls)

        source_summaries = {
            source: summarize_source_results(dining_metrics.get("by_source", {}).get(source, []))
            for source in ["District", "Swiggy Dineout", "EazyDiner", "Justdial", "Web"]
        }

        district_summary = source_summaries.get("District")
        benchmark_target = district_summary or source_summaries.get("Swiggy Dineout")
        instagram_metrics = extract_instagram_metrics(data.get("instagram"))

        target_context = " ".join([
            instagram_metrics.get("bio") or "",
            " ".join(result.get("snippet", "") for result in data.get("general_results", [])[:6]),
        ])

        st.write("Discovering and scoring a comparable District competitive cohort...")
        competitor_result = discover_competitors(
            restaurant=restaurant,
            location=location,
            target_summary=benchmark_target or {},
            target_context=target_context,
            limit=5,
        )
        competitors = competitor_result["competitors"]
        competitor_names = [item["name"] for item in competitors]

        st.write("Reading customer voice, creator activity, earned attention and search discovery...")
        public_intel = collect_public_intelligence(
            restaurant=restaurant,
            location=location,
            instagram_handle=instagram_metrics.get("handle"),
            competitor_names=competitor_names,
        )

        content_items = extract_instagram_content_items(
            debug_data.get("instagram_candidates", []) + public_intel.get("creators", []),
            restaurant_handle=instagram_metrics.get("handle"),
        )
        content_summary = summarize_content_items(content_items)
        customer_voice = analyze_customer_voice(public_intel.get("reviews", []))
        earned = analyze_earned_attention(public_intel.get("earned", []))
        discovery = analyze_discovery(public_intel.get("discovery", []), restaurant, competitor_names)
        paid_signal = detect_paid_signal(public_intel.get("paid", []), restaurant)

        competitive_metrics = build_competitive_metrics(benchmark_target or {}, competitors)
        cross_source_metrics = build_cross_source_metrics(source_summaries)
        health = external_health_score(benchmark_target or {}, competitive_metrics, instagram_metrics, content_summary)

        insights = generate_core_insights(
            competitive_metrics=competitive_metrics,
            cross_source_metrics=cross_source_metrics,
            customer_voice=customer_voice,
            content_summary=content_summary,
            discovery=discovery,
            target_summary=benchmark_target or {},
        )
        workspace = consultant_workspace(insights, customer_voice, benchmark_target or {})

        status.update(label="Dining Intelligence report ready", state="complete")

    st.divider()
    header_col, coverage_col = st.columns([3, 1])
    with header_col:
        st.header(restaurant)
        st.caption(location)
    with coverage_col:
        st.metric("Public-data coverage", f"{health.get('coverage', 0)}%")

    if not district_summary:
        st.warning("A high-confidence District snapshot was not available, so the report uses the strongest available dining source for directional analysis.")

    tabs = st.tabs([
        "⚡ Executive Diagnostic",
        "🏁 Competition",
        "💬 Customer Voice",
        "📣 Marketing & Content",
        "🍸 Dining Proposition",
        "🧠 Consultant Workspace",
        "🔎 Evidence",
    ])

    with tabs[0]:
        st.subheader("External Restaurant Health")
        st.caption("Directional public-market score — not revenue, footfall, profitability or ROAS.")
        top1, top2, top3, top4 = st.columns(4)
        with top1:
            st.metric("External Health", f"{health['score']:.0f}/100" if health.get("score") is not None else "—")
            if health.get("score") is not None:
                st.progress(int(health["score"]) / 100)
        with top2:
            price_index = competitive_metrics.get("price_index")
            st.metric("Price vs cohort", f"{price_index:.2f}x" if price_index is not None else "—", delta=f"{(price_index - 1) * 100:+.0f}%" if price_index is not None else None)
        with top3:
            rating_gap = competitive_metrics.get("rating_gap")
            st.metric("Rating gap", f"{rating_gap:+.1f}" if rating_gap is not None else "—", delta="vs cohort median" if rating_gap is not None else None)
        with top4:
            volume_index = competitive_metrics.get("rating_volume_index")
            st.metric("Public interaction index", f"{volume_index:.2f}x" if volume_index is not None else "—", delta="rating/review volume vs median" if volume_index is not None else None)

        if health.get("components"):
            st.markdown("#### What drives the score")
            component_df = pd.DataFrame([{"Dimension": key, "Score": value} for key, value in health["components"].items()]).set_index("Dimension")
            st.bar_chart(component_df)

        st.markdown("#### Consultant diagnosis")
        if insights:
            for insight in insights[:5]:
                render_insight(insight)
        else:
            st.info("Public evidence is currently too thin for a strong diagnosis. The Evidence tab shows exactly what was and was not observable.")

        st.markdown("#### Cross-source reality check")
        x1, x2, x3 = st.columns(3)
        with x1:
            st.metric("Observed rating spread", f"{cross_source_metrics['rating_spread']:.1f}" if cross_source_metrics.get("rating_spread") is not None else "—")
        with x2:
            st.metric("Observed price spread", fmt_money(cross_source_metrics.get("price_spread")))
        with x3:
            st.metric("Largest public review base", fmt_num(cross_source_metrics.get("max_public_review_count")))

    with tabs[1]:
        st.subheader("Competitive Position")
        st.caption("Cohort is selected from District using cuisine, price, location and occasion/positioning similarity. Match score is comparability, not performance.")
        rows = []
        if benchmark_target:
            rows.append({
                "Restaurant": restaurant,
                "Role": "Target",
                "Match": 1.0,
                "Rating": benchmark_target.get("rating"),
                "Ratings / Reviews": benchmark_target.get("review_count"),
                "Cost for Two": benchmark_target.get("cost_for_two"),
                "Top Offer %": benchmark_target.get("discount_percent"),
                "Cuisines": ", ".join(benchmark_target.get("cuisines", [])[:4]),
                "Positioning": ", ".join(benchmark_target.get("positioning_tags", [])[:4]),
            })
        for item in competitors:
            metric = item["metrics"]
            rows.append({
                "Restaurant": item["name"],
                "Role": "Competitor",
                "Match": item["match_score"],
                "Rating": metric.get("rating"),
                "Ratings / Reviews": metric.get("review_count"),
                "Cost for Two": metric.get("cost_for_two"),
                "Top Offer %": metric.get("discount_percent"),
                "Cuisines": ", ".join(metric.get("cuisines", [])[:4]),
                "Positioning": ", ".join(metric.get("positioning_tags", [])[:4]),
            })

        comp_df = pd.DataFrame(rows)
        if not comp_df.empty:
            st.dataframe(
                comp_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Match": st.column_config.ProgressColumn("Cohort Match", min_value=0, max_value=1, format="%.0f%%"),
                    "Rating": st.column_config.NumberColumn(format="%.1f"),
                    "Ratings / Reviews": st.column_config.NumberColumn(format="%d"),
                    "Cost for Two": st.column_config.NumberColumn(format="₹%d"),
                    "Top Offer %": st.column_config.NumberColumn(format="%d%%"),
                },
            )
            chart_df = comp_df[comp_df["Rating"].notna() & comp_df["Cost for Two"].notna()][["Restaurant", "Rating", "Cost for Two", "Ratings / Reviews"]].copy()
            if len(chart_df) >= 2:
                chart_df["Ratings / Reviews"] = chart_df["Ratings / Reviews"].fillna(1).clip(lower=1)
                st.markdown("#### Price vs reputation map")
                st.scatter_chart(chart_df, x="Cost for Two", y="Rating", size="Ratings / Reviews")

        b1, b2, b3, b4 = st.columns(4)
        with b1:
            st.metric("Cohort median rating", f"{competitive_metrics['cohort_rating_median']:.1f}" if competitive_metrics.get("cohort_rating_median") is not None else "—")
        with b2:
            st.metric("Cohort median price", fmt_money(competitive_metrics.get("cohort_price_median")))
        with b3:
            st.metric("Reputation percentile", fmt_pct(competitive_metrics.get("reputation_percentile")))
        with b4:
            st.metric("Premium justification gap", f"{competitive_metrics['premium_justification_gap']:+.0f} pts" if competitive_metrics.get("premium_justification_gap") is not None else "—")

        with st.expander("Why these competitors?"):
            for item in competitors:
                parts = item["match_components"]
                st.markdown(f"**{item['name']} — {item['match_score']:.0%} match**")
                st.write(f"Cuisine {parts['cuisine_similarity']:.0%} · Price {parts['price_similarity']:.0%} · Positioning {parts['positioning_similarity']:.0%}")
                if item.get("url"):
                    st.markdown(item["url"])

    with tabs[2]:
        st.subheader("Customer Voice")
        st.caption("Directional topic analysis from search-visible public review snippets. This is not a complete review census.")
        v1, v2, v3 = st.columns(3)
        with v1:
            st.metric("Usable review snippets", customer_voice.get("sample_size", 0))
        with v2:
            st.metric("Voice confidence", customer_voice.get("confidence", "Low"))
        with v3:
            strongest = customer_voice["strengths"][0]["topic"] if customer_voice.get("strengths") else "—"
            st.metric("Strongest positive theme", strongest)

        topic_rows = []
        for row in customer_voice.get("topics", []):
            topic_rows.append({"Topic": row["topic"], "Mentions": row["mentions"], "Positive": row["positive"], "Negative": row["negative"], "Net sentiment": row["net_sentiment"]})
        if topic_rows:
            topic_df = pd.DataFrame(topic_rows)
            st.dataframe(topic_df, use_container_width=True, hide_index=True)
            st.markdown("#### Topic occurrence")
            st.bar_chart(topic_df.set_index("Topic")[["Mentions"]])

        voice_left, voice_right = st.columns(2)
        with voice_left:
            st.markdown("#### What customers visibly praise")
            if customer_voice.get("strengths"):
                for item in customer_voice["strengths"]:
                    st.success(f"**{item['topic']}** — {item['mentions']} observed mentions")
            else:
                st.write("No clear positive topic signal in the observable sample.")
        with voice_right:
            st.markdown("#### What deserves investigation")
            if customer_voice.get("concerns"):
                for item in customer_voice["concerns"]:
                    st.warning(f"**{item['topic']}** — {item['mentions']} observed mentions")
            else:
                st.write("No clear negative topic signal in the observable sample.")

        with st.expander("Review evidence"):
            for result in customer_voice.get("evidence", [])[:15]:
                st.markdown(f"**{result.get('title', '')}**")
                st.write(result.get("snippet", ""))
                if result.get("url"):
                    st.markdown(result["url"])
                st.divider()

    with tabs[3]:
        st.subheader("Marketing Traction & Content Intelligence")
        st.caption("Only observable public signals are shown. No spend, ROAS or booking impact is inferred.")
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.metric("Instagram followers", fmt_num(instagram_metrics.get("followers")))
        with m2:
            st.metric("Instagram posts", fmt_num(instagram_metrics.get("posts")))
        with m3:
            st.metric("Content sample", content_summary.get("sample_size", 0))
        with m4:
            lift = content_summary.get("creator_lift")
            st.metric("Creator visible lift", f"{lift:.1f}x" if lift is not None else "—")
        with m5:
            st.metric("Earned mentions", earned.get("count", 0))

        if instagram_metrics.get("bio"):
            st.markdown("#### Owned positioning")
            st.info(instagram_metrics["bio"])

        theme_rows = content_summary.get("themes", [])
        if theme_rows:
            st.markdown("#### Observable content themes")
            st.dataframe(pd.DataFrame(theme_rows), use_container_width=True, hide_index=True)

        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("#### Creator / UGC activity")
            st.metric("Creator/UGC items in sample", content_summary.get("creator_count", 0))
            st.metric("Owned items in sample", content_summary.get("owned_count", 0))
            if content_items:
                with st.expander("Content evidence"):
                    for item in content_items[:15]:
                        st.markdown(f"**{item['type']} · {item['theme']}**")
                        if item.get("engagement") is not None:
                            st.caption(f"Visible engagement: {item['engagement']:,}")
                        st.write(item.get("snippet", ""))
                        if item.get("url"):
                            st.markdown(item["url"])
                        st.divider()
        with c_right:
            st.markdown("#### Paid activity signal")
            if paid_signal["status"] == "Observable public signal found":
                st.success(paid_signal["status"])
            else:
                st.info(paid_signal["status"])
            st.caption(paid_signal["claim_limit"])

            st.markdown("#### Earned positioning")
            if earned.get("top_themes"):
                for theme, count in earned["top_themes"]:
                    st.write(f"**{theme}** · {count} observable mentions")
            else:
                st.write("No strong earned-positioning theme detected.")

        st.markdown("#### Search discovery snapshot")
        d1, d2 = st.columns(2)
        with d1:
            share = discovery.get("share_of_observed_mentions")
            st.metric("Share of observed cohort mentions", f"{share:.0%}" if share is not None else "—")
        with d2:
            st.metric("Target mentions", discovery.get("target_mentions", 0))

        discovery_rows = []
        for row in discovery.get("queries", []):
            discovery_rows.append({"Search": row["query"], restaurant: "Yes" if row["target_found"] else "No", "Competitors surfaced": ", ".join(row["competitors_found"]) or "—"})
        if discovery_rows:
            st.dataframe(pd.DataFrame(discovery_rows), use_container_width=True, hide_index=True)
        st.caption(discovery["methodology"])

    with tabs[4]:
        st.subheader("Dining Proposition")
        st.caption("How the restaurant is publicly priced, promoted and positioned across observable sources.")
        if benchmark_target:
            p1, p2, p3, p4 = st.columns(4)
            with p1:
                st.metric("Primary rating", f"{benchmark_target.get('rating'):.1f}" if benchmark_target.get("rating") else "—")
            with p2:
                st.metric("Cost for two", fmt_money(benchmark_target.get("cost_for_two")))
            with p3:
                st.metric("Top visible offer", benchmark_target["offers"][0] if benchmark_target.get("offers") else "—")
            with p4:
                st.metric("Price percentile", fmt_pct(competitive_metrics.get("price_percentile")))

            st.markdown("#### Observable positioning")
            tags = benchmark_target.get("positioning_tags", [])
            cuisines = benchmark_target.get("cuisines", [])
            if tags:
                st.write("**Experience / occasion:** " + " · ".join(tags))
            if cuisines:
                st.write("**Cuisine:** " + " · ".join(cuisines))
            if benchmark_target.get("offers"):
                st.write("**Visible offers:** " + " · ".join(benchmark_target["offers"]))

        st.markdown("#### Cross-platform dining signals")
        source_rows = []
        for source, summary in source_summaries.items():
            if summary:
                source_rows.append({"Source": source, "Rating": summary.get("rating"), "Ratings / Reviews": summary.get("review_count"), "Cost for Two": summary.get("cost_for_two"), "Top Offer": summary["offers"][0] if summary.get("offers") else None, "Confidence": summary.get("confidence")})
        if source_rows:
            st.dataframe(pd.DataFrame(source_rows), use_container_width=True, hide_index=True)

        st.markdown("#### Brand promise vs customer reality")
        positive_topics = [item["topic"] for item in customer_voice.get("strengths", [])]
        concern_topics = [item["topic"] for item in customer_voice.get("concerns", [])]
        if benchmark_target and benchmark_target.get("positioning_tags"):
            st.success("Public promise: " + ", ".join(benchmark_target["positioning_tags"][:5]))
        if positive_topics:
            st.success("Observable customer proof: " + ", ".join(positive_topics))
        if concern_topics:
            st.warning("Execution risks to validate: " + ", ".join(concern_topics))

    with tabs[5]:
        st.subheader("Consultant Workspace")
        st.caption("A conversation-ready briefing for the restaurant owner. Every statement stays within what public evidence can support.")
        w1, w2, w3 = st.columns(3)
        with w1:
            st.markdown("### ✅ What's working")
            for item in workspace.get("strengths", []):
                st.success(f"**{item['title']}**\n\n{item.get('observation', '')}")
        with w2:
            st.markdown("### ⚠️ Gaps to investigate")
            for item in workspace.get("gaps", []):
                st.warning(f"**{item['title']}**\n\n{item.get('observation', '')}")
        with w3:
            st.markdown("### 🚀 Opportunities")
            for item in workspace.get("opportunities", []):
                st.info(f"**{item['title']}**\n\n{item.get('recommendation', '')}")

        st.markdown("### Five owner questions that move the conversation forward")
        for index, question in enumerate(workspace.get("owner_questions", []), start=1):
            st.markdown(f"**{index}. {question}**")

        st.markdown("### Recommended 30-day consulting agenda")
        st.write(
            "1. Validate the top public customer-voice concern against internal feedback and on-ground audits.\n"
            "2. Lock the true competitive cohort and benchmark price, offer intensity and reputation weekly.\n"
            "3. Identify the strongest occasion/experience territory and align listing copy, owned content and creator briefs.\n"
            "4. Separate creator reach, paid activity and organic discovery into measurable booking-source hypotheses.\n"
            "5. Re-run this external snapshot monthly to track rating volume, offers, social presence and competitor movement."
        )

    with tabs[6]:
        st.subheader("Evidence & Confidence")
        st.caption("Use this tab when an owner challenges a claim. High-confidence values come from direct public pages; search snippets and web observations remain labelled.")
        profiles = [("District", data.get("district")), ("Swiggy Dineout", data.get("dineout")), ("Instagram", data.get("instagram")), ("Official Website", data.get("website"))]
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
        st.dataframe(pd.DataFrame(dining_metrics.get("direct_page_debug", [])), use_container_width=True, hide_index=True)

        with st.expander("Dining evidence by source"):
            for source, items in dining_metrics.get("by_source", {}).items():
                st.markdown(f"### {source}")
                for item in items:
                    st.markdown(f"**{item.get('title', '')}**")
                    st.caption(f"{item.get('extraction_method', 'search_snippet').replace('_', ' ').title()} · {item.get('confidence', 'Medium')} confidence")
                    if item.get("snippet"):
                        st.write(item["snippet"])
                    if item.get("url"):
                        st.markdown(item["url"])
                    st.divider()

        with st.expander("Public intelligence evidence"):
            st.markdown("### Earned media")
            for item in earned.get("evidence", []):
                st.markdown(f"**{item.get('title', '')}**")
                st.write(item.get("snippet", ""))
                if item.get("url"):
                    st.markdown(item["url"])
                st.divider()
            st.markdown("### Paid-signal evidence")
            for item in paid_signal.get("evidence", []):
                st.markdown(f"**{item.get('title', '')}**")
                st.write(item.get("snippet", ""))
                if item.get("url"):
                    st.markdown(item["url"])
                st.divider()

        with st.expander("Developer debug"):
            st.write("District candidates")
            st.json(debug_data.get("district_candidates", []))
            st.write("Competitor discovery")
            st.json(competitor_result)
            st.write("Instagram candidates")
            st.json(debug_data.get("instagram_candidates", []))
            st.write("Public intelligence errors")
            st.json(public_intel.get("errors", []))

    st.divider()
    st.caption("Claim boundary: This report describes observable public-market signals. It does not infer footfall, bookings, revenue, profitability, paid spend, ROAS or causal business impact without internal restaurant data.")
