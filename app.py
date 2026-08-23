import streamlit as st

from search_engine import resolve_restaurant
from collectors import (
    enrich_dining_metrics_with_pages,
    extract_dining_metrics,
    extract_instagram_metrics,
    summarize_source_results,
)


st.set_page_config(
    page_title="Dining Intelligence",
    page_icon="🍽️",
    layout="wide",
)

st.title("🍽️ Dining Intelligence")
st.caption(
    "Public dining, competitive and marketing intelligence "
    "for restaurant consultants."
)

with st.form("restaurant_search"):
    col1, col2 = st.columns(2)

    with col1:
        restaurant = st.text_input(
            "Restaurant",
            placeholder="Covah - The Cavern",
        )

    with col2:
        location = st.text_input(
            "Location",
            placeholder="Gurgaon",
        )

    submitted = st.form_submit_button(
        "Generate Dining Report",
        type="primary",
    )


if submitted:
    if not restaurant or not location:
        st.warning("Please enter both restaurant name and location.")

    else:
        with st.status(
            "Building restaurant intelligence...",
            expanded=True,
        ) as status:
            st.write("Searching for restaurant...")

            data = resolve_restaurant(
                restaurant,
                location,
            )

            st.write("Identifying public dining platforms...")

            debug_data = data.get("debug", {})
            all_dining_candidates = (
                debug_data.get("zomato_candidates", [])
                + debug_data.get("dineout_candidates", [])
                + debug_data.get("metric_candidates", [])
            )

            dining_metrics = extract_dining_metrics(
                primary_result=data.get("zomato"),
                supporting_results=all_dining_candidates,
            )

            st.write("Checking public restaurant pages for richer metrics...")

            direct_urls = []

            if data.get("zomato") and data["zomato"].get("url"):
                direct_urls.append(data["zomato"]["url"])

            if data.get("dineout") and data["dineout"].get("url"):
                direct_urls.append(data["dineout"]["url"])

            for candidate in all_dining_candidates:
                candidate_url = candidate.get("url", "")
                lower_url = candidate_url.lower()

                if "district.in/dining/" in lower_url:
                    direct_urls.append(candidate_url)
                    break

            dining_metrics = enrich_dining_metrics_with_pages(
                dining_metrics,
                direct_urls,
            )

            instagram_metrics = extract_instagram_metrics(
                data.get("instagram")
            )

            st.write("Structuring verified dining and marketing signals...")

            status.update(
                label="Restaurant intelligence ready",
                state="complete",
            )

        st.divider()
        st.header(restaurant)
        st.caption(location)

        st.subheader("Public profiles identified")
        profile_columns = st.columns(4)

        profiles = [
            ("Zomato / District", data.get("zomato")),
            ("Swiggy Dineout", data.get("dineout")),
            ("Instagram", data.get("instagram")),
            ("Official Website", data.get("website")),
        ]

        for col, (name, result) in zip(profile_columns, profiles):
            with col:
                st.markdown(f"### {name}")

                if result:
                    st.success("Found")
                    st.write(result.get("title", ""))

                    if result.get("url"):
                        st.link_button("Open source", result["url"])
                else:
                    st.warning("Not confidently identified")

        # --------------------------------------------------
        # VERIFIED DINING SNAPSHOT
        # --------------------------------------------------

        st.divider()
        st.subheader("Verified Dining Snapshot")
        st.caption(
            "High-confidence public-page values are prioritised. "
            "Platform differences are shown rather than averaged away."
        )

        primary_sources = [
            "Zomato",
            "District",
            "Swiggy Dineout",
        ]

        comparison_rows = []

        for source in primary_sources:
            summary = summarize_source_results(
                dining_metrics.get("by_source", {}).get(source, [])
            )

            if not summary:
                continue

            comparison_rows.append(
                {
                    "Platform": source,
                    "Rating": summary["rating"],
                    "Ratings / Reviews": summary["review_count"],
                    "Cost for Two": summary["cost_for_two"],
                    "Top Visible Offer": summary["offers"][0]
                    if summary["offers"]
                    else None,
                    "Confidence": summary["confidence"],
                }
            )

        if comparison_rows:
            st.dataframe(
                comparison_rows,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Rating": st.column_config.NumberColumn(
                        format="%.1f"
                    ),
                    "Ratings / Reviews": st.column_config.NumberColumn(
                        format="%d"
                    ),
                    "Cost for Two": st.column_config.NumberColumn(
                        format="₹%d"
                    ),
                },
            )
        else:
            st.warning(
                "No high-confidence primary dining metrics were available."
            )

        # --------------------------------------------------
        # PRIMARY SOURCE DETAIL
        # --------------------------------------------------

        st.subheader("Platform Detail")

        for source in primary_sources:
            source_results = dining_metrics.get("by_source", {}).get(source, [])
            summary = summarize_source_results(source_results)

            if not summary:
                continue

            st.markdown(f"### {source}")

            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

            with metric_col1:
                st.metric(
                    "Rating",
                    f"{summary['rating']:.1f}"
                    if summary["rating"] is not None
                    else "—",
                )

            with metric_col2:
                st.metric(
                    "Ratings / Reviews",
                    f"{summary['review_count']:,}"
                    if summary["review_count"] is not None
                    else "—",
                )

            with metric_col3:
                st.metric(
                    "Cost for Two",
                    f"₹{summary['cost_for_two']:,}"
                    if summary["cost_for_two"] is not None
                    else "—",
                )

            with metric_col4:
                st.metric(
                    "Visible Offer",
                    summary["offers"][0]
                    if summary["offers"]
                    else "—",
                )

            method_label = summary["method"].replace("_", " ").title()
            st.caption(
                f"Method: {method_label} · Confidence: {summary['confidence']}"
            )

            if summary["cuisines"]:
                st.write(
                    "**Cuisine signals:** "
                    + ", ".join(summary["cuisines"])
                )

            with st.expander(f"View {source} evidence"):
                for item in source_results:
                    method = item.get("extraction_method", "search_snippet")
                    confidence = item.get("confidence", "Medium")

                    st.markdown(f"**{item['title']}**")
                    st.caption(
                        f"Method: {method.replace('_', ' ').title()} · "
                        f"Confidence: {confidence}"
                    )

                    if item.get("snippet"):
                        st.write(item["snippet"])

                    if item.get("url"):
                        st.markdown(item["url"])

                    st.divider()

        # --------------------------------------------------
        # SECONDARY PUBLIC SIGNALS
        # --------------------------------------------------

        with st.expander("Secondary public dining signals"):
            for source in ["EazyDiner", "Justdial", "Web"]:
                source_results = dining_metrics.get("by_source", {}).get(source, [])
                summary = summarize_source_results(source_results)

                if not summary:
                    continue

                st.markdown(f"### {source}")

                signal_parts = []

                if summary["rating"] is not None:
                    signal_parts.append(f"Rating {summary['rating']:.1f}")

                if summary["review_count"] is not None:
                    signal_parts.append(
                        f"{summary['review_count']:,} ratings/reviews"
                    )

                if summary["cost_for_two"] is not None:
                    signal_parts.append(
                        f"₹{summary['cost_for_two']:,} for two"
                    )

                if summary["offers"]:
                    signal_parts.append(summary["offers"][0])

                if summary["cuisines"]:
                    signal_parts.append(
                        ", ".join(summary["cuisines"])
                    )

                st.write(
                    " · ".join(signal_parts)
                    if signal_parts
                    else "No structured metric extracted."
                )

                st.caption(
                    "Secondary signal only — not used as the primary platform benchmark."
                )

        # --------------------------------------------------
        # MARKETING TRACTION
        # --------------------------------------------------

        st.divider()
        st.subheader("Marketing Traction")
        st.markdown("### Instagram Presence")

        social_col1, social_col2, social_col3, social_col4 = st.columns(4)

        followers = instagram_metrics["followers"]
        posts = instagram_metrics["posts"]
        following = instagram_metrics["following"]
        handle = instagram_metrics["handle"]

        with social_col1:
            st.metric(
                "Followers",
                f"{followers:,}" if followers is not None else "—",
            )

        with social_col2:
            st.metric(
                "Posts",
                f"{posts:,}" if posts is not None else "—",
            )

        with social_col3:
            st.metric(
                "Following",
                f"{following:,}" if following is not None else "—",
            )

        with social_col4:
            st.metric(
                "Instagram Handle",
                f"@{handle}" if handle else "—",
            )

        if instagram_metrics["bio"]:
            st.write("**Public profile signal:**")
            st.write(instagram_metrics["bio"])

        if instagram_metrics["url"]:
            st.link_button(
                "Open Instagram",
                instagram_metrics["url"],
            )

        # --------------------------------------------------
        # SEARCH EVIDENCE / DEBUG
        # --------------------------------------------------

        st.divider()
        st.subheader("Evidence & Debug")

        with st.expander("View public search evidence"):
            general_results = data.get("general_results", [])

            if not general_results:
                st.write("No general search results found.")
            else:
                for result in general_results:
                    st.markdown(f"**{result.get('title', '')}**")

                    if result.get("snippet"):
                        st.write(result["snippet"])

                    if result.get("url"):
                        st.markdown(result["url"])

                    st.divider()

        with st.expander("Developer debug"):
            st.write("Direct page extraction attempts")
            st.json(dining_metrics.get("direct_page_debug", []))

            st.write("Extracted Instagram metrics")
            st.json(instagram_metrics)

            st.write("Dining metrics by source")
            st.json(dining_metrics.get("by_source", {}))

            st.write("Targeted dining metric candidates")
            st.json(debug_data.get("metric_candidates", []))

            st.write("Dining metric search errors")
            st.json(debug_data.get("metric_errors", []))

        st.info(
            "Primary restaurant extraction is now usable. Next: build the "
            "competitive cohort, benchmark price/rating/reputation, and "
            "generate consultant-grade diagnostic insights."
        )
