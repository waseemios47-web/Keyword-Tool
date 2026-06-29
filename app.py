import streamlit as st
import pandas as pd
import time

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
if "results" not in st.session_state:
    st.session_state["results"] = []

# Initialize API Client
@st.cache_resource
def get_client():
    return MartesoClient()

client = get_client()

# --- Sidebar Configuration ---
with st.sidebar:
    st.title("🍎 ASO Tool")
    st.divider()
    
    st.header("⚙️ Settings")
    
    country_name = st.selectbox(
        "Country",
        COUNTRY_NAMES,
        index=COUNTRY_NAMES.index("🇺🇸 United States") if "🇺🇸 United States" in COUNTRY_NAMES else 0
    )
    
    country = get_country_code(country_name)
    language = st.text_input("Language", value=get_default_language(country_name))
    
    st.divider()
    
    # --- Tracking Limits UI ---
    st.subheader("Tracking Limits")
    
    try:
        global_tracked = client.tracked_count(country=None) 
        country_tracked = client.tracked_count(country=country)
        
        MAX_SLOTS = 50
        remaining = max(0, MAX_SLOTS - global_tracked)
        
        limit_color = "green" if remaining > 10 else ("orange" if remaining > 0 else "red")
        
        st.markdown(f"**Total Tracked (All Countries):** {global_tracked} / {MAX_SLOTS}")
        st.markdown(f"**Tracked in {country.upper()}:** {country_tracked}")
        st.markdown(f"**Remaining Slots:** :{limit_color}[{remaining}]")
    except Exception as e:
        st.error(f"Failed to load limits.")
        remaining = 0
        global_tracked = 0

    if st.button("Refresh Data", use_container_width=True):
        st.rerun()

# --- Main Layout: Clean Tabs ---
tab1, tab2 = st.tabs(["🔍 Keyword Research", "📂 Tracked Manager"])

# ==========================================
# TAB 1: RESEARCH & SESSION RESULTS
# ==========================================
with tab1:
    col_input, col_results = st.columns([1, 2], gap="large")
    
    with col_input:
        st.markdown("### Input")
        raw_keywords = st.text_area(
            "Enter one keyword per line",
            height=200,
            placeholder="habit tracker\nwater tracker\nfitness",
            label_visibility="collapsed"
        )

        if st.button("Smart Analyze", type="primary", use_container_width=True):
            keyword_list = [k.strip().lower() for k in raw_keywords.splitlines() if k.strip()]
            
            if not keyword_list:
                st.warning("Please enter at least one keyword.")
                st.stop()
                
            # Duplicate Detection
            new_keywords = []
            for kw in keyword_list:
                if client.keyword_exists(kw, country):
                    continue
                if kw not in new_keywords: 
                    new_keywords.append(kw)
                    
            duplicates_count = len(keyword_list) - len(new_keywords)
            
            # Limits Enforcement
            to_analyze = new_keywords[:remaining]
            skipped_count = len(new_keywords) - len(to_analyze)
            
            # Feedback
            if duplicates_count > 0:
                st.info(f"Skipped {duplicates_count} keyword(s) already tracked in {country.upper()}.")
            if skipped_count > 0:
                st.warning(f"Analyzed {len(to_analyze)} keywords. {skipped_count} skipped (no slots left).")
                
            # Analysis Loop
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
                            "Keyword": kw, "Popularity": None, "Difficulty": None, 
                            "Search Volume": None, "Country": country, "Language": language, "Error": str(e)
                        })
                    progress.progress((i + 1) / len(to_analyze))
                
                # Wait 3 seconds for Marteso backend to fetch data from Apple
                status.write("Fetching final metrics from Apple...")
                time.sleep(3) 
                
                fresh_tracked_items = client.get_keywords_by_country(country)
                
                # Update our session results with the real data
                for res in new_results:
                    if res.get("Popularity") is None or res.get("Popularity") == "Pending...":
                        match = next((item for item in fresh_tracked_items if item["term"] == res["Keyword"]), None)
                        if match:
                            res["Popularity"] = match.get("popularity")
                            res["Difficulty"] = match.get("difficulty")
                            res["Search Volume"] = match.get("searchVolume")
                    
                status.empty()
                progress.empty()
                
                st.session_state["results"].extend(new_results)
                st.rerun()

    with col_results:
        # FIXED: Removed the dynamic country code from this header so it doesn't cause confusion
        st.markdown("### Session Results") 
        if st.session_state["results"]:
            df_results = pd.DataFrame(st.session_state["results"])
            
            # Clean up metadata columns but KEEP Country and Language as requested in the spec
            cols_to_drop = ["ID", "Updated", "Error"]
            for col in cols_to_drop:
                if col in df_results.columns:
                    df_results = df_results.drop(columns=[col])
            
            # Ensure proper column order for readability
            all_cols = df_results.columns.tolist()
            preferred_order = ["Keyword", "Popularity", "Difficulty", "Search Volume", "Country", "Language"]
            ordered_cols = [c for c in preferred_order if c in all_cols] + [c for c in all_cols if c not in preferred_order]
            df_results = df_results[ordered_cols]
                
            # Replace any lingering None values
            df_results = df_results.fillna("Pending...")
            
            # Standard upper-case transform for country codes to keep it beautiful
            if "Country" in df_results.columns:
                df_results["Country"] = df_results["Country"].astype(str).str.upper()
            
            st.dataframe(df_results, use_container_width=True, hide_index=True)
            
            if st.button("Clear Session Results"):
                st.session_state["results"] = []
                st.rerun()
        else:
            st.info("No keywords analyzed yet. Enter keywords on the left.")

# ==========================================
# TAB 2: TRACKED KEYWORD MANAGER
# ==========================================
with tab2:
    st.markdown(f"### Tracked Keywords in {country.upper()}")
    
    try:
        tracked_items = client.get_keywords_by_country(country)
    except Exception as e:
        st.error("Could not fetch tracked keywords.")
        tracked_items = []

    if tracked_items:
        df_tracked = pd.DataFrame([{
            "ID": item["id"],
            "Keyword": item["term"],
            "Popularity": item.get("popularity"),
            "Difficulty": item.get("difficulty"),
            "Volume": item.get("searchVolume")
        } for item in tracked_items])
        
        # Display clean dataframe without ID column
        df_display = df_tracked.drop(columns=["ID"]).fillna("Pending...")
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        st.divider()
        st.markdown("#### Manage Keywords")
        
        del_col1, del_col2 = st.columns(2)
        with del_col1:
            keyword_to_delete = st.selectbox("Select Keyword to Delete", df_tracked["Keyword"].tolist(), label_visibility="collapsed")
            if st.button("Delete Selected", type="primary"):
                target_id = df_tracked[df_tracked["Keyword"] == keyword_to_delete].iloc[0]["ID"]
                if client.delete_keyword(target_id):
                    st.toast(f"Deleted {keyword_to_delete}")
                    st.rerun()
                    
        with del_col2:
            if st.button(f"Delete All {len(tracked_items)} Keywords in {country.upper()}", type="secondary"):
                with st.spinner("Deleting all keywords..."):
                    client.delete_country_keywords(country)
                st.toast("Bulk delete complete.")
                st.rerun()
    else:
        st.info(f"You have no tracked keywords in {country_name}.")
