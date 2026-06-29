import streamlit as st
import pandas as pd

from modules.countries import (
    COUNTRY_NAMES,
    get_country_code,
    get_default_language
)

from modules.marteso import MartesoClient


# -------------------------------------------------

st.set_page_config(
    page_title="ASO Keyword Tool",
    page_icon="🍎",
    layout="wide"
)

st.title("🍎 ASO Keyword Research Tool")

# -------------------------------------------------

client = MartesoClient()

# -------------------------------------------------

st.sidebar.header("Settings")

country_name = st.sidebar.selectbox(
    "Country",
    COUNTRY_NAMES,
    index=COUNTRY_NAMES.index("🇺🇸 United States")
)

country = get_country_code(country_name)

language = st.sidebar.text_input(
    "Language",
    value=get_default_language(country_name)
)

# -------------------------------------------------

keywords = st.text_area(
    "Enter one keyword per line",
    height=250,
    placeholder="""
habit tracker
water tracker
fitness
calorie counter
"""
)

# -------------------------------------------------

if st.button("Analyze Keywords", use_container_width=True):

    keyword_list = [
        k.strip()
        for k in keywords.splitlines()
        if k.strip()
    ]

    if not keyword_list:
        st.warning("Please enter at least one keyword.")
        st.stop()

    results = []

    progress = st.progress(0)

    status = st.empty()

    for i, keyword in enumerate(keyword_list):

        status.write(f"Checking **{keyword}**...")

        try:

            data = client.search_keyword(
                keyword,
                country,
                language
            )

            results.append(data)

        except Exception as e:

            results.append({

                "Keyword": keyword,

                "Popularity": None,

                "Difficulty": None,

                "Search Volume": None,

                "Country": country,

                "Language": language,

                "Error": str(e)

            })

        progress.progress((i + 1) / len(keyword_list))

    status.empty()

    df = pd.DataFrame(results)

    st.success(f"{len(df)} keywords analyzed.")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
