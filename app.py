import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Set UI Configuration
st.set_page_config(page_title="NYC Apartment Hunter", layout="wide")
st.title("🏙️ NYC Apartment Vetting Dashboard")

file_path = "daily_apartment_scan.xlsx"

if not os.path.exists(file_path):
    st.warning("⚠️ No data found. Run `python3 hunter.py` in your terminal to generate the data.")
else:
    df = pd.read_excel(file_path)
    
    # Left Sidebar Filters
    st.sidebar.header("🎯 Filter Results")
    
    # Safe Status Filter
    if "Vetting Status" in df.columns:
        all_statuses = df["Vetting Status"].dropna().unique()
        default_status = ["APPROVED"] if "APPROVED" in all_statuses else all_statuses
        status_filter = st.sidebar.multiselect("Vetting Status", options=all_statuses, default=default_status)
    else:
        status_filter = []

    # Safe Price Filter
    if "Price" in df.columns and not df.empty:
        min_price = int(df["Price"].min())
        max_price = int(df["Price"].max())
        selected_price = st.sidebar.slider("Max Price ($)", min_price, max_price, max_price)
        filtered_df = df[(df["Vetting Status"].isin(status_filter)) & (df["Price"] <= selected_price)].copy()
    else:
        filtered_df = df.copy()
    
    # STRUCTURAL SORT ENGINE: August Listings -> Immediate -> Others -> N/A
    def assign_sort_priority(date_val):
        d_str = str(date_val).strip().lower()
        if d_str.startswith("8/") and "2026" in d_str: return 0   
        if "immediate" in d_str or "now" in d_str: return 1      
        if d_str == "n/a" or d_str == "nan" or d_str == "none": return 3            
        return 2                                                 

    if not filtered_df.empty:
        if "Move-in Date" in filtered_df.columns:
            filtered_df["_sort_key"] = filtered_df["Move-in Date"].apply(assign_sort_priority)
            filtered_df = filtered_df.sort_values(by=["_sort_key", "Pipeline Score"], ascending=[True, False])
        elif "Pipeline Score" in filtered_df.columns:
            filtered_df = filtered_df.sort_values(by="Pipeline Score", ascending=False)
    
    # Top KPI Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Listings Scanned", len(df))
    col2.metric("Filtered Results", len(filtered_df))
    if "Pipeline Score" in filtered_df.columns and not filtered_df.empty:
        col3.metric("Avg Score (Filtered)", f"{filtered_df['Pipeline Score'].mean():.1f}")
    else:
        col3.metric("Avg Score (Filtered)", "0")
    
    # 🗺️ INTERACTIVE PLOTLY MAP HOVER SYSTEM (UPGRADED UI)
    if "Latitude" in filtered_df.columns and "Longitude" in filtered_df.columns:
        valid_coords = filtered_df[filtered_df["Latitude"].notna() & filtered_df["Longitude"].notna()]
        if not valid_coords.empty:
            st.subheader("🗺️ Interactive Property Map (Hover for Details)")
            
            hover_dict = {"Latitude": False, "Longitude": False}
            if "Price" in valid_coords.columns: hover_dict["Price"] = ":$%d"
            if "Pipeline Score" in valid_coords.columns: hover_dict["Pipeline Score"] = True
            if "Move-in Date" in valid_coords.columns: hover_dict["Move-in Date"] = True
            if "Commute to School" in valid_coords.columns: hover_dict["Commute to School"] = True

            fig = px.scatter_mapbox(
                valid_coords,
                lat="Latitude",
                lon="Longitude",
                hover_name="Address" if "Address" in valid_coords.columns else None,
                hover_data=hover_dict,
                zoom=12.2,
                height=450
            )
            
            # Make the dots BIG and bright neon cyan
            fig.update_traces(marker=dict(size=14, color="#00E5FF", opacity=0.85))

            # Change background to a sleek, minimalist dark map
            fig.update_layout(
                mapbox_style="carto-darkmatter",
                margin={"r":0, "t":0, "l":0, "b":0}
            )
            st.plotly_chart(fig, use_container_width=True)
        
    # Reorganize Columns for Table View
    ideal_columns = [
        "Address", "Price", "Move-in Date", "Days On Market", "Pipeline Score", "Risk Assessment Summary", 
        "Year Built", "Lease Term", "Utilities", "Features & Amenities",
        "Commute to Uncle", "Commute to School", 
        "Class A (Minor)", "Class B (Hazard)", "Class C (Emergency)", 
        "Total Open Violations", "Open HPD Complaints", "Active DOB Permits", "StreetEasy Link"
    ]
    
    display_columns = [col for col in ideal_columns if col in filtered_df.columns]
    
    st.subheader("📋 Vetted Pipeline Results")
    st.dataframe(
        filtered_df[display_columns],
        column_config={
            "StreetEasy Link": st.column_config.LinkColumn("Listing Link"),
            "Pipeline Score": st.column_config.ProgressColumn("Score", format="%d", min_value=0, max_value=100),
            "Price": st.column_config.NumberColumn("Price", format="$%d"),
            "Year Built": st.column_config.NumberColumn("Year Built", format="%d"),
            "Days On Market": st.column_config.NumberColumn("DOM", format="%d")
        },
        width="stretch",
        hide_index=True
    )
    
    st.sidebar.divider()
    st.sidebar.info("💡 Run `python3 hunter.py` in the terminal to pull new data, then click Refresh.")
    if st.sidebar.button("🔄 Refresh Latest Data"):
        st.rerun()