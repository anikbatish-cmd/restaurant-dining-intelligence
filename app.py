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

            st.write("Identifying District and public dining sources...")

            debug_data = data.get("debug", {})
            all_dining_candidates = (
                debug_data.get("district_candidates", [])
                + debug_data.get("dineout_candidates", [])
                + debug_data.get("metric_candidates", [])
            )

            dining_metrics = extract_dining_metrics(
                primary_result=data.get("district"),
                supporting_results=all_dining_candidates,
            )

            st.write("Checking public restaurant pages for richer metrics...")

            direct_urls = []

            if data.get("district") and data["district"].get("url"):
                direct_urls.append(data["district"]["url"])

            if data.get("dineout") and data["dineout"].get("url"):
                direct_urls.append(data["dineout"]["url"])

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

        # --------------------------------------------------
        # PUBLIC PROFILES
        # --------------------------------------------------

        st.subheader("Public profiles identified")
        profile_columns = st.columns(4)

        profiles = [
            ("District", data.get("district")),
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
        # DISTRICT PRIMARY SNAPSHOT
        # --------------------------------------------------

        st.divider()
        st.subheader("District Dining Snapshot")
        st.caption(
            "District is the primary dining benchmark for the report. "
            "Swiggy Dineout and other public sources are retained only as supporting signals."
        )

        district_summary = summarize_source_results(
            dining_metrics.get("by_source", {}).get("District", [])
        )

        if district_summary:
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

            with metric_col1:
                st.metric(
                    "District Rating",
                    f"{district_summary['rating']:.1f}"
                    if district_summary["rating"] is not None
                    else "—",
                )

            with metric_col2:
                st.metric(
                    "District Ratings / Reviews",
                    f"{district_summary['review_count']:,}"
                    if district_summary["review_count"] is not None
                    else "—",
                )

            with metric_col3:
                st.metric(
                    "District Cost for Two",
                    f"₹{district_summary['cost_for_two']:,}"
                    if district_summary["cost_for_two"] is not None
                    else "—",
                )

            with metric_col4:
                st.metric(
                    "Top Visible District Offer",
                    district_summary["offers"][0]
                    if district_summary["offers"]
                    else "—",
                )

            method_label = district_summary["method"].replace("_", " ").title()
            st.caption(
                f"Method: {method_label} · Confidence: {district_summary['confidence']}"
            )

            if district_summary["cuisines"]:
                st.write(
                    "**District cuisine signals:** "
                    + ", ".join(district_summary["cuisines"])
                )

            if district_summary["offers"]:
                st.write(
                    "**Visible District offers:** "
                    + " · ".join(district_summary["offers"])
                )

            with st.expander("View District evidence"):
                for item in dining_metrics.get("by_source", {}).get("District", []):
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

        else:
            st.warning(
                "District was identified, but no structured District dining metrics "
                "could be extracted for this restaurant."
            )

        # --------------------------------------------------
        # SUPPORTING DINING SIGNALS
        # --------------------------------------------------

        st.subheader("Supporting Dining Signals")
        st.caption(
            "These sources provide context and cross-checks. They are not used "
            "as the primary dining benchmark."
        )

        supporting_sources = [
            "Swiggy Dineout",
            "EazyDiner",
            "Justdial",
            "Web",
        ]

        for source in supporting_sources:
            source_results = dining_metrics.get("by_source", {}).get(source, [])
            summary = summarize_source_results(source_results)

            if not summary:
                continue

            with st.expander(source):
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
                    f"Confidence: {summary['confidence']} · Supporting signal only"
                )

                for item in source_results:
                    if item.get("url"):
                        st.markdown(item["url"])

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
            st.write("District candidates")
            st.json(debug_data.get("district_candidates", []))

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
            "District is now the primary dining data source. Next: build the "
            "competitive cohort using District metrics, benchmark price/rating/" 
            "reputation, and generate consultant-grade diagnostic insights."
        )
