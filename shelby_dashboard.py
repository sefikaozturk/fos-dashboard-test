import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from io import StringIO
import re

# Page config
st.set_page_config(
    page_title="Friends of Shelby Dashboard",
    page_icon="🌲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define the actual sheet structure
SHEET_CONFIG = {
    "Overall Dashboard": {
        "gid": "433779691",
        "description": "Main dashboard metrics"
    },
    "Volunteer Participation Trends": {
        "gid": "650046450", 
        "description": "Time series volunteer data"
    },
    "Volunteer Satisfaction": {
        "gid": "1063103188",
        "description": "Volunteer satisfaction metrics"
    },
    "Most Popular Events": {
        "gid": "130383720",
        "description": "Event popularity data"
    },
    "Acres Cleaned Timeline": {
        "gid": "2145939805",
        "description": "Forest restoration timeline"
    },
    "Acres Cleaned Monthly": {
        "gid": "614540949",
        "description": "Monthly forest data"
    },
    "Barrier Ratings Over Time": {
        "gid": "385018677",
        "description": "Accessibility barriers timeline"
    },
    "Park Visits Data": {
        "gid": "840958021",
        "description": "Park visitation statistics"
    },
    "Park Accessibility Ratings": {
        "gid": "993445816",
        "description": "Accessibility ratings by organization"
    },
    "Survey Response Details": {
        "gid": "571418631",
        "description": "Survey response details"
    }
}

SPREADSHEET_ID = "1OgP1vp1OjiRgtisNrHoHxPIPbRxGjKtcegCS7ztVPr0"

# Function to fetch specific sheet data
@st.cache_data(ttl=300)
def fetch_sheet_data(sheet_name):
    """Fetch data from a specific named sheet"""
    if sheet_name not in SHEET_CONFIG:
        st.error(f"Sheet '{sheet_name}' not found in configuration")
        return None
    
    gid = SHEET_CONFIG[sheet_name]["gid"]
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={gid}"
    
    try:
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            # Try to parse the CSV
            df = pd.read_csv(StringIO(response.text))
            
            # Clean the dataframe
            df = df.dropna(how='all').dropna(axis=1, how='all')  # Remove empty rows/columns
            df.columns = df.columns.str.strip()  # Clean column names
            
            return df
        else:
            st.error(f"Failed to fetch {sheet_name}: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        st.error(f"Error fetching {sheet_name}: {str(e)}")
        return None

# Function to safely extract a single metric from a dataframe
def extract_single_metric(df, metric_name="value"):
    """Extract a single metric value from a dataframe"""
    if df is None or df.empty:
        return None
    
    # Strategy 1: Look for the metric in first row, first column with data
    for idx, row in df.iterrows():
        for col in df.columns:
            if pd.notna(row[col]):
                value = pd.to_numeric(row[col], errors='coerce')
                if pd.notna(value):
                    return value
    
    return None

# Function to extract time series data from specific sheets
def extract_time_series_data(df, date_column=None, value_columns=None):
    """Extract time series data with specific column mapping"""
    if df is None or df.empty:
        return None, None
    
    # Auto-detect date column if not specified
    if date_column is None:
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['date', 'month', 'time', 'period', 'year']):
                date_column = col
                break
    
    if date_column is None or date_column not in df.columns:
        return None, None
    
    # Get dates
    dates = df[date_column].dropna().tolist()
    
    # Get value columns
    if value_columns is None:
        value_columns = [col for col in df.columns if col != date_column]
    
    series_data = {}
    for col in value_columns:
        if col in df.columns:
            numeric_series = pd.to_numeric(df[col], errors='coerce')
            if not numeric_series.isna().all():
                series_data[col] = numeric_series.fillna(0).tolist()
    
    return dates, series_data

# Function to get all sheet data
@st.cache_data(ttl=300)
def fetch_all_sheets():
    """Fetch all sheet data"""
    all_data = {}
    data_status = {}
    
    for sheet_name in SHEET_CONFIG.keys():
        df = fetch_sheet_data(sheet_name)
        all_data[sheet_name] = df
        
        if df is not None:
            data_status[sheet_name] = {
                'status': 'success',
                'rows': len(df),
                'columns': len(df.columns),
                'columns_list': df.columns.tolist()
            }
        else:
            data_status[sheet_name] = {
                'status': 'failed',
                'rows': 0,
                'columns': 0,
                'columns_list': []
            }
    
    return all_data, data_status

# Custom CSS (same as before)
st.markdown("""
<style>
.main > div {
    padding-top: 2rem;
}
.metric-card, .metric-card-light {
    background: #4a4a4a;
    color: white;
    padding: 1rem 1.25rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    height: 100px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    text-align: left;
}
.metric-card-light {
    background: #f0f2f6;
    color: #333;
    border: 1px solid #e1e5e9;
}
.metric-card h4, .metric-card-light h4 {
    margin: 0 0 0.4rem 0;
    font-size: 0.8rem;
    font-weight: 500;
    line-height: 1.2;
    opacity: 0.9;
}
.metric-card h2, .metric-card-light h2 {
    margin: 0 0 0.2rem 0;
    font-size: 1.7rem;
    font-weight: 600;
    line-height: 1.1;
}
.metric-card small, .metric-card-light small {
    font-size: 0.72rem;
    opacity: 0.8;
    margin: 0;
    line-height: 1;
}
.chart-container {
    background: white;
    border-radius: 10px;
    padding: 1.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 2rem;
    border: 1px solid #e1e5e9;
}
</style>
""", unsafe_allow_html=True)

# Fetch all data
with st.spinner("Loading data from Google Sheets..."):
    all_data, data_status = fetch_all_sheets()

# Helper functions for formatting
def format_number(value, format_type="number"):
    """Format numbers for display"""
    if value is None or pd.isna(value):
        return "No Data"
    
    if format_type == "currency":
        return f"${value:,.2f}"
    elif format_type == "percentage":
        return f"{value:.1f}%"
    elif format_type == "decimal":
        return f"{value:.2f}"
    else:
        return f"{value:,.0f}" if value >= 1 else f"{value:.3f}"

# Sidebar Navigation
with st.sidebar:
    st.markdown("🌲 **Friends of Shelby**")
    st.markdown("### Navigation")
    
    volunteer_selected = st.button("Volunteer Program", key="nav1", use_container_width=True)
    forest_selected = st.button("Restore The Forest Program", key="nav2", use_container_width=True)
    strategic_selected = st.button("Strategic Plan - Pillar 1", key="nav3", use_container_width=True)
    
    st.markdown("### Data Status")
    
    success_count = sum(1 for status in data_status.values() if status['status'] == 'success')
    failed_count = len(data_status) - success_count
    
    if success_count > 0:
        st.success(f"✅ {success_count} sheets loaded successfully")
    if failed_count > 0:
        st.error(f"❌ {failed_count} sheets failed to load")
    
    if st.button("🔍 Show Data Details", use_container_width=True):
        st.write("**Sheet Status:**")
        for sheet_name, status in data_status.items():
            if status['status'] == 'success':
                st.success(f"✅ {sheet_name}: {status['rows']} rows, {status['columns']} cols")
                if status['columns_list']:
                    st.write(f"   Columns: {', '.join(status['columns_list'][:3])}{'...' if len(status['columns_list']) > 3 else ''}")
            else:
                st.error(f"❌ {sheet_name}: Failed to load")
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Determine which page to show
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Volunteer Program"

if volunteer_selected:
    st.session_state.current_page = "Volunteer Program"
elif forest_selected:
    st.session_state.current_page = "Restore The Forest Program"
elif strategic_selected:
    st.session_state.current_page = "Strategic Plan - Pillar 1"

page = st.session_state.current_page

# Page 1: Volunteer Program
if page == "Volunteer Program":
    col1, col2 = st.columns([6, 2])
    with col1:
        st.title("Friends of Shelby Dashboard")
        st.markdown("**Volunteer Program**")
    with col2:
        st.markdown("**Sefika Ozturk** - *Admin*")
    
    # Get metrics from Overall Dashboard sheet
    dashboard_data = all_data.get("Overall Dashboard")
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Extract total volunteers from dashboard data
        total_volunteers = "Loading..."
        if dashboard_data is not None:
            vol_value = extract_single_metric(dashboard_data)
            total_volunteers = format_number(vol_value)
        
        st.markdown(f"""
        <div style="background: #4a4a4a; color: white; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Total Volunteers</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{total_volunteers}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # You'll need to specify which column contains hours data
        total_hours = "Check Sheet"
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Total Hours</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{total_hours}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        value_hours = "Check Sheet"
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Value of Hours</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{value_hours}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        change_value = "Check Sheet"
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Change fr. Last Year</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{change_value}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        chart_container = st.container(border=True)
        with chart_container:
            st.subheader("Volunteer Participation Trends Over Time")
            
            # Get time series data from Volunteer Participation Trends sheet
            trends_data = all_data.get("Volunteer Participation Trends")
            
            if trends_data is not None and not trends_data.empty:
                dates, series_data = extract_time_series_data(trends_data)
                
                if dates and series_data:
                    fig = go.Figure()
                    colors = ['#333', '#666', '#999', '#ccc']
                    
                    for i, (series_name, values) in enumerate(series_data.items()):
                        fig.add_trace(go.Scatter(
                            x=dates[:len(values)], 
                            y=values[:len(dates)], 
                            name=series_name,
                            line=dict(color=colors[i % len(colors)])
                        ))
                    
                    fig.update_layout(
                        showlegend=True,
                        height=400,
                        xaxis_title="",
                        yaxis_title="",
                        plot_bgcolor='white',
                        paper_bgcolor='white'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("📊 Data loaded but no time series pattern detected. Please check date/numeric columns in the sheet.")
                    if trends_data is not None:
                        st.write("**Available columns:**", trends_data.columns.tolist())
            else:
                st.warning("⚠️ Volunteer Participation Trends sheet not available or empty")
    
    with col2:
        chart_container = st.container(border=True)
        with chart_container:
            st.subheader("Volunteer Satisfaction")
            
            satisfaction_data = all_data.get("Volunteer Satisfaction")
            if satisfaction_data is not None and not satisfaction_data.empty:
                st.write("**Data Preview:**")
                st.dataframe(satisfaction_data.head(5), use_container_width=True)
            else:
                st.warning("⚠️ Volunteer Satisfaction data not available")

# Page 2: Restore The Forest Program
elif page == "Restore The Forest Program":
    col1, col2 = st.columns([6, 2])
    with col1:
        st.title("Friends of Shelby Dashboard")
        st.markdown("**Restore The Forest Program**")
    with col2:
        st.markdown("**Renee McKelvey** - *Community Member*")
    
    # Top metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Get data from Acres Cleaned sheets
        acres_timeline = all_data.get("Acres Cleaned Timeline")
        acres_value = "Loading..."
        if acres_timeline is not None:
            val = extract_single_metric(acres_timeline)
            acres_value = format_number(val, "decimal")
        
        st.markdown(f"""
        <div style="background: #4a4a4a; color: white; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Acres Cleaned</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{acres_value}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        forest_percent = "Check Sheet"
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">% of Forest Reached</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{forest_percent}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        rtf_volunteers = "Check Sheet"
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">RTF Volunteers</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{rtf_volunteers}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts
    col1, col2 = st.columns([2, 1])
    
    with col1:
        chart_container = st.container(border=True)
        with chart_container:
            st.subheader("Acres Cleaned Over Time")
            
            acres_monthly = all_data.get("Acres Cleaned Monthly")
            if acres_monthly is not None and not acres_monthly.empty:
                dates, series_data = extract_time_series_data(acres_monthly)
                
                if dates and series_data:
                    fig = go.Figure()
                    colors = ['#2E7D32', '#388E3C', '#43A047', '#4CAF50']
                    
                    for i, (series_name, values) in enumerate(series_data.items()):
                        fig.add_trace(go.Scatter(
                            x=dates[:len(values)], 
                            y=values[:len(dates)], 
                            name=series_name,
                            line=dict(color=colors[i % len(colors)])
                        ))
                    
                    fig.update_layout(
                        showlegend=True,
                        height=400,
                        xaxis_title="",
                        yaxis_title="Acres",
                        plot_bgcolor='white',
                        paper_bgcolor='white'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("📊 Data loaded but no time series pattern detected.")
                    st.write("**Available columns:**", acres_monthly.columns.tolist())
            else:
                st.warning("⚠️ Acres Cleaned Monthly data not available")
    
    with col2:
        chart_container = st.container(border=True)
        with chart_container:
            st.subheader("Forest Data Summary")
            
            # Show data from both acres sheets
            if acres_timeline is not None:
                st.write("**Acres Timeline Data:**")
                st.dataframe(acres_timeline.head(5), use_container_width=True)
            
            if acres_monthly is not None:
                st.write("**Monthly Data:**")
                st.dataframe(acres_monthly.head(3), use_container_width=True)

# Page 3: Strategic Plan - Pillar 1  
else:
    col1, col2 = st.columns([6, 2])
    with col1:
        st.title("Friends of Shelby Dashboard")
        st.markdown("**Strategic Plan - Pillar 1**")
    with col2:
        st.markdown("**Sefika Ozturk** - *Admin*")
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Get data from survey sheets
    survey_data = all_data.get("Survey Response Details")
    
    with col1:
        survey_responses = "Loading..."
        if survey_data is not None:
            val = extract_single_metric(survey_data)
            survey_responses = format_number(val)
        
        st.markdown(f"""
        <div style="background: #4a4a4a; color: white; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Total Responses</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{survey_responses}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        barriers_percent = "Check Sheet"
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">% Facing Barriers</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{barriers_percent}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        accessibility_change = "Check Sheet"
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Accessibility</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{accessibility_change}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        park_visits_change = "Check Sheet"
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Park Visits</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{park_visits_change}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Main chart - Park Accessibility Ratings Over Time
    chart_container = st.container(border=True)
    with chart_container:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("Park Accessibility Ratings Over Time by Organization")
            
            accessibility_ratings = all_data.get("Park Accessibility Ratings")
            if accessibility_ratings is not None and not accessibility_ratings.empty:
                dates, series_data = extract_time_series_data(accessibility_ratings)
                
                if dates and series_data:
                    fig_acc = go.Figure()
                    colors = ['#333', '#666', '#999', '#ccc']
                    
                    for i, (org_name, org_values) in enumerate(series_data.items()):
                        fig_acc.add_trace(go.Scatter(
                            x=dates[:len(org_values)], 
                            y=org_values[:len(dates)], 
                            name=org_name,
                            line=dict(color=colors[i % len(colors)]),
                            marker=dict(size=8)
                        ))
                    
                    fig_acc.update_layout(
                        height=400,
                        showlegend=True,
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        yaxis=dict(range=[0, 100]),
                        yaxis_title="Accessibility Rating"
                    )
                    st.plotly_chart(fig_acc, use_container_width=True)
                else:
                    st.info("📊 Data loaded but no time series pattern detected.")
                    st.write("**Available columns:**", accessibility_ratings.columns.tolist())
        
        with col2:
            st.markdown("### Filters")
            col_q4, col_q5, col_q6 = st.columns(3)
            with col_q4:
                st.button("Q4", type="secondary", key="filter_q4")
            with col_q5:
                st.button("Q5", type="secondary", key="filter_q5") 
            with col_q6:
                st.button("Q6", type="primary", key="filter_q6")
            
            st.selectbox("Pick date", ["04/2025"], key="date_filter")
            st.selectbox("Pick organization", ["All Organizations"], key="org_filter")
            st.checkbox("Show multiple", value=True, key="multi_filter")
    
    # Bottom section - Survey Statements Horizontal Bar Chart
    chart_container = st.container(border=True)
    with chart_container:
        # Header row with title and toggle buttons
        col_title, spacer, col_buttons = st.columns([3, 1, 2])
        
        with col_title:
            st.subheader("Park Accessibility Statements")
        
        with col_buttons:
            col_q4b, col_q5b, col_q6b = st.columns(3)
            with col_q4b:
                st.button("Q4", type="secondary", key="stmt_q4")
            with col_q5b:  
                st.button("Q5", type="secondary", key="stmt_q5")
            with col_q6b:
                st.button("Q6", type="primary", key="stmt_q6")
        
        # Full-width chart using Google Sheets survey data
        statements = []
        percentages = []
        
        # Try to find survey statements data
        for sheet_name, df in all_data.items():
            if df is not None and not df.empty:
                # Look for statement/percentage columns
                statement_col = None
                percentage_col = None
                
                for col in df.columns:
                    col_lower = col.lower()
                    if any(keyword in col_lower for keyword in ['statement', 'question', 'survey', 'accessibility']):
                        statement_col = col
                    elif any(keyword in col_lower for keyword in ['percentage', 'percent', 'rate', 'response']):
                        percentage_col = col
                
                if statement_col and percentage_col:
                    # Extract data
                    for idx, row in df.iterrows():
                        if pd.notna(row[statement_col]) and pd.notna(row[percentage_col]):
                            statement = str(row[statement_col]).strip()
                            percentage = pd.to_numeric(row[percentage_col], errors='coerce')
                            if pd.notna(percentage) and statement:
                                statements.append(statement)
                                percentages.append(percentage)
                    break
        
        if statements and percentages:
            fig_horiz = go.Figure()
            fig_horiz.add_trace(go.Bar(
                y=statements,
                x=percentages,
                orientation='h',
                marker_color='#333'
            ))
            
            fig_horiz.update_layout(
                height=500,
                xaxis_title="Response Rate (%)",
                yaxis_title="",
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=300, r=50, t=50, b=50),
                xaxis=dict(range=[0, 100])
            )
            st.plotly_chart(fig_horiz, use_container_width=True)
        else:
            st.warning("⚠️ Survey statements data not available from Google Sheets")
            
            # Fallback to show expected format
            st.info("Expected data format: Statement column and Percentage column in survey_data sheet")
