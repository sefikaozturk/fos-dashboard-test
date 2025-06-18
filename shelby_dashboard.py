import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from io import StringIO

# Page config
st.set_page_config(
    page_title="Friends of Shelby Dashboard",
    page_icon="🌲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to fetch real data from Google Sheets
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_google_sheets_data():
    """Fetch ALL data from Google Sheets with correct GIDs"""
    try:
        # Your Google Sheets document ID
        spreadsheet_id = "1OgP1vp1OjiRgtisNrHoHxPIPbRxGjKtcegCS7ztVPr0"
        
        # Correct sheet URLs with your actual GIDs
        sheet_urls = {
            'main_metrics': f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid=433779691",  # Overall Dashboard
            'volunteer_trends': f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid=650046450",  # Volunteer Participation Trends
            'volunteer_satisfaction': f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid=1063103188",  # Volunteer Satisfaction
            'popular_events': f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid=130383720",  # Most Popular Events
            'acres_timeline': f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid=2145939805",  # Acres Cleaned Timeline
            'acres_monthly': f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid=614540949",  # Acres Cleaned Monthly
            'barrier_ratings': f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid=385018677",  # Barrier Ratings Over Time
            'park_visits': f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid=840958021",  # Park Visits Data
            'accessibility_ratings': f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid=993445816",  # Park Accessibility Ratings
            'survey_details': f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid=571418631"  # Survey Response Details
        }
        
        all_data = {}
        
        for sheet_name, url in sheet_urls.items():
            try:
                # Add headers to mimic browser request
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(url, timeout=15, headers=headers)
                
                if response.status_code == 200:
                    csv_data = StringIO(response.text)
                    df = pd.read_csv(csv_data)
                    
                    # Clean column names
                    df.columns = df.columns.str.strip()
                    
                    # Remove completely empty rows and columns
                    df = df.dropna(how='all').dropna(axis=1, how='all')
                    
                    all_data[sheet_name] = df
                    st.success(f"✅ Loaded {sheet_name}: {len(df)} rows, {len(df.columns)} columns")
                else:
                    st.error(f"❌ Failed to fetch {sheet_name}: HTTP {response.status_code}")
                    all_data[sheet_name] = None
                    
            except Exception as e:
                st.error(f"❌ Error fetching {sheet_name}: {str(e)}")
                all_data[sheet_name] = None
        
        return all_data
        
    except Exception as e:
        st.error(f"Critical error fetching Google Sheets data: {str(e)}")
        return None


# Function to extract metrics from the main data sheet
def extract_metrics(sheets_data):
    """Extract key metrics from Google Sheets data"""
    if not sheets_data or 'main_metrics' not in sheets_data or sheets_data['main_metrics'] is None:
        st.error("Main metrics data not available from Google Sheets")
        return {}
    
    df = sheets_data['main_metrics']
    metrics = {}
    
    try:
        # Method 1: If data is in key-value pairs format
        if 'Metric' in df.columns and 'Value' in df.columns:
            for _, row in df.iterrows():
                if pd.notna(row['Metric']) and pd.notna(row['Value']):
                    key = str(row['Metric']).strip().lower().replace(' ', '_').replace('%', 'percent')
                    value = pd.to_numeric(row['Value'], errors='coerce')
                    if pd.notna(value):
                        metrics[key] = value
        
        # Method 2: If metrics are in column headers with values below
        else:
            for col in df.columns:
                if col.strip():
                    clean_col = col.strip().lower().replace(' ', '_').replace('%', 'percent')
                    # Get first non-null numeric value from the column
                    col_values = pd.to_numeric(df[col], errors='coerce').dropna()
                    if len(col_values) > 0:
                        metrics[clean_col] = col_values.iloc[0]
        
        # Method 3: Look for specific patterns in cell values
        if not metrics:
            # Search through all cells for recognizable patterns
            for col in df.columns:
                for idx, value in df[col].items():
                    if pd.notna(value):
                        str_val = str(value).strip()
                        # Look for patterns like "Total Volunteers: 891"
                        if ':' in str_val:
                            parts = str_val.split(':', 1)
                            if len(parts) == 2:
                                key = parts[0].strip().lower().replace(' ', '_')
                                val = pd.to_numeric(parts[1].strip(), errors='coerce')
                                if pd.notna(val):
                                    metrics[key] = val
        
    except Exception as e:
        st.error(f"Error extracting metrics: {str(e)}")
    
    return metrics

# Function to get volunteer trend data from sheets
def get_volunteer_trends(sheets_data):
    """Extract volunteer trend data from Google Sheets"""
    if not sheets_data or 'volunteer_trends' not in sheets_data or sheets_data['volunteer_trends'] is None:
        st.warning("Volunteer trends data not available from Google Sheets")
        return None, None
    
    df = sheets_data['volunteer_trends']
    
    try:
        # Look for month/date column
        month_col = None
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['month', 'date', 'time', 'period']):
                month_col = col
                break
        
        if month_col is None:
            st.warning("No month/date column found in volunteer trends data")
            return None, None
        
        months = df[month_col].dropna().tolist()
        activities = {}
        
        # Get all other numeric columns as activities
        for col in df.columns:
            if col != month_col:
                numeric_data = pd.to_numeric(df[col], errors='coerce').fillna(0)
                if numeric_data.sum() > 0:  # Only include if there's actual data
                    activities[col] = numeric_data.tolist()
        
        return months, activities
        
    except Exception as e:
        st.error(f"Error processing volunteer trends: {str(e)}")
        return None, None

# Function to get forest restoration data
def get_forest_data(sheets_data):
    """Extract forest restoration data from Google Sheets"""
    if not sheets_data or 'forest_data' not in sheets_data or sheets_data['forest_data'] is None:
        st.warning("Forest data not available from Google Sheets")
        return None, None
    
    df = sheets_data['forest_data']
    
    try:
        # Look for month and acres columns
        month_col = None
        acres_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['month', 'date', 'time', 'period']):
                month_col = col
            elif any(keyword in col_lower for keyword in ['acre', 'area', 'cleaned', 'restored']):
                acres_col = col
        
        if month_col is None or acres_col is None:
            st.warning("Month or acres column not found in forest data")
            return None, None
        
        months = df[month_col].dropna().tolist()
        acres = pd.to_numeric(df[acres_col], errors='coerce').fillna(0).tolist()
        
        return months, acres
        
    except Exception as e:
        st.error(f"Error processing forest data: {str(e)}")
        return None, None

# Function to get accessibility data
def get_accessibility_data(sheets_data):
    """Extract accessibility data from Google Sheets"""
    if not sheets_data or 'accessibility_data' not in sheets_data or sheets_data['accessibility_data'] is None:
        st.warning("Accessibility data not available from Google Sheets")
        return None, None
    
    df = sheets_data['accessibility_data']
    
    try:
        # Look for month column
        month_col = None
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['month', 'date', 'time', 'period']):
                month_col = col
                break
        
        if month_col is None:
            st.warning("No month column found in accessibility data")
            return None, None
        
        months = df[month_col].dropna().tolist()
        org_data = {}
        
        # Get organization columns
        for col in df.columns:
            if col != month_col:
                numeric_data = pd.to_numeric(df[col], errors='coerce').fillna(0)
                if numeric_data.sum() > 0:
                    org_data[col] = numeric_data.tolist()
        
        return months, org_data
        
    except Exception as e:
        st.error(f"Error processing accessibility data: {str(e)}")
        return None, None

# Function to get survey statements data
def get_survey_statements(sheets_data):
    """Extract survey statements data from Google Sheets"""
    if not sheets_data or 'survey_data' not in sheets_data or sheets_data['survey_data'] is None:
        st.warning("Survey data not available from Google Sheets")
        return None, None
    
    df = sheets_data['survey_data']
    
    try:
        # Look for statement and percentage columns
        statement_col = None
        percentage_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['statement', 'question', 'text', 'description']):
                statement_col = col
            elif any(keyword in col_lower for keyword in ['percent', 'rate', 'score', 'value', '%']):
                percentage_col = col
        
        if statement_col is None or percentage_col is None:
            st.warning("Statement or percentage column not found in survey data")
            return None, None
        
        statements = df[statement_col].dropna().tolist()
        percentages = pd.to_numeric(df[percentage_col], errors='coerce').fillna(0).tolist()
        
        return statements, percentages
        
    except Exception as e:
        st.error(f"Error processing survey data: {str(e)}")
        return None, None

# Fetch all data from Google Sheets
with st.spinner("Loading data from Google Sheets..."):
    sheets_data = fetch_google_sheets_data()

if sheets_data is None:
    st.error("❌ Cannot load dashboard - Google Sheets data unavailable")
    st.stop()

# Extract metrics
metrics = extract_metrics(sheets_data)

# Custom CSS
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
.component-separator {
    margin: 1rem 0;
    padding-bottom: 1rem;
}
.chart-container {
    background: white;
    border-radius: 10px;
    padding: 1.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 2rem;
    border: 1px solid #e1e5e9;
}
.stSelectbox > div > div {
    background-color: white;
}
h1 {
    color: #333;
    font-weight: 600;
}
h3 {
    color: #666;
    font-weight: 500;
}
.nav-section {
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e1e5e9;
}
.block-container {
    padding-top: 1rem;
}
div[data-testid="column"] {
    padding: 0 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation
with st.sidebar:
    st.markdown("🌲 **Friends of Shelby**")
    st.markdown('<div class="nav-section">', unsafe_allow_html=True)
    st.markdown("### Navigation")
    
    volunteer_selected = st.button("Volunteer Program", key="nav1", use_container_width=True)
    forest_selected = st.button("Restore The Forest Program", key="nav2", use_container_width=True)
    strategic_selected = st.button("Strategic Plan - Pillar 1", key="nav3", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### General Filters")
    st.selectbox("Date Range", ["Last Month", "Last 3 Months", "Last Year"], key="sidebar_date")
    st.selectbox("Organization", ["All", "ICLR", "Cerecore HCA"], key="sidebar_org")
    st.multiselect("Metrics to Show", ["Volunteers", "Hours", "Accessibility", "Satisfaction"], key="sidebar_metrics")
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Show data status
if sheets_data:
    st.sidebar.success(f"✅ Data loaded from Google Sheets")
    if st.sidebar.button("Show Raw Data", key="show_raw"):
        st.sidebar.write("**Available sheets:**")
        for sheet_name, df in sheets_data.items():
            if df is not None:
                st.sidebar.write(f"- {sheet_name}: {len(df)} rows")
            else:
                st.sidebar.write(f"- {sheet_name}: ❌ Failed to load")

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

# Helper function to safely get metric value
def get_metric_value(key, format_type="number"):
    value = metrics.get(key)
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

# Page 1: Volunteer Program
if page == "Volunteer Program":
    st.markdown('<div class="component-separator">', unsafe_allow_html=True)
    col1, col2 = st.columns([6, 2])
    with col1:
        st.title("Friends of Shelby Dashboard")
        st.markdown("**Volunteer Program**")
    with col2:
        st.markdown("**Sefika Ozturk** - *Admin*")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Top metrics row - ONLY from Google Sheets
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_volunteers = get_metric_value('total_volunteers')
        st.markdown(f"""
        <div style="background: #4a4a4a; color: white; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Total Volunteers</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{total_volunteers}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_hours = get_metric_value('total_hours', 'decimal')
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Total Hours</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{total_hours}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        value_hours = get_metric_value('value_of_hours', 'currency')
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Value of The Hours</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{value_hours}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        change_value = get_metric_value('change_from_last_year', 'percentage')
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Change fr. Last Year</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{change_value}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts row - ONLY from Google Sheets
    col1, col2 = st.columns([2, 1])
    
    with col1:
        chart_container = st.container(border=True)
        with chart_container:
            st.subheader("Volunteer Participation Trends Over Time")
            
            months, activities = get_volunteer_trends(sheets_data)
            
            if months and activities:
                fig = go.Figure()
                colors = ['#333', '#666', '#999', '#ccc']
                
                for i, (activity_name, activity_data) in enumerate(activities.items()):
                    fig.add_trace(go.Scatter(
                        x=months[:len(activity_data)], 
                        y=activity_data[:len(months)], 
                        name=activity_name,
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
                st.warning("⚠️ Volunteer trends data not available from Google Sheets")
    
    with col2:
        chart_container = st.container(border=True)
        with chart_container:
            st.subheader("Popular Events")
            
            # Try to create pie chart from volunteer trends data
            months, activities = get_volunteer_trends(sheets_data)
            
            if activities:
                # Sum up activities to show popularity
                activity_totals = {name: sum(data) for name, data in activities.items()}
                
                labels = list(activity_totals.keys())
                values = list(activity_totals.values())
                colors = ['#f4d03f', '#d5b895', '#a6a6a6', '#333']
                
                fig_pie = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.5,
                    marker_colors=colors[:len(labels)],
                    showlegend=True
                )])
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.warning("⚠️ Event popularity data not available from Google Sheets")

# Page 2: Restore The Forest Program
elif page == "Restore The Forest Program":
    st.markdown('<div class="component-separator">', unsafe_allow_html=True)
    col1, col2 = st.columns([6, 2])
    with col1:
        st.title("Friends of Shelby Dashboard")
        st.markdown("**Restore The Forest Program**")
    with col2:
        st.markdown("**Renee McKelvey** - *Community Member*")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Top metrics - ONLY from Google Sheets
    col1, col2, col3 = st.columns(3)
    
    with col1:
        acres_cleaned = get_metric_value('total_acres_cleaned', 'decimal')
        st.markdown(f"""
        <div style="background: #4a4a4a; color: white; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Acres Cleaned</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{acres_cleaned}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        forest_percent = get_metric_value('percent_forest_reached', 'percentage')
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">% of Forest Reached</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{forest_percent}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        rtf_volunteers = get_metric_value('total_rtf_volunteers')
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">  
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">RTF Volunteers</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{rtf_volunteers}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts - ONLY from Google Sheets
    col1, col2 = st.columns([2, 1])
    
    with col1:
        chart_container = st.container(border=True)
        with chart_container:
            st.subheader("Acres Cleaned Over Time")
            
            months, acres_data = get_forest_data(sheets_data)
            
            if months and acres_data:
                fig_line = go.Figure()
                fig_line.add_trace(go.Scatter(
                    x=months, 
                    y=acres_data, 
                    name='Acres Cleaned',
                    line=dict(color='#333'),
                    mode='lines+markers'
                ))
                
                fig_line.update_layout(
                    height=400,
                    showlegend=True,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    yaxis_title="Acres"
                )
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.warning("⚠️ Forest restoration timeline data not available from Google Sheets")
    
    with col2:
        chart_container = st.container(border=True)
        with chart_container:
            st.subheader("Monthly Restoration Summary")
            
            rtf_hours = get_metric_value('total_rtf_hours', 'decimal')
            st.markdown(f"""
            **Total RTF Hours: {rtf_hours}**  
            *From Google Sheets*
            
            Forest restoration activities tracked through volunteer submissions and ArcGIS monitoring.
            """)

# Page 3: Strategic Plan - Pillar 1
else:
    st.markdown('<div class="component-separator">', unsafe_allow_html=True)
    col1, col2 = st.columns([6, 2])
    with col1:
        st.title("Friends of Shelby Dashboard")
        st.markdown("**Strategic Plan - Pillar 1**")
    with col2:
        st.markdown("**Sefika Ozturk** - *Admin*")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Top metrics - ONLY from Google Sheets
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        survey_responses = get_metric_value('total_survey_responses')
        st.markdown(f"""
        <div style="background: #4a4a4a; color: white; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Total Responses</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{survey_responses}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
# Complete the third page - Strategic Plan Pillar 1
# This goes after the cut-off point in your existing code

    with col2:
        barriers_percent = get_metric_value('percent_facing_barriers', 'percentage')
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">% Facing Barriers</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{barriers_percent}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        accessibility_change = get_metric_value('percent_change_accessibility', 'percentage')
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Accessibility</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{accessibility_change}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">From Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        park_visits_change = get_metric_value('percent_change_park_visits', 'percentage')
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
            
            months, org_data = get_accessibility_data(sheets_data)
            
            if months and org_data:
                fig_acc = go.Figure()
                colors = ['#333', '#666', '#999', '#ccc']
                
                for i, (org_name, org_values) in enumerate(org_data.items()):
                    fig_acc.add_trace(go.Scatter(
                        x=months[:len(org_values)], 
                        y=org_values[:len(months)], 
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
        statements, percentages = get_survey_statements(sheets_data)
        
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
