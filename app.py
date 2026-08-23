import streamlit as st

from search_engine import resolve_restaurant
from collectors import extract_dining_metrics


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Dining Intelligence",
    page_icon="🍽️",
    layout="wide",
)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("🍽️ Dining Intelligence")

st.caption(
    "Public dining, competitive and marketing intelligence "
    "for restaurant consultants."
)


# --------------------------------------------------
# SEARCH FORM
# --------------------------------------------------

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


# --------------------------------------------------
# REPORT
# --------------------------------------------------

if submitted:

    if not restaurant or not location:

        st.warning(
            "Please enter both restaurant name and location."
        )

    else:

        # ------------------------------------------
        # DISCOVERY
        # ------------------------------------------

        with st.status(
            "Building restaurant intelligence...",
            expanded=True,
        ) as status:

            st.write(
                "Searching for restaurant..."
            )

            data = resolve_restaurant(
                restaurant,
                location,
            )

            st.write(
                "Identifying public dining platforms..."
            )

            dining_metrics = extract_dining_metrics(
                primary_result=data["zomato"],
                supporting_results=data["debug"][
                    "zomato_candidates"
                ],
            )

            st.write(
                "Extracting public dining signals..."
            )

            status.update(
                label="Restaurant discovery complete",
                state="complete",
            )


        # ------------------------------------------
        # RESTAURANT HEADER
        # ------------------------------------------

        st.divider()

        st.header(restaurant)

        st.caption(location)


        # ------------------------------------------
        # PUBLIC PROFILES
        # ------------------------------------------

        st.subheader(
            "Public profiles identified"
        )

        profile_columns = st.columns(4)

        profiles = [
            (
                "Zomato / District",
                data["zomato"],
            ),
            (
                "Swiggy Dineout",
                data["dineout"],
            ),
            (
                "Instagram",
                data["instagram"],
            ),
            (
                "Official Website",
                data["website"],
            ),
        ]

        for col, (name, result) in zip(
            profile_columns,
            profiles,
        ):

            with col:

                st.markdown(
                    f"### {name}"
                )

                if result:

                    st.success(
                        "Found"
                    )

                    st.write(
                        result.get(
                            "title",
                            "",
                        )
                    )

                    if result.get("url"):

                        st.link_button(
                            "Open source",
                            result["url"],
                        )

                else:

                    st.warning(
                        "Not confidently identified"
                    )


        # ------------------------------------------
        # DINING PLATFORM SNAPSHOT
        # ------------------------------------------

        st.divider()

        st.subheader(
            "Dining Platform Snapshot"
        )

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

            source_results = dining_metrics[
                "by_source"
            ].get(
                source,
                [],
            )

            if not source_results:
                continue

            any_source_found = True

            st.markdown(
                f"### {source}"
            )

            rating = None
            reviews = None
            price = None
            offers = []
            cuisines = []

            for item in source_results:

                if (
                    rating is None
                    and item["rating"] is not None
                ):
                    rating = item["rating"]

                if (
                    reviews is None
                    and item["review_count"] is not None
                ):
                    reviews = item[
                        "review_count"
                    ]

                if (
                    price is None
                    and item["cost_for_two"] is not None
                ):
                    price = item[
                        "cost_for_two"
                    ]

                for offer in item["offers"]:

                    if offer not in offers:
                        offers.append(
                            offer
                        )

                for cuisine in item["cuisines"]:

                    if cuisine not in cuisines:
                        cuisines.append(
                            cuisine
                        )


            # --------------------------------------
            # SOURCE METRICS
            # --------------------------------------

            col1, col2, col3, col4 = (
                st.columns(4)
            )

            with col1:

                st.metric(
                    "Rating",
                    f"{rating:.1f}"
                    if rating is not None
                    else "—",
                )


            with col2:

                st.metric(
                    "Ratings / Reviews",
                    f"{reviews:,}"
                    if reviews is not None
                    else "—",
                )


            with col3:

                st.metric(
                    "Cost for Two",
                    f"₹{price:,}"
                    if price is not None
                    else "—",
                )


            with col4:

                st.metric(
                    "Visible Offer",
                    offers[0]
                    if offers
                    else "—",
                )


            # --------------------------------------
            # CUISINE SIGNALS
            # --------------------------------------

            if cuisines:

                st.write(
                    "**Cuisine signals:** "
                    + ", ".join(
                        cuisines
                    )
                )


            # --------------------------------------
            # SOURCE EVIDENCE
            # --------------------------------------

            with st.expander(
                f"View {source} evidence"
            ):

                for item in source_results:

                    st.markdown(
                        f"**{item['title']}**"
                    )

                    if item["snippet"]:

                        st.write(
                            item["snippet"]
                        )

                    if item["url"]:

                        st.markdown(
                            item["url"]
                        )

                    st.divider()


        if not any_source_found:

            st.warning(
                "No structured dining metrics "
                "could be extracted from the "
                "public search results."
            )


        # ------------------------------------------
        # SEARCH EVIDENCE
        # ------------------------------------------

        st.divider()

        st.subheader(
            "Search evidence"
        )

        with st.expander(
            "View public results used "
            "to identify restaurant"
        ):

            general_results = data.get(
                "general_results",
                [],
            )

            if not general_results:

                st.write(
                    "No general search results found."
                )

            else:

                for result in general_results:

                    st.markdown(
                        f"**{result.get('title', '')}**"
                    )

                    if result.get(
                        "snippet"
                    ):

                        st.write(
                            result["snippet"]
                        )

                    if result.get(
                        "url"
                    ):

                        st.markdown(
                            result["url"]
                        )

                    st.divider()


        # ------------------------------------------
        # DEVELOPER DEBUG
        # ------------------------------------------

        with st.expander(
            "Developer debug"
        ):

            st.write(
                "Zomato candidates"
            )

            st.json(
                data["debug"].get(
                    "zomato_candidates",
                    [],
                )
            )

            st.write(
                "Zomato search errors"
            )

            st.json(
                data["debug"].get(
                    "zomato_errors",
                    [],
                )
            )

            st.write(
                "Dineout candidates"
            )

            st.json(
                data["debug"].get(
                    "dineout_candidates",
                    [],
                )
            )

            st.write(
                "Instagram candidates"
            )

            st.json(
                data["debug"].get(
                    "instagram_candidates",
                    [],
                )
            )


        # ------------------------------------------
        # CURRENT BUILD STATUS
        # ------------------------------------------

        st.info(
            "Restaurant discovery and source-aware dining "
            "metric extraction are active. "
            "Next: direct platform extraction, competitor "
            "identification and competitive benchmarking."
        )
