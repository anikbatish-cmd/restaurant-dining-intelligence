import streamlit as st

from search_engine import resolve_restaurant
from collectors import extract_dining_metrics, extract_instagram_metrics


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

            all_dining_candidates = (
                data.get("debug", {}).get("zomato_candidates", [])
                + data.get("debug", {}).get("dineout_candidates", [])
                + data.get("debug", {}).get("metric_candidates", [])
            )

            dining_metrics = extract_dining_metrics(
                primary_result=data.get("zomato"),
                supporting_results=all_dining_candidates,
            )

            instagram_metrics = extract_instagram_metrics(
                data.get("instagram")
            )

            st.write("Extracting public dining and marketing signals...")

            status.update(
                label="Restaurant discovery complete",
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

        st.divider()
        st.subheader("Dining Platform Snapshot")
        st.caption(
            "Metrics are kept separate by source so values "
            "from different platforms are not mixed together."
        )

        source_priority = [
            "Zomato",
            "District",
            "Swiggy Dineout",
            "EazyDiner",
            "Justdial",
            "Web",
        ]

        any_source_found = False

        for source in source_priority:
            source_results = dining_metrics["by_source"].get(source, [])

            if not source_results:
                continue

            any_source_found = True
            st.markdown(f"### {source}")

            rating = None
            reviews = None
            price = None
            offers = []
            cuisines = []

            for item in source_results:
                if rating is None and item["rating"] is not None:
                    rating = item["rating"]

                if reviews is None and item["review_count"] is not None:
                    reviews = item["review_count"]

                if price is None and item["cost_for_two"] is not None:
                    price = item["cost_for_two"]

                for offer in item["offers"]:
                    if offer not in offers:
                        offers.append(offer)

                for cuisine in item["cuisines"]:
                    if cuisine not in cuisines:
                        cuisines.append(cuisine)

            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

            with metric_col1:
                st.metric(
                    "Rating",
                    f"{rating:.1f}" if rating is not None else "—",
                )

            with metric_col2:
                st.metric(
                    "Ratings / Reviews",
                    f"{reviews:,}" if reviews is not None else "—",
                )

            with metric_col3:
                st.metric(
                    "Cost for Two",
                    f"₹{price:,}" if price is not None else "—",
                )

            with metric_col4:
                st.metric(
                    "Visible Offer",
                    offers[0] if offers else "—",
                )

            if cuisines:
                st.write("**Cuisine signals:** " + ", ".join(cuisines))

            with st.expander(f"View {source} evidence"):
                for item in source_results:
                    st.markdown(f"**{item['title']}**")

                    if item["snippet"]:
                        st.write(item["snippet"])

                    if item["url"]:
                        st.markdown(item["url"])

                    st.divider()

        if not any_source_found:
            st.warning(
                "No structured dining metrics could be extracted "
                "from the public search results."
            )

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

        st.divider()
        st.subheader("Search evidence")

        with st.expander(
            "View public results used to identify restaurant"
        ):
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
            st.write("Zomato candidates")
            st.json(
                data.get("debug", {}).get("zomato_candidates", [])
            )

            st.write("Targeted dining metric candidates")
            st.json(
                data.get("debug", {}).get("metric_candidates", [])
            )

            st.write("Dining metric search errors")
            st.json(
                data.get("debug", {}).get("metric_errors", [])
            )

            st.write("Dineout candidates")
            st.json(
                data.get("debug", {}).get("dineout_candidates", [])
            )

            st.write("Instagram candidates")
            st.json(
                data.get("debug", {}).get("instagram_candidates", [])
            )

            st.write("Extracted Instagram metrics")
            st.json(instagram_metrics)

            st.write("Dining metrics by source")
            st.json(dining_metrics["by_source"])

        st.info(
            "Restaurant discovery, source-aware dining extraction and "
            "Instagram traction extraction are active. Next: validate "
            "targeted metric extraction, then build direct competitor "
            "identification and competitive benchmarking."
        )
