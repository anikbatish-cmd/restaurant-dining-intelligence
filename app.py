import streamlit as st

st.set_page_config(
    page_title="Dining Intelligence",
    page_icon="🍽️",
    layout="wide"
)

st.title("🍽️ Dining Intelligence")

st.write(
    "Enter a restaurant to generate an external dining and marketing diagnostic."
)

restaurant = st.text_input(
    "Restaurant name",
    placeholder="e.g. Covah - The Cavern"
)

location = st.text_input(
    "Location",
    placeholder="e.g. Gurgaon"
)

if st.button("Generate Dining Report", type="primary"):

    if not restaurant or not location:
        st.warning("Please enter both restaurant name and location.")

    else:
        st.success(f"Analysing {restaurant}, {location}")

        st.subheader("Restaurant identified")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Price Index", "—")
        col2.metric("Rating Gap", "—")
        col3.metric("Popularity Index", "—")
        col4.metric("Google Rating Gap", "—")

        st.info(
            "Live restaurant data collection will be connected in the next version."
        )
