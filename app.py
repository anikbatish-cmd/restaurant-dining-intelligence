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

        cols = st.columns(4)

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
            cols,
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

                    st.link_button(
                        "Open source",
                        result["url"],
                    )

                else:

                    st.warning(
                        "Not confidently identified"
                    )


        # ------------------------------------------
        # DINING SNAPSHOT
        # ------------------------------------------

        st.divider()

        st.subheader(
            "Dining Snapshot"
        )

        col1, col2, col3, col4 = (
            st.columns(4)
        )


        # RATING

        with col1:

            rating = dining_metrics[
                "rating"
            ]

            st.metric(
                "Dining Rating",
                f"{rating:.1f}"
                if rating is not None
                else "—",
            )


        # REVIEW COUNT

        with col2:

            reviews = dining_metrics[
                "review_count"
            ]

            st.metric(
                "Public Review / Rating Count",
                f"{reviews:,}"
                if reviews is not None
                else "—",
            )


        # COST FOR TWO

        with col3:

            price = dining_metrics[
                "cost_for_two"
            ]

            st.metric(
                "Cost for Two",
                f"₹{price:,}"
                if price is not None
                else "—",
            )


        # OFFER

        with col4:

            offers = dining_metrics[
                "offers"
            ]

            st.metric(
                "Visible Offer",
                offers[0]
                if offers
                else "—",
            )


        # ------------------------------------------
        # CUISINE SIGNALS
        # ------------------------------------------

        if dining_metrics["cuisines"]:

            st.write(
                "**Cuisine signals:** "
                + ", ".join(
                    dining_metrics[
                        "cuisines"
                    ]
                )
            )


        # ------------------------------------------
        # DINING EVIDENCE
        # ------------------------------------------

        with st.expander(
            "View evidence behind dining snapshot"
        ):

            for item in dining_metrics[
                "evidence"
            ]:

                st.markdown(
                    f"**{item['title']}**"
                )

                st.write(
                    item["snippet"]
                )

                if item["url"]:

                    st.markdown(
                        item["url"]
                    )

                st.divider()


        # ------------------------------------------
        # SEARCH EVIDENCE
        # ------------------------------------------

        st.divider()

        st.subheader(
            "Search evidence"
        )

        with st.expander(
            "View public results used to identify restaurant"
        ):

            for result in data[
                "general_results"
            ]:

                st.markdown(
                    f"**{result['title']}**"
                )

                st.write(
                    result["snippet"]
                )

                if result["url"]:

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
                data["debug"][
                    "zomato_candidates"
                ]
            )

            st.write(
                "Search errors"
            )

            st.json(
                data["debug"][
                    "zomato_errors"
                ]
            )


        # ------------------------------------------
        # CURRENT BUILD STATUS
        # ------------------------------------------

        st.info(
            "Dining metric extraction is active. "
            "Next: automatically identify and benchmark "
            "the competitive cohort."
        )
