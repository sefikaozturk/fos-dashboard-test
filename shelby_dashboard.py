import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Any
import json

# Google Sheets Data Processor Class
class GoogleSheetsDataProcessor:
    def __init__(self, spreadsheet_id: str, api_key: str):
        self.spreadsheet_id = spreadsheet_id
        self.api_key = api_key
        self.base_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"

    def fetch_sheet_data(self, sheet_name: str, range_param: str = '') -> List[List[str]]:
        """Fetch data from a specific sheet range"""
        try:
            range_str = f"!{range_param}" if range_param else ""
            url = f"{self.base_url}/values/{sheet_name}{range_str}?key={self.api_key}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get('values', [])
        except Exception as e:
            st.error(f"Error fetching data from {sheet_name}: {str(e)}")
            return []

    def get_sheet_names(self) -> List[str]:
        """Get all sheet names from the spreadsheet"""
        try:
            url = f"{self.base_url}?key={self.api_key}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return [sheet['properties']['title'] for sheet in data['sheets']]
        except Exception as e:
            st.error(f"Error fetching sheet names: {str(e)}")
            return []

    def process_volunteer_participation_trends(self) -> pd.DataFrame:
        """Process Volunteer Participation Trends"""
        raw_data = self.fetch_sheet_data('Volunteer Participation Trends')
        if not raw_data or len(raw_data) <= 1:
            return pd.DataFrame(columns=['Date', 'Event Name', 'Participant Count', 'Total Count'])
        
        trends = []
        for i in range(1, len(raw_data)):
            row = raw_data[i]
            if len(row) >= 4:
                trends.append({
                    'Date': row[0] if row[0] else '',
                    'Event Name': row[1] if row[1] else '',
                    'Participant Count': int(row[2]) if row[2].isdigit() else 0,
                    'Total Count': int(row[3]) if row[3].isdigit() else 0
                })
        
        df = pd.DataFrame(trends)
        if not df.empty and 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.sort_values('Date')
        return df

    def process_volunteer_satisfaction(self) -> pd.DataFrame:
        """Process Volunteer Satisfaction Data"""
        raw_data = self.fetch_sheet_data('Volunteer Satisfaction')
        if not raw_data or len(raw_data) <= 1:
            return pd.DataFrame(columns=['Date', 'Event Name', 'Satisfaction Score', 'Overall Average'])
        
        satisfaction = []
        for i in range(1, len(raw_data)):
            row = raw_data[i]
            if len(row) >= 4:
                satisfaction.append({
                    'Date': row[0] if row[0] else '',
                    'Event Name': row[1] if row[1] else '',
                    'Satisfaction Score': float(row[2]) if row[2].replace('.', '').isdigit() else 0,
                    'Overall Average': float(row[3]) if row[3].replace('.', '').isdigit() else 0
                })
        
        df = pd.DataFrame(satisfaction)
        if not df.empty and 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df

    def process_most_popular_events(self) -> pd.DataFrame:
        """Process Most Popular Events"""
        raw_data = self.fetch_sheet_data('Most Popular Events')
        if raw_data and len(raw_data) > 1:
            events = []
            for i in range(1, len(raw_data)):
                row = raw_data[i]
                if len(row) >= 3:
                    events.append({
                        'Event Name': row[0] if row[0] else '',
                        'Total Participants': int(row[1]) if row[1].isdigit() else 0,
                        'Percentage Share': float(row[2]) if row[2].replace('.', '').isdigit() else 0
                    })
            return pd.DataFrame(events)
        else:
            # Fall back to calculating from participation data
            participation_df = self.process_volunteer_participation_trends()
            if participation_df.empty:
                return pd.DataFrame(columns=['Event Name', 'Total Participants', 'Percentage Share'])
            
            event_counts = participation_df.groupby('Event Name')['Participant Count'].sum().reset_index()
            total_participants = event_counts['Participant Count'].sum()
            
            if total_participants > 0:
                event_counts['Percentage Share'] = (event_counts['Participant Count'] / total_participants * 100).round(2)
            else:
                event_counts['Percentage Share'] = 0
            
            popular_events = event_counts.nlargest(3, 'Participant Count')
            popular_events.columns = ['Event Name', 'Total Participants', 'Percentage Share']
            return popular_events

    def process_acres_cleaned_timeline(self) -> pd.DataFrame:
        """Process Acres Cleaned Timeline"""
        raw_data = self.fetch_sheet_data('Acres Cleaned Timeline')
        if not raw_data or len(raw_data) <= 1:
            return pd.DataFrame(columns=['Date', 'Acres Cleaned', 'Cumulative Total'])
        
        timeline = []
        cumulative_total = 0
        for i in range(1, len(raw_data)):
            row = raw_data[i]
            if len(row) >= 2:
                acres_cleaned = float(row[1]) if row[1].replace('.', '').isdigit() else 0
                cumulative_total += acres_cleaned
                timeline.append({
                    'Date': row[0] if row[0] else '',
                    'Acres Cleaned': acres_cleaned,
                    'Cumulative Total': cumulative_total
                })
        
        df = pd.DataFrame(timeline)
        if not df.empty and 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            three_years_ago = datetime.now() - timedelta(days=3*365)
            df = df[df['Date'] >= three_years_ago]
        return df

    def process_survey_response_details(self) -> pd.DataFrame:
        """Process Survey Response Details"""
        raw_data = self.fetch_sheet_data('Survey Response Details')
        if not raw_data or len(raw_data) <= 1:
            return pd.DataFrame(columns=['Date', 'Respondent ID', 'Organization', 'Barrier Statements', 'Park Visit Details', 'Accessibility Comments'])
        
        responses = []
        for i in range(1, len(raw_data)):
            row = raw_data[i]
            if len(row) >= 6:
                responses.append({
                    'Date': row[0] if row[0] else '',
                    'Respondent ID': row[1] if row[1] else '',
                    'Organization': row[2] if row[2] else '',
                    'Barrier Statements': row[3] if row[3] else '',
                    'Park Visit Details': row[4] if row[4] else '',
                    'Accessibility Comments': row[5] if row[5] else ''
                })
        
        df = pd.DataFrame(responses)
        if not df.empty and 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df

    def process_barrier_ratings(self) -> pd.DataFrame:
        """Process Barrier Ratings Over Time"""
        raw_data = self.fetch_sheet_data('Barrier Ratings Over Time')
        if not raw_data or len(raw_data) <= 1:
            return pd.DataFrame(columns=['Date', 'Organization', 'Rating'])
        
        ratings = []
        for i in range(1, len(raw_data)):
            row = raw_data[i]
            if len(row) >= 3:
                ratings.append({
                    'Date': row[0] if row[0] else '',
                    'Organization': row[1] if row[1] else '',
                    'Rating': float(row[2]) if row[2].replace('.', '').isdigit() else 0
                })
        
        df = pd.DataFrame(ratings)
        if not df.empty and 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df

    def calculate_dashboard_metrics(self) -> Dict[str, Any]:
        """Calculate key metrics for dashboard"""
        metrics = {}
        
        # Volunteer metrics
        participation_df = self.process_volunteer_participation_trends()
        if not participation_df.empty:
            metrics['total_volunteers'] = participation_df['Participant Count'].sum()
            metrics['total_hours'] = participation_df['Total Count'].sum()
            metrics['value_of_hours'] = metrics['total_hours'] * 13.2  # Assuming $13.2/hour value
            
        # Acres metrics
        acres_df = self.process_acres_cleaned_timeline()
        if not acres_df.empty:
            metrics['total_acres_cleaned'] = acres_df['Cumulative Total'].iloc[-1] if len(acres_df) > 0 else 0
            metrics['percent_forest_reached'] = min(100, (metrics['total_acres_cleaned'] / 4000) * 100)  # Assuming 4000 total acres
            
        # Survey metrics
        survey_df = self.process_survey_response_details()
        if not survey_df.empty:
            metrics['total_survey_responses'] = len(survey_df)
            barrier_count = len([x for x in survey_df['Barrier Statements'] if x and 'yes' in x.lower()])
            metrics['percent_facing_barriers'] = (barrier_count / len(survey_df) * 100) if len(survey_df) > 0 else 0
            
        return metrics

# Page config
st.set_page_config(
    page_title="Friends of Shelby Dashboard", 
    page_icon="🌲", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (keeping original styling)
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
    
    .sidebar .sidebar-content {
        background-color: #4a4a4a;
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

# Initialize data processor
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_data_processor(spreadsheet_id, api_key):
    return GoogleSheetsDataProcessor(spreadsheet_id, api_key)

# Sidebar Navigation
with st.sidebar:
    st.markdown("🌲 **Friends of Shelby**")
    
    # Google Sheets Configuration
    st.markdown("### Data Configuration")
    default_spreadsheet_id = "1OgP1vp1OjiRgtisNrHoHxPIPbRxGjKtcegCS7ztVPr0"
    spreadsheet_id = st.text_input("Spreadsheet ID", value=default_spreadsheet_id)
    api_key = st.text_input("Google Sheets API Key", type="password")
    
    if st.button("Refresh Data"):
        st.cache_data.clear()
    
    st.markdown('<div class="nav-section">', unsafe_allow_html=True)
    st.markdown("### Navigation")
    
    # Navigation buttons
    volunteer_selected = st.button("Volunteer Program", key="nav1", use_container_width=True)
    forest_selected = st.button("Restore The Forest Program", key="nav2", use_container_width=True)
    strategic_selected = st.button("Strategic Plan - Pillar 1", key="nav3", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Filters section
    st.markdown("### General Filters")
    st.selectbox("Date Range", ["Last Month", "Last 3 Months", "Last Year"], key="sidebar_date")
    st.selectbox("Organization", ["All", "ICLR", "Cerecore HCA"], key="sidebar_org")
    st.multiselect("Metrics to Show", ["Volunteers", "Hours", "Accessibility", "Satisfaction"], key="sidebar_metrics")

# Check if API key is provided
if not api_key:
    st.warning("Please enter your Google Sheets API key in the sidebar to load real data. Using sample data for now.")
    data_processor = None
else:
    try:
        data_processor = get_data_processor(spreadsheet_id, api_key)
        # Test connection
        sheet_names = data_processor.get_sheet_names()
        if not sheet_names:
            st.error("Could not connect to Google Sheets. Please check your API key and spreadsheet ID.")
            data_processor = None
        else:
            st.success(f"Connected to Google Sheets! Found {len(sheet_names)} sheets")
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {str(e)}")
        data_processor = None

# Determine current page
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Volunteer Program"

if volunteer_selected:
    st.session_state.current_page = "Volunteer Program"
elif forest_selected:
    st.session_state.current_page = "Restore The Forest Program"
elif strategic_selected:
    st.session_state.current_page = "Strategic Plan - Pillar 1"

page = st.session_state.current_page

# Get real data or use fallback
if data_processor:
    try:
        metrics = data_processor.calculate_dashboard_metrics()
        participation_df = data_processor.process_volunteer_participation_trends()
        satisfaction_df = data_processor.process_volunteer_satisfaction()
        popular_events_df = data_processor.process_most_popular_events()
        acres_df = data_processor.process_acres_cleaned_timeline()
        survey_df = data_processor.process_survey_response_details()
        barrier_ratings_df = data_processor.process_barrier_ratings()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        metrics = {}
        participation_df = pd.DataFrame()
        satisfaction_df = pd.DataFrame()
        popular_events_df = pd.DataFrame()
        acres_df = pd.DataFrame()
        survey_df = pd.DataFrame()
        barrier_ratings_df = pd.DataFrame()
else:
    # Fallback to sample data
    metrics = {
        'total_volunteers': 21324, 'total_hours': 16769, 'value_of_hours': 221324.50,
        'total_acres_cleaned': 1340, 'percent_forest_reached': 34,
        'total_survey_responses': 25, 'percent_facing_barriers': 75
    }
    participation_df = pd.DataFrame()
    satisfaction_df = pd.DataFrame()
    popular_events_df = pd.DataFrame()
    acres_df = pd.DataFrame()
    survey_df = pd.DataFrame()
    barrier_ratings_df = pd.DataFrame()

# Page 1: Volunteer Program
if page == "Volunteer Program":
    # Header
    st.markdown('<div class="component-separator">', unsafe_allow_html=True)
    col1, col2 = st.columns([6, 2])
    with col1:
        st.title("Friends of Shelby Dashboard")
        st.markdown("**Volunteer Program**")
    with col2:
        st.markdown("**Sefika Ozturk** - *Admin*")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background: #4a4a4a; color: white; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Total Volunteers</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{metrics.get('total_volunteers', 21324):,}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">+2,031</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Total Hours</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{metrics.get('total_hours', 16769):,}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">+3,390</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Value of The Hours</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">${metrics.get('value_of_hours', 221324.50):,.2f}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">+$23,456</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Change fr. Last Year</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">12.8%</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">↑ 2.2%</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts row
    col1, col2 = st.columns([2, 1])
    
    with col1:
        chart_container = st.container(border=True)
        with chart_container:
            st.subheader("Volunteer Participation Trends Over Time")
            
            if not participation_df.empty:
                # Create line chart from real data
                fig = go.Figure()
                for event in participation_df['Event Name'].unique():
                    event_data = participation_df[participation_df['Event Name'] == event]
                    fig.add_trace(go.Scatter(
                        x=event_data['Date'], 
                        y=event_data['Participant Count'],
                        name=event,
                        mode='lines+markers'
                    ))
            else:
                # Fallback sample data
                months = ['Jan', 'Feb', 'Mar', 'Apr', 'May']
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=months, y=[45, 55, 65, 45, 35], name='Invasive Removal', line=dict(color='#333')))
                fig.add_trace(go.Scatter(x=months, y=[35, 75, 55, 65, 45], name='Trail Maintenance', line=dict(color='#666')))
                fig.add_trace(go.Scatter(x=months, y=[25, 45, 55, 85, 65], name='Painting', line=dict(color='#999')))
                fig.add_trace(go.Scatter(x=months, y=[55, 35, 45, 75, 55], name='Lake Cleaning', line=dict(color='#ccc')))
            
            fig.update_layout(
                showlegend=True,
                height=400,
                xaxis_title="",
                yaxis_title="",
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        chart_container = st.container(border=True)
        with chart_container:
            st.subheader("Popular Events")
            
            if not popular_events_df.empty:
                # Use real data
                fig_pie = go.Figure(data=[go.Pie(
                    labels=popular_events_df['Event Name'][:3], 
                    values=popular_events_df['Total Participants'][:3],
                    hole=0.5,
                    showlegend=True
                )])
            else:
                # Fallback sample data
                labels = ['Trail Main...', 'Invasive ...', 'Pai...']
                values = [40, 35, 25]
                colors = ['#f4d03f', '#d5b895', '#a6a6a6']
                fig_pie = go.Figure(data=[go.Pie(
                    labels=labels, 
                    values=values,
                    hole=0.5,
                    marker_colors=colors,
                    showlegend=True
                )])
            
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
    
    # Bottom section - Volunteer Satisfaction
    chart_container = st.container(border=True)
    with chart_container:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("Volunteer Satisfaction")
            
            if not satisfaction_df.empty:
                # Use real satisfaction data
                fig_bar = px.bar(satisfaction_df, x='Event Name', y='Satisfaction Score', 
                               title="", color='Event Name')
            else:
                # Fallback sample data
                categories = ['Invasive Removal', 'Trail Maintenance', 'Painting', 'Lake Cleaning']
                months_bar = ['Jan', 'Feb', 'Mar', 'Apr', 'May']
                
                fig_bar = go.Figure()
                for i, month in enumerate(months_bar):
                    values = np.random.randint(60, 90, len(categories))
                    fig_bar.add_trace(go.Bar(
                        name=month,
                        x=categories,
                        y=values,
                        marker_color=['#333', '#666', '#999', '#ccc'][i % 4]
                    ))
                fig_bar.update_layout(barmode='group')
            
            fig_bar.update_layout(
                height=400,
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            st.markdown("### Filters")
            st.selectbox("Pick date", ["Overall"])
            st.selectbox("Pick organization", ["Overall"])
            st.checkbox("Show multiple")

# Page 2: Restore The Forest Program  
elif page == "Restore The Forest Program":
    # Header
    st.markdown('<div class="component-separator">', unsafe_allow_html=True)
    col1, col2 = st.columns([6, 2])
    with col1:
        st.title("Friends of Shelby Dashboard")
        st.markdown("**Restore The Forest Program**")
    with col2:
        st.markdown("**Renee McKelvey** - *Community Member*")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Top metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="background: #4a4a4a; color: white; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Acres Cleaned</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{metrics.get('total_acres_cleaned', 1340):,}</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">Acreage for the current month</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">% of Forest Reached</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{metrics.get('percent_forest_reached', 34):.0f}%</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">Area % of the forest covered by RTF</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
            <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Volunteers</div>
            <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{metrics.get('percent_forest_reached', 34):.0f}%</div>
            <div style="font-size: 0.72rem; opacity: 0.8;">Area % of the forest covered by RTF</div>
        </div>
        """, unsafe_allow_html=True)
            
    # Charts row with proper containers
    col1, col2 = st.columns([2, 1])
    
    with col1:
        chart_container = st.container(border=True)
        with chart_container:
            st.subheader("Acres Cleaned Over Time")
            
            # Line chart with two years
            months_long = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'August']
            data_2024 = [12, 10, 8, 15, 10, 8, 6, 14]
            data_2025 = [8, 9, 7, 12, 8, 12, 4, 18]
            
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=months_long, y=data_2024, name='2024', line=dict(color='#333')))
            fig_line.add_trace(go.Scatter(x=months_long, y=data_2025, name='2025', line=dict(color='#666')))
            
            fig_line.update_layout(
                height=400,
                showlegend=True,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            st.plotly_chart(fig_line, use_container_width=True)
    
    with col2:
        chart_container = st.container(border=True)
        with chart_container:
            st.subheader("Acres Cleaned per Month")
            
            months_short, acres_data = generate_forest_data()
            
            # Stacked bar chart
            fig_stack = go.Figure()
            fig_stack.add_trace(go.Bar(
                name='Type 1',
                x=months_short,
                y=[x*0.6 for x in acres_data],
                marker_color='#d5b895'
            ))
            fig_stack.add_trace(go.Bar(
                name='Type 2',
                x=months_short,
                y=[x*0.4 for x in acres_data],
                marker_color='#a6a6a6'
            ))
            
            fig_stack.update_layout(
                barmode='stack',
                height=400,
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            st.plotly_chart(fig_stack, use_container_width=True)
    
    # Bottom section - Logs with proper containers
    col1, col2 = st.columns(2)
    
    with col1:
        log_container = st.container(border=True)
        with log_container:
            st.subheader("ArcGIS System Log")
            
            log_items = [
                ("New Support Ticket Opened", "Today"),
                ("System Reset", "14 min"),
                ("Production Server Down", "2 hours"),
                ("System Shutdown", "1 day"),
                ("DB Overloaded 80%", "1 day"),
                ("13 New Alerts", "2 days")
            ]
            
            for item, time in log_items:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(f"• {item}")
                with col_b:
                    st.write(time)
            
            st.write("🔄 view all")
    
    with col2:
        log_container = st.container(border=True)
        with log_container:
            st.subheader("DIY Volunteers & WildSpotter Submissions Log")
            
            # Log entries
            st.markdown("""
            **Christan Bilney** - *2 days ago*  
            Low priority | V 3.20
            
            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisl ut aliquip ex ea commodo consequat. **More...**
            
            ---
            
            **Hady Vanetti** - *4 days ago*  
            **Critical** | V 3.13
            
            Aliquam vel nibh iaculis, ornare purus sit amet, euismod dui. Cras sed tristique neque. Cras ornare dui lorem, vel rhoncus elit venenatis sit amet. Suspendisse varius massa in gravida commodo. **More...**
            """)

# Page 3: Strategic Plan - Pillar 1
else:
    # Header
    st.markdown('<div class="component-separator">', unsafe_allow_html=True)
    col1, col2 = st.columns([6, 2])
    with col1:
        st.title("Friends of Shelby Dashboard")
        st.markdown("**Strategic Plan - Pillar 1**")
    with col2:
        st.markdown("**Sefika Ozturk** - *Admin*")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Top metrics with equal sizing
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        with st.container():
            st.markdown("""
            <div style="background: #4a4a4a; color: white; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Total Responses</div>
                <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">25</div>
                <div style="font-size: 0.72rem; opacity: 0.8;">+2</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown("""
            <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
                <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">% Facing Barriers</div>
                <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">75%</div>
                <div style="font-size: 0.72rem; opacity: 0.8;">+3%</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        with st.container():
            st.markdown("""
            <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
                <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Accessibility</div>
                <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">+23%</div>
                <div style="font-size: 0.72rem; opacity: 0.8;">+5%</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col4:
        with st.container():
            st.markdown("""
            <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
                <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Park Visits</div>
                <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">+14.8%</div>
                <div style="font-size: 0.72rem; opacity: 0.8;">↑ 2.2%</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Main chart with proper container
    col1, col2 = st.columns([3, 1])
    
    with col1:
        chart_container = st.container(border=True)
        with chart_container:
            st.subheader("Park Accessibility Ratings Over Time by Organization")
            
            months_acc, iclr_data, cerecore_data = generate_accessibility_data()
            
            fig_acc = go.Figure()
            fig_acc.add_trace(go.Scatter(
                x=months_acc, 
                y=iclr_data, 
                name='ICLR',
                line=dict(color='#333'),
                marker=dict(size=8)
            ))
            fig_acc.add_trace(go.Scatter(
                x=months_acc, 
                y=cerecore_data, 
                name='Cerecore HCA',
                line=dict(color='#666'),
                marker=dict(size=8)
            ))
            
            fig_acc.update_layout(
                height=400,
                showlegend=True,
                plot_bgcolor='white',
                paper_bgcolor='white',
                yaxis=dict(range=[0, 100])
            )
            st.plotly_chart(fig_acc, use_container_width=True)
    
    with col2:
        filter_container = st.container(border=True)
        with filter_container:
            st.markdown("### Filters")
            col_q4, col_q5, col_q6 = st.columns(3)
            with col_q4:
                st.button("Q4", type="secondary")
            with col_q5:
                st.button("Q5", type="secondary") 
            with col_q6:
                st.button("Q6", type="primary")
            
            st.selectbox("Pick date", ["04/2025"])
            st.selectbox("Pick organization", ["ICLR, Cerecore HCA"])
            st.checkbox("Show multiple", value=True)
    
    # Bottom section - Horizontal bar chart with proper container
    col1, col2 = st.columns([4, 1])
    
    with col1:
        chart_container = st.container(border=True)
        with chart_container:
            st.subheader("Park Accessibility Statements")
            
            statements = [
                "It is easy to physically get to the park.",
                "It is easy to find their way around the park.",
                "The park has activities they want to participate in.",
                "They see people that look like them at the park.",
                "It is easy to find information about park activities.",
                "It is easy for them to get equipments they need.",
                "They feel welcome at the park.",
                "They feel safe at the park."
            ]
            
            values = [13, 20, 34, 36, 45, 46, 66, 80]
            
            fig_horiz = go.Figure()
            fig_horiz.add_trace(go.Bar(
                y=statements,
                x=values,
                orientation='h',
                marker_color='#333'
            ))
            
            fig_horiz.update_layout(
                height=500,
                xaxis_title="Response Rate (%)",
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=300)
            )
            st.plotly_chart(fig_horiz, use_container_width=True)
    
    with col2:
        filter_container = st.container(border=True)
        with filter_container:
            col_q4b, col_q5b, col_q6b = st.columns(3)
            with col_q4b:
                st.button("Q4", type="secondary", key="q4b")
            with col_q5b:
                st.button("Q5", type="secondary", key="q5b")
            with col_q6b:
                st.button("Q6", type="primary", key="q6b")
