import streamlit as st
import pandas as pd
import base64
from datetime import datetime

# Set page config
st.set_page_config(page_title="Insights Filter", page_icon="🎫", layout="wide")

# Title
st.title("🎫 Insights Filter")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file is not None:
    # Read CSV file
    df = pd.read_csv(uploaded_file)
    print(f"Number of rows in original dataframe: {len(df)}")
    print(f"Column names: {df.columns.tolist()}")
    print(f"CSV loaded. Columns: {df.columns.tolist()}")
    print(f"DateTime column type after loading: {df['DateTime'].dtype}")
    
    # Process the data
    def process_data(df):
        print(f"Processing data. Initial row count: {len(df)}")
        
        # Check DateTime column before processing
        print(f"DateTime column type before processing: {df['DateTime'].dtype}")
        print(f"Sample DateTime values: {df['DateTime'].head()}")
        
        # Convert Price to numeric, handling price ranges
        def extract_lowest_price(price):
            if isinstance(price, str) and '-' in price:
                return float(price.split('-')[0].replace('$', '').strip())
            return pd.to_numeric(price.replace('$', '').replace(',', ''), errors='coerce') if isinstance(price, str) else price

        if 'Price' in df.columns:
            df['Price'] = df['Price'].apply(extract_lowest_price)
        if 'LowestStubHubPrice' in df.columns:
            df['LowestStubHubPrice'] = pd.to_numeric(df['LowestStubHubPrice'], errors='coerce')
        
        # Calculate Percentage Difference
        if 'Price' in df.columns and 'LowestStubHubPrice' in df.columns:
            df['Percentage Difference'] = ((df['LowestStubHubPrice'] - df['Price']) / df['Price']) * 100
        
        # Add 'Has Stubhub' column
        df['Has Stubhub'] = df['LowestStubHubPrice'].notna().map({True: 'Yes', False: 'No'})
        
        # Convert DateTime and calculate Days Until Event
        try:
            df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
            print(f"DateTime conversion successful. New dtype: {df['DateTime'].dtype}")
        except Exception as e:
            print(f"Error converting DateTime: {e}")
            print("Keeping DateTime as string")
            df['DateTime'] = df['DateTime'].astype(str)

        current_date = pd.Timestamp.now().date()
        df['Days Until Event'] = df['DateTime'].apply(lambda x: (pd.to_datetime(x, errors='coerce').date() - current_date).days if pd.notna(x) else None)
        
        # Add more debug information
        print(f"DateTime column dtype: {df['DateTime'].dtype}")
        print(f"Days Until Event column dtype: {df['Days Until Event'].dtype}")
        print(f"Sample Days Until Event values: {df['Days Until Event'].head()}")
        print(f"Number of events with valid Days Until Event: {df['Days Until Event'].notna().sum()}")
        
        # Select and reorder columns
        columns = ['ID', 'Name', 'DateTime', 'Location', 'Days Until Event']
        if 'Price' in df.columns:
            columns.append('Price')
        if 'LowestStubHubPrice' in df.columns:
            columns.append('LowestStubHubPrice')
        if 'Percentage Difference' in df.columns:
            columns.append('Percentage Difference')
        if 'OOSZones' in df.columns:
            columns.append('OOSZones')
        if 'monitoring' in df.columns:
            columns.append('monitoring')
        columns.append('Has Stubhub')
        df_processed = df[columns]
        
        print(f"Data processing complete. Final row count: {len(df_processed)}")
        print(f"Processed column names: {df_processed.columns.tolist()}")
        print(f"Column data types: {df_processed.dtypes}")
        return df_processed

    # Process the data
    df_processed = process_data(df)
    print(f"Number of rows after processing: {len(df_processed)}")
    
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
    if 'OOSZones' in df_processed.columns:
        st.sidebar.markdown("### Filter by OOS Zones")
        oos_zones_search = st.sidebar.text_input("Search OOS Zones", key="oos_zones_search")
        unique_oos_zones = sorted(set(zone.strip() for zones in df_processed['OOSZones'].dropna() for zone in str(zones).split(',')))
        filtered_oos_zones = [zone for zone in unique_oos_zones if oos_zones_search.lower() in zone.lower()]
        selected_oos_zones = st.sidebar.multiselect('Select OOS Zones', filtered_oos_zones, key='oos_zones_multiselect')
    
    # Filter by Days Until Event
    if 'Days Until Event' in df_processed.columns:
        st.sidebar.subheader("Filter by Days Until Event")
        use_days_until_event_filter = st.sidebar.checkbox("Use Days Until Event filter", value=False)
        days_until_event_filter = st.sidebar.number_input("Show events within +/- days", min_value=0, value=30)
        show_past_events = st.sidebar.checkbox("Show past events", value=False)
    
    # Apply filters
    df_filtered = df_processed.copy()
    print(f"Number of rows before filtering: {len(df_filtered)}")
    
    if 'Percentage Difference' in df_processed.columns and (percentage_diff_range[0] > 0 or percentage_diff_range[1] < 1000):
        df_filtered = df_filtered[
            (df_filtered['Percentage Difference'] >= percentage_diff_range[0]) &
            (df_filtered['Percentage Difference'] <= percentage_diff_range[1])
        ]
    print(f"Number of rows after percentage difference filter: {len(df_filtered)}")
    
    if event_name_search:
        df_filtered = df_filtered[df_filtered['Name'].str.contains(event_name_search, case=False, na=False)]
    print(f"Number of rows after event name search: {len(df_filtered)}")
    
    if 'monitoring' in df_processed.columns and monitoring_filter != "All":
        df_filtered = df_filtered[df_filtered['monitoring'] == monitoring_filter]
    print(f"Number of rows after monitoring filter: {len(df_filtered)}")
    
    if has_stubhub_filter != "All":
        df_filtered = df_filtered[df_filtered['Has Stubhub'] == has_stubhub_filter]
    print(f"Number of rows after Has Stubhub filter: {len(df_filtered)}")
    
    if selected_oos_zones:
        df_filtered = df_filtered[df_filtered['OOSZones'].apply(lambda x: any(zone.lower() in str(x).lower() for zone in selected_oos_zones))]
    print(f"Number of rows after OOS Zones filter: {len(df_filtered)}")
    
    if 'Days Until Event' in df_processed.columns and use_days_until_event_filter:
        print(f"Number of rows before Days Until Event filter: {len(df_filtered)}")
        if not show_past_events:
            df_filtered = df_filtered[df_filtered['Days Until Event'].ge(0) | df_filtered['Days Until Event'].isna()]
        df_filtered = df_filtered[
            df_filtered['Days Until Event'].isna() |
            (df_filtered['Days Until Event'].abs() <= days_until_event_filter)
        ]
        print(f"Number of rows after Days Until Event filter: {len(df_filtered)}")
    else:
        print("Days Until Event filter not applied")
    
    print(f"Days Until Event filter status: {'Applied' if use_days_until_event_filter else 'Not Applied'}")
    print(f"Show past events: {show_past_events}")
    print(f"Days until event filter value: {days_until_event_filter}")
    
    print(f"Final number of rows after all filters: {len(df_filtered)}")
    
    # Verification function
    def verify_filters():
        issues = []
        if 'monitoring' not in df.columns:
            issues.append("Monitoring column is missing")
        if 'OOSZones' not in df.columns:
            issues.append("OOS Zones column is missing")
        return issues

    # Call the function and display warnings
    filter_issues = verify_filters()
    for issue in filter_issues:
        st.warning(issue)
    
    # Display processed data with interactive table
    st.subheader("Processed Data")
    
    # Display total number of events
    st.metric("Total Events Displayed", len(df_filtered))
    
    # Sorting functionality
    sort_column = st.selectbox("Sort by", df_filtered.columns)
    sort_order = st.radio("Sort order", ("Ascending", "Descending"))
    df_filtered = df_filtered.sort_values(by=sort_column, ascending=(sort_order == "Ascending"))
    
    # Display interactive table
    st.dataframe(
        data=df_filtered,
        use_container_width=True,
        hide_index=True,
        height=800,  # Increased height to accommodate more rows
        column_config={
            "ID": st.column_config.TextColumn("ID", width="small"),
            "Name": st.column_config.TextColumn("Event Name", width="medium"),
            "DateTime": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
            "Location": st.column_config.TextColumn("Location", width="small"),
            "Days Until Event": st.column_config.NumberColumn("Days Until Event", width="small"),
            "Price": st.column_config.NumberColumn("Original Price", format="$%.2f"),
            "LowestStubHubPrice": st.column_config.NumberColumn("StubHub Price", format="$%.2f"),
            "Percentage Difference": st.column_config.NumberColumn("% Difference", format="%.2f%%"),
            "OOSZones": st.column_config.TextColumn("OOS Zones", width="medium"),
            "monitoring": st.column_config.TextColumn("Monitoring", width="small"),
            "Has Stubhub": st.column_config.TextColumn("Has StubHub", width="small")
        }
    )
    
    # Export filtered data
    if st.button("Export Filtered IDs"):
        csv = df_filtered['ID'].to_csv(index=False).encode()
        b64 = base64.b64encode(csv).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="filtered_ids.csv">Download Filtered IDs</a>'
        st.markdown(href, unsafe_allow_html=True)
    
    # Import Event IDs for highlighting
    uploaded_ids = st.file_uploader("Upload Event IDs for highlighting", type="txt")
    if uploaded_ids is not None:
        highlighted_ids = set(uploaded_ids.getvalue().decode().splitlines())
        df_filtered['Highlighted'] = df_filtered['ID'].isin(highlighted_ids)
        
        # Filter options for highlighted events
        highlight_filter = st.radio("Show events:", ("All", "Highlighted", "Non-Highlighted"))
        if highlight_filter == "Highlighted":
            df_filtered = df_filtered[df_filtered['Highlighted']]
        elif highlight_filter == "Non-Highlighted":
            df_filtered = df_filtered[~df_filtered['Highlighted']]
        
        # Display updated table with highlighting
        st.dataframe(
            data=df_filtered,
            use_container_width=True,
            hide_index=True,
            height=800,  # Increased height to accommodate more rows
            column_config={
                "ID": st.column_config.TextColumn("ID", width="small"),
                "Name": st.column_config.TextColumn("Event Name", width="medium"),
                "DateTime": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "Location": st.column_config.TextColumn("Location", width="small"),
                "Days Until Event": st.column_config.NumberColumn("Days Until Event", width="small"),
                "Price": st.column_config.NumberColumn("Original Price", format="$%.2f"),
                "LowestStubHubPrice": st.column_config.NumberColumn("StubHub Price", format="$%.2f"),
                "Percentage Difference": st.column_config.NumberColumn("% Difference", format="%.2f%%"),
                "OOSZones": st.column_config.TextColumn("OOS Zones", width="medium"),
                "monitoring": st.column_config.TextColumn("Monitoring", width="small"),
                "Has Stubhub": st.column_config.TextColumn("Has StubHub", width="small")
            }
        )
        
        # Update total number of events after highlighting
        st.metric("Total Events Displayed", len(df_filtered))

else:
    st.info("Please upload a CSV file to begin the analysis.")

# Footer
st.markdown("---")
st.markdown("Created with ❤️ using Streamlit")
