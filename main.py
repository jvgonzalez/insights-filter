import streamlit as st
import pandas as pd
import base64
from datetime import datetime

# Set page config
st.set_page_config(page_title="Insights Filter", page_icon="🎫", layout="wide")

# Title
st.title("🎫 Insights Filter (Updated)")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file is not None:
    # Read CSV file
    df = pd.read_csv(uploaded_file)
    
    # Process the data
    def process_data(df):
        # Convert date columns to datetime
        date_columns = ['Event Date', 'On Sale Date']
        for col in date_columns:
            df[col] = pd.to_datetime(df[col])
        
        # Calculate days until event
        df['Days Until Event'] = (df['Event Date'] - datetime.now()).dt.days
        
        # Calculate percentage difference
        df['Percentage Difference'] = ((df['TM Price'] - df['SH Price']) / df['SH Price']) * 100
        
        # Format percentage difference
        df['Percentage Difference'] = df['Percentage Difference'].apply(lambda x: f"{x:.2f}%")
        
        # Create Has Stubhub column
        df['Has Stubhub'] = df['SH Price'].apply(lambda x: 'Yes' if pd.notnull(x) else 'No')
        
        return df

    # Process the data
    df_processed = process_data(df)
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Event name search
    event_name_search = st.sidebar.text_input("Search event name")
    
    # Percentage difference range
    if 'Percentage Difference' in df_processed.columns:
        st.sidebar.subheader("Percentage Difference Filter")
        col1, col2, col3 = st.sidebar.columns([2, 1, 1])
        with col1:
            percentage_diff_range = st.slider(
                "Range",
                min_value=0.0,
                max_value=1000.0,
                value=(0.0, 1000.0),
                step=0.1
            )
        with col2:
            min_percentage = st.number_input("Min %", min_value=0.0, max_value=1000.0, value=percentage_diff_range[0], step=0.1)
        with col3:
            max_percentage = st.number_input("Max %", min_value=0.0, max_value=1000.0, value=percentage_diff_range[1], step=0.1)

        # Update slider when number inputs change
        if min_percentage != percentage_diff_range[0] or max_percentage != percentage_diff_range[1]:
            percentage_diff_range = (min_percentage, max_percentage)
    
    # Monitoring filter
    if 'monitoring' in df_processed.columns:
        unique_monitoring_values = df_processed['monitoring'].unique().tolist()
        monitoring_filter = st.sidebar.selectbox("Filter by Monitoring", ["All"] + unique_monitoring_values)
    
    # Has Stubhub filter
    has_stubhub_filter = st.sidebar.selectbox("Filter by Has Stubhub", ["All", "Yes", "No"])
    
    # OOS Zones filter
    st.sidebar.markdown("### Filter by OOS Zones")
    oos_zones_search = st.sidebar.text_input("Search OOS Zones", key="oos_zones_search")
    
    # Updated slider for OOS Zones amount
    min_oos_zones = 0
    max_oos_zones = 30
    oos_zones_range = st.sidebar.slider('Number of OOS Zones', min_value=min_oos_zones, max_value=max_oos_zones, value=(min_oos_zones, max_oos_zones))
    
    if 'OOSZones' in df_processed.columns:
        unique_oos_zones = sorted(set(zone.strip() for zones in df_processed['OOSZones'].dropna() for zone in str(zones).split(',')))
        filtered_oos_zones = [zone for zone in unique_oos_zones if oos_zones_search.lower() in zone.lower()]
        selected_oos_zones = st.sidebar.multiselect('Select OOS Zones', filtered_oos_zones, key='oos_zones_multiselect')
    
    # Apply filters
    df_filtered = df_processed.copy()
    
    if event_name_search:
        df_filtered = df_filtered[df_filtered['Event Name'].str.contains(event_name_search, case=False)]
    
    if 'Percentage Difference' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['Percentage Difference'].apply(lambda x: float(x.strip('%')) >= percentage_diff_range[0] and float(x.strip('%')) <= percentage_diff_range[1])]
    
    if monitoring_filter != "All":
        df_filtered = df_filtered[df_filtered['monitoring'] == monitoring_filter]
    
    if has_stubhub_filter != "All":
        df_filtered = df_filtered[df_filtered['Has Stubhub'] == has_stubhub_filter]
    
    if selected_oos_zones:
        df_filtered = df_filtered[df_filtered['OOSZones'].apply(lambda x: any(zone in str(x) for zone in selected_oos_zones))]
    
    df_filtered = df_filtered[df_filtered['OOSZones'].apply(lambda x: oos_zones_range[0] <= len(str(x).split(',')) <= oos_zones_range[1])]
    
    # Display filtered data
    st.write(f"Showing {len(df_filtered)} events")
    st.dataframe(df_filtered)
    
    # Download CSV button
    def get_csv_download_link(df):
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="filtered_data.csv">Download CSV file</a>'
        return href

    st.markdown(get_csv_download_link(df_filtered), unsafe_allow_html=True)

else:
    st.info("Please upload a CSV file to begin the analysis.")

# Footer
st.markdown("---")
st.markdown("Created with ❤️ using Streamlit")
