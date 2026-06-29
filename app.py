import streamlit as st
import pandas as pd

from modules.countries import (
    COUNTRY_NAMES,
    get_country_code,
    get_default_language
)
from modules.marteso import MartesoClient

# --- Page Configuration ---
st.set_page_config(
    page_title="ASO Keyword Tool",
    page_icon="🍎",
    layout="wide"
)

# --- Session State Initialization ---
# This ensures results stay on screen even if the user edits the text area
if "results" not in st.session_state:
    st.session_state["results"] = []

st.title("🍎 ASO Keyword Research Tool")

# Initialize API Client
@st.cache_resource
def get_client():
    return MartesoClient()

client = get_client()

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    country_name = st.selectbox(
        "Country",
        COUNTRY_NAMES,
        index=COUNTRY_NAMES.index("🇺🇸 United States") if "🇺🇸 United States" in COUNTRY_NAMES else 0
    )
    
    country = get_country_code(country_name)
    language = st.text_input(
        "Language",
        value=get_default_language(country_name)
    )
    
    st.divider()
    
    # --- Tracking Limits UI ---
    st.subheader("Tracking Limits")
    
    # Fetch live counts using your MartesoClient
    try:
        total_tracked = client.tracked_count(country)
        remaining = client.remaining_slots(country)
        MAX_SLOTS = 50
        
        limit_color = "green" if remaining > 10 else ("orange" if remaining > 0 else "red")
        
        st.markdown(f"**Tracked ({country.upper()}):** {total_tracked} / {MAX_SLOTS}")
        st.markdown(f"**Remaining:** :{limit_color}[{remaining}]")
    except Exception as e:
        st.error(f"Failed to load limits: {e}")
        remaining = 0

    if st.button("Refresh Data", use_container_width=True):
        st.rerun()


# --- Main Area: Keyword Research ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Research")
    raw_keywords = st.text_area(
        "Enter one keyword per line",
        height=250,
        placeholder="habit tracker\nwater tracker\nfitness"
    )

    if st.button("Smart Analyze", type="primary", use_container_width=True):
        keyword_list = [k.strip().lower() for k in raw_keywords.splitlines() if k.strip()]
        
        if not keyword_list:
            st.warning("Please enter at least one keyword.")
            st.stop()
            
        # 1. Duplicate Detection
        new_keywords = []
        for kw in keyword_list:
            if client.keyword_exists(kw, country):
                continue
            if kw not in new_keywords: # Prevent duplicates within the text area itself
                new_keywords.append(kw)
                
        duplicates_count = len(keyword_list) - len(new_keywords)
        
        # 2. Smart Limits Enforcement
        to_analyze = new_keywords[:remaining]
        skipped_count = len(new_keywords) - len(to_analyze)
        
        # 3. User Feedback
        if duplicates_count > 0:
            st.info(f"Skipped {duplicates_count} keywords already tracked in {country.upper()}.")
        if skipped_count > 0:
            st.warning(f"Analyzed {len(to_analyze)} keywords. {skipped_count} skipped because no tracking slots remained.")
            
        # 4. Analysis Loop
        if to_analyze:
            progress = st.progress(0)
            status = st.empty()
            
            new_results = []
            for i, kw in enumerate(to_analyze):
                status.write(f"Checking **{kw}** ({i + 1}/{len(to_analyze)})...")
                try:
                    data = client.search_keyword(kw, country, language)
                    new_results.append(data)
                except Exception as e:
                    new_results.append({
                        "Keyword": kw,
                        "Popularity": None,
                        "Difficulty": None,
                        "Search Volume": None,
                        "Country": country,
                        "Language": language,
                        "Error": str(e)
                    })
                progress.progress((i + 1) / len(to_analyze))
                
            status.empty()
            progress.empty()
            
            # Save to session state
            st.session_state["results"].extend(new_results)
            st.success(f"Successfully analyzed {len(to_analyze)} keywords.")
            st.rerun()

with col2:
    st.subheader("Session Results")
    if st.session_state["results"]:
        df_results = pd.DataFrame(st.session_state["results"])
        
        # Display clean dataframe (hide errors/IDs if preferred, but keeping it flexible)
        st.dataframe(df_results, use_container_width=True, hide_index=True)
        
        if st.button("Clear Session Results"):
            st.session_state["results"] = []
            st.rerun()
    else:
        st.info("No keywords analyzed in this session yet.")

st.divider()

# --- Tracked Keyword Manager ---
st.header(f"Tracked Keywords Manager ({country.upper()})")

try:
    tracked_items = client.get_keywords_by_country(country)
except Exception as e:
    st.error("Could not fetch tracked keywords.")
    tracked_items = []

if tracked_items:
    # Format tracked items for display
    df_tracked = pd.DataFrame([{
        "ID": item["id"],
        "Keyword": item["term"],
        "Popularity": item.get("popularity"),
        "Difficulty": item.get("difficulty"),
        "Volume": item.get("searchVolume"),
        "Updated": item.get("updatedAt")
    } for item in tracked_items])
    
    st.dataframe(df_tracked, use_container_width=True, hide_index=True)
    
    del_col1, del_col2 = st.columns(2)
    
    with del_col1:
        keyword_to_delete = st.selectbox("Select Keyword to Delete", df_tracked["Keyword"].tolist())
        if st.button("Delete Selected"):
            target_id = df_tracked[df_tracked["Keyword"] == keyword_to_delete].iloc[0]["ID"]
            if client.delete_keyword(target_id):
                st.success(f"Deleted {keyword_to_delete}")
                st.rerun()
            else:
                st.error("Failed to delete keyword.")
                
    with del_col2:
        if st.button(f"Delete All in {country.upper()}", type="secondary"):
            with st.spinner("Deleting all keywords..."):
                client.delete_country_keywords(country)
            st.success("Bulk delete complete.")
            st.rerun()
else:
    st.info(f"No tracked keywords found for {country_name}.")
