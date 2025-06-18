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

# Function to discover available sheets
@st.cache_data(ttl=300)
def discover_sheets(spreadsheet_id):
    """Discover all available sheets in the spreadsheet"""
    sheets_info = {}
    
    # Try common GID values and the main sheet
    potential_gids = [0, 1, 2, 3, 433779691, 1234567890, 2147483647]
    
    for gid in potential_gids:
        try:
            url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200 and len(response.text.strip()) > 0:
                # Try to parse as CSV to validate
                try:
                    df = pd.read_csv(StringIO(response.text))
                    # Only consider it valid if it has actual data
                    if not df.empty and not df.isna().all().all():
                        sheets_info[f"sheet_{gid}"] = {
                            'gid': gid,
                            'url': url,
                            'rows': len(df),
                            'columns': len(df.columns),
                            'sample_data': df.head(3).to_dict('records') if not df.empty else []
                        }
                except:
                    continue
        except:
            continue
    
    return sheets_info

# Function to fetch and analyze sheet data
@st.cache_data(ttl=300)
def fetch_sheet_data(spreadsheet_id, gid):
    """Fetch data from a specific sheet"""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))
            
            # Clean the dataframe
            df = df.dropna(how='all').dropna(axis=1, how='all')  # Remove empty rows/columns
            df.columns = df.columns.str.strip()  # Clean column names
            
            return df
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching sheet {gid}: {str(e)}")
        return None

# Function to intelligently extract metrics from any dataframe
def extract_metrics_from_df(df, sheet_name=""):
    """Extract metrics from a dataframe using multiple strategies"""
    metrics = {}
    
    if df is None or df.empty:
        return metrics
    
    # Strategy 1: Look for key-value pairs
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['metric', 'key', 'name', 'label']):
            value_col = None
            # Find corresponding value column
            for val_col in df.columns:
                if val_col != col and any(keyword in val_col.lower() for keyword in ['value', 'amount', 'number', 'total', 'count']):
                    value_col = val_col
                    break
            
            if value_col:
                for idx, row in df.iterrows():
                    if pd.notna(row[col]) and pd.notna(row[value_col]):
                        key = str(row[col]).lower().replace(' ', '_').replace('%', 'percent')
                        value = pd.to_numeric(row[value_col], errors='coerce')
                        if pd.notna(value):
                            metrics[f"{sheet_name}_{key}"] = value
    
    # Strategy 2: Look for cells with ":" pattern (like "Total Volunteers: 891")
    for col in df.columns:
        for idx, cell_value in df[col].items():
            if pd.notna(cell_value):
                str_val = str(cell_value).strip()
                if ':' in str_val:
                    parts = str_val.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip().lower().replace(' ', '_').replace('%', 'percent')
                        value = pd.to_numeric(parts[1].strip(), errors='coerce')
                        if pd.notna(value):
                            metrics[f"{sheet_name}_{key}"] = value
    
    # Strategy 3: Column headers as metrics (first row as values)
    for col in df.columns:
        if col.strip():
            # Get first non-null numeric value
            col_values = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(col_values) > 0:
                key = col.lower().replace(' ', '_').replace('%', 'percent')
                metrics[f"{sheet_name}_{key}"] = col_values.iloc[0]
    
    # Strategy 4: Look for summary rows (rows with "total", "sum", etc.)
    for idx, row in df.iterrows():
        for col in df.columns:
            if pd.notna(row[col]):
                str_val = str(row[col]).lower()
                if any(keyword in str_val for keyword in ['total', 'sum', 'count', 'average', 'mean']):
                    # This row might contain summary data
                    for other_col in df.columns:
                        if other_col != col:
                            value = pd.to_numeric(row[other_col], errors='coerce')
                            if pd.notna(value):
                                key = f"{other_col.lower().replace(' ', '_')}_{str_val.replace(' ', '_')}"
                                metrics[f"{sheet_name}_{key}"] = value
    
    return metrics

# Function to extract time series data
def extract_time_series(df, sheet_name=""):
    """Extract time series data from dataframe"""
    if df is None or df.empty:
        return None, None
    
    # Find date/time column
    date_col = None
    for col in df.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in ['date', 'month', 'time', 'period', 'year']):
            date_col = col
            break
    
    if date_col is None:
        return None, None
    
    # Get date values
    dates = df[date_col].dropna().tolist()
    
    # Get numeric columns as series
    series_data = {}
    for col in df.columns:
        if col != date_col:
            numeric_series = pd.to_numeric(df[col], errors='coerce')
            if not numeric_series.isna().all() and numeric_series.sum() != 0:
                series_data[col] = numeric_series.fillna(0).tolist()
    
    return dates, series_data

# Main data fetching function
@st.cache_data(ttl=300)
def fetch_all_data():
    """Fetch all data from Google Sheets"""
    spreadsheet_id = "1OgP1vp1OjiRgtisNrHoHxPIPbRxGjKtcegCS7ztVPr0"
    
    # First discover available sheets
    sheets_info = discover_sheets(spreadsheet_id)
    
    if not sheets_info:
        st.error("No accessible sheets found in the spreadsheet")
        return None, None, None
    
    # Fetch data from all discovered sheets
    all_data = {}
    all_metrics = {}
    
    for sheet_name, info in sheets_info.items():
        df = fetch_sheet_data(spreadsheet_id, info['gid'])
        if df is not None:
            all_data[sheet_name] = df
            # Extract metrics from this sheet
            sheet_metrics = extract_metrics_from_df(df, sheet_name)
            all_metrics.update(sheet_metrics)
    
    return sheets_info, all_data, all_metrics

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
with st.spinner("Discovering and loading data from Google Sheets..."):
    sheets_info, all_data, all_metrics = fetch_all_data()

if sheets_info is None:
    st.error("❌ Cannot load dashboard - No data available from Google Sheets")
    st.stop()

# Helper function to safely get metric value
def get_metric_value(metrics, possible_keys, format_type="number", default="No Data"):
    """Try multiple possible keys to find a metric value"""
    for key in possible_keys:
        # Try exact match first
        if key in metrics:
            value = metrics[key]
            if pd.notna(value):
                return format_value(value, format_type)
        
        # Try partial matches
        for metric_key in metrics.keys():
            if key.lower() in metric_key.lower():
                value = metrics[metric_key]
                if pd.notna(value):
                    return format_value(value, format_type)
    
    return default

def format_value(value, format_type):
    """Format value based on type"""
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
    if sheets_info:
        st.success(f"✅ {len(sheets_info)} sheets discovered")
        st.success(f"✅ {len(all_metrics)} metrics extracted")
        
        if st.button("🔍 Show Discovered Data", use_container_width=True):
            st.write("**Discovered Sheets:**")
            for sheet_name, info in sheets_info.items():
                st.write(f"- {sheet_name}: {info['rows']} rows, {info['columns']} columns")
            
            st.write("**Extracted Metrics:**")
            for key, value in list(all_metrics.items())[:10]:  # Show first 10
                st.write(f"- {key}: {value}")
            if len(all_metrics) > 10:
                st.write(f"... and {len(all_metrics) - 10} more")
    
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
    
    # Top metrics row - Dynamic from discovered data
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        volunteer_keys = ['total_volunteers', 'volunteers', 'volunteer_count', 'total_volunteer', 'volunteer_total']
        total_volunteers = get_metric_value(all_metrics, volunteer_keys)
        st.markdown(f"""
        <div style="background: #4a4a4a; color: white; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Total Volunteers</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{total_volunteers}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">Live from Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        hours_keys = ['total_hours', 'hours', 'volunteer_hours', 'total_volunteer_hours', 'hours_total']
        total_hours = get_metric_value(all_metrics, hours_keys, 'decimal')
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Total Hours</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{total_hours}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">Live from Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        value_keys = ['value_of_hours', 'hours_value', 'monetary_value', 'dollar_value', 'value_hours']
        value_hours = get_metric_value(all_metrics, value_keys, 'currency')
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Value of Hours</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{value_hours}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">Live from Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        change_keys = ['change_from_last_year', 'yearly_change', 'percent_change', 'growth_rate', 'change_percent']
        change_value = get_metric_value(all_metrics, change_keys, 'percentage')
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Change fr. Last Year</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{change_value}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">Live from Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        chart_container = st.container(border=True)
        with chart_container:
            st.subheader("Volunteer Participation Trends Over Time")
            
            # Try to find time series data from any sheet
            chart_data = None
            for sheet_name, df in all_data.items():
                dates, series_data = extract_time_series(df, sheet_name)
                if dates and series_data:
                    chart_data = (dates, series_data)
                    break
            
            if chart_data:
                dates, series_data = chart_data
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
                st.info("📊 No time series data found in the sheets. Please add date/month columns with corresponding numeric data.")
    
    with col2:
        chart_container = st.container(border=True)
        with chart_container:
            st.subheader("Data Overview")
            
            if all_data:
                # Show some basic statistics about the data
                st.write("**Available Data Sheets:**")
                for sheet_name, df in all_data.items():
                    if df is not None and not df.empty:
                        st.write(f"📄 {sheet_name}")
                        st.write(f"   - {len(df)} rows × {len(df.columns)} columns")
                        
                        # Show sample data
                        if len(df) > 0:
                            st.write("   Sample:")
                            sample_data = df.head(2)
                            for col in sample_data.columns[:2]:  # Show first 2 columns
                                values = sample_data[col].dropna().tolist()
                                if values:
                                    st.write(f"   {col}: {values[0]}")

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
        acres_keys = ['acres_cleaned', 'total_acres', 'acres_restored', 'forest_acres', 'cleaned_acres']
        acres_cleaned = get_metric_value(all_metrics, acres_keys, 'decimal')
        st.markdown(f"""
        <div style="background: #4a4a4a; color: white; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Acres Cleaned</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{acres_cleaned}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">Live from Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        forest_keys = ['percent_forest_reached', 'forest_coverage', 'forest_percent', 'coverage_percent']
        forest_percent = get_metric_value(all_metrics, forest_keys, 'percentage')
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">% of Forest Reached</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{forest_percent}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">Live from Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        rtf_keys = ['rtf_volunteers', 'forest_volunteers', 'restoration_volunteers', 'total_rtf_volunteers']
        rtf_volunteers = get_metric_value(all_metrics, rtf_keys)
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">RTF Volunteers</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{rtf_volunteers}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">Live from Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Show available data for this program
    st.subheader("Available Forest Program Data")
    if all_data:
        for sheet_name, df in all_data.items():
            if df is not None and not df.empty:
                # Look for forest-related data
                forest_related = any(keyword in sheet_name.lower() or 
                                   any(keyword in col.lower() for col in df.columns)
                                   for keyword in ['forest', 'acre', 'tree', 'restoration', 'rtf'])
                
                if forest_related:
                    with st.expander(f"📊 {sheet_name} Data"):
                        st.dataframe(df.head(10))

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
    
    with col1:
        survey_keys = ['survey_responses', 'total_responses', 'responses', 'survey_total']
        survey_responses = get_metric_value(all_metrics, survey_keys)
        st.markdown(f"""
        <div style="background: #4a4a4a; color: white; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Total Responses</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{survey_responses}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">Live from Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        barriers_keys = ['percent_facing_barriers', 'barriers_percent', 'barriers', 'accessibility_barriers']
        barriers_percent = get_metric_value(all_metrics, barriers_keys, 'percentage')
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">% Facing Barriers</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{barriers_percent}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">Live from Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        access_keys = ['percent_change_accessibility', 'accessibility_change', 'accessibility', 'access_improvement']
        accessibility_change = get_metric_value(all_metrics, access_keys, 'percentage')
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Accessibility</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{accessibility_change}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">Live from Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        visits_keys = ['percent_change_park_visits', 'park_visits_change', 'visits_change', 'park_visits', 'visits_percent']
        park_visits_change = get_metric_value(all_metrics, visits_keys, 'percentage')
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Park Visits</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{park_visits_change}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">Live from Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Main chart - Park Accessibility Ratings Over Time
    chart_container = st.container(border=True)
    with chart_container:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("Park Accessibility Ratings Over Time by Organization")
            
            # Try to find accessibility data from any sheet
            chart_data = None
            for sheet_name, df in all_data.items():
                dates, series_data = extract_time_series(df, sheet_name)
                if dates and series_data:
                    # Look for accessibility-related data
                    accessibility_data = {}
                    for col_name, values in series_data.items():
                        if any(keyword in col_name.lower() for keyword in ['accessibility', 'rating', 'score', 'organization']):
                            accessibility_data[col_name] = values
                    if accessibility_data:
                        chart_data = (dates, accessibility_data)
                        break
            
            if chart_data:
                dates, org_data = chart_data
                fig_acc = go.Figure()
                colors = ['#333', '#666', '#999', '#ccc']
                
                for i, (org_name, org_values) in enumerate(org_data.items()):
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
                st.warning("⚠️ Accessibility ratings data not available from Google Sheets")
        
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
