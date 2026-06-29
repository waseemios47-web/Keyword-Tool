import streamlit as st

st.set_page_config(
    page_title="ASO Keyword Tool",
    page_icon="🍎",
    layout="wide"
)

st.title("🍎 ASO Keyword Research Tool")

st.sidebar.header("Settings")

country = st.sidebar.selectbox(
    "Country",
    [
        "United States",
        "United Kingdom",
        "Canada",
        "Australia"
    ]
)

language = st.sidebar.selectbox(
    "Language",
    [
        "English"
    ]
)

st.subheader("Keywords")

keywords = st.text_area(
    "Enter one keyword per line",
    height=250,
    placeholder="""habit tracker
water tracker
calorie counter
fitness"""
)

if st.button("Analyze Keywords", use_container_width=True):

    kws = [
        k.strip()
        for k in keywords.splitlines()
        if k.strip()
    ]

    st.success(f"{len(kws)} keywords ready for analysis.")

    st.write(kws)
