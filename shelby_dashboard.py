import streamlit as st
# ─────────── Securely load Google Sheets creds ───────────
spreadsheet_id = st.secrets["SPREADSHEET_ID"]
api_key         = st.secrets["GOOGLE_SHEETS_API_KEY"]

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
        raw_data = self.fetch_sheet_data('Volunteer Participation Trends')
        if not raw_data or len(raw_data) <= 1:
            return pd.DataFrame(columns=['Date', 'Event Name', 'Participant Count', 'Total Count'])
        trends = []
        for i in range(1, len(raw_data)):
            row = raw_data[i]
            if len(row) >= 4:
                trends.append({
                    'Date': row[0],
                    'Event Name': row[1],
                    'Participant Count': int(row[2]) if row[2].isdigit() else 0,
                    'Total Count': int(row[3]) if row[3].isdigit() else 0
                })
        df = pd.DataFrame(trends)
        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.sort_values('Date')
        return df

    def process_volunteer_satisfaction(self) -> pd.DataFrame:
        raw_data = self.fetch_sheet_data('Volunteer Satisfaction')
        if not raw_data or len(raw_data) <= 1:
            return pd.DataFrame(columns=['Date', 'Event Name', 'Satisfaction Score', 'Overall Average'])
        satisfaction = []
        for i in range(1, len(raw_data)):
            row = raw_data[i]
            if len(row) >= 4:
                satisfaction.append({
                    'Date': row[0],
                    'Event Name': row[1],
                    'Satisfaction Score': float(row[2]) if row[2].replace('.', '').isdigit() else 0,
                    'Overall Average': float(row[3]) if row[3].replace('.', '').isdigit() else 0
                })
        df = pd.DataFrame(satisfaction)
        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df

    def process_most_popular_events(self) -> pd.DataFrame:
        raw_data = self.fetch_sheet_data('Most Popular Events')
        if raw_data and len(raw_data) > 1:
            events = []
            for i in range(1, len(raw_data)):
                row = raw_data[i]
                if len(row) >= 3:
                    events.append({
                        'Event Name': row[0],
                        'Total Participants': int(row[1]) if row[1].isdigit() else 0,
                        'Percentage Share': float(row[2]) if row[2].replace('.', '').isdigit() else 0
                    })
            return pd.DataFrame(events)
        # fallback
        participation_df = self.process_volunteer_participation_trends()
        if participation_df.empty:
            return pd.DataFrame(columns=['Event Name', 'Total Participants', 'Percentage Share'])
        event_counts = participation_df.groupby('Event Name')['Participant Count'].sum().reset_index()
        total = event_counts['Participant Count'].sum()
        if total > 0:
            event_counts['Percentage Share'] = (event_counts['Participant Count'] / total * 100).round(2)
        else:
            event_counts['Percentage Share'] = 0
        popular = event_counts.nlargest(3, 'Participant Count')
        popular.columns = ['Event Name', 'Total Participants', 'Percentage Share']
        return popular

    def process_acres_cleaned_timeline(self) -> pd.DataFrame:
        raw_data = self.fetch_sheet_data('Acres Cleaned Timeline')
        if not raw_data or len(raw_data) <= 1:
            return pd.DataFrame(columns=['Date', 'Acres Cleaned', 'Cumulative Total'])
        timeline = []
        cumulative = 0
        for i in range(1, len(raw_data)):
            row = raw_data[i]
            if len(row) >= 2:
                acres = float(row[1]) if row[1].replace('.', '').isdigit() else 0
                cumulative += acres
                timeline.append({'Date': row[0], 'Acres Cleaned': acres, 'Cumulative Total': cumulative})
        df = pd.DataFrame(timeline)
        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df

    def process_survey_response_details(self) -> pd.DataFrame:
        raw_data = self.fetch_sheet_data('Survey Response Details')
        if not raw_data or len(raw_data) <= 1:
            return pd.DataFrame(columns=['Date', 'Respondent ID', 'Organization', 'Barrier Statements', 'Park Visit Details', 'Accessibility Comments'])
        responses = []
        for i in range(1, len(raw_data)):
            row = raw_data[i]
            if len(row) >= 6:
                responses.append({
                    'Date': row[0], 'Respondent ID': row[1], 'Organization': row[2],
                    'Barrier Statements': row[3], 'Park Visit Details': row[4], 'Accessibility Comments': row[5]
                })
        df = pd.DataFrame(responses)
        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df

    def process_barrier_ratings(self) -> pd.DataFrame:
        raw_data = self.fetch_sheet_data('Barrier Ratings Over Time')
        if not raw_data or len(raw_data) <= 1:
            return pd.DataFrame(columns=['Date', 'Organization', 'Rating'])
        ratings = []
        for i in range(1, len(raw_data)):
            row = raw_data[i]
            if len(row) >= 3:
                ratings.append({'Date': row[0], 'Organization': row[1], 'Rating': float(row[2]) if row[2].replace('.', '').isdigit() else 0})
        df = pd.DataFrame(ratings)
        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df

    def calculate_dashboard_metrics(self) -> Dict[str, Any]:
        metrics: Dict[str, Any] = {}
        # Volunteer metrics
        part_df = self.process_volunteer_participation_trends()
        if not part_df.empty:
            metrics['total_volunteers'] = part_df['Participant Count'].sum()
            metrics['total_hours'] = part_df['Total Count'].sum()
            metrics['value_of_hours'] = metrics['total_hours'] * 13.2
        # Acres metrics
        acres_df = self.process_acres_cleaned_timeline()
        if not acres_df.empty:
            metrics['total_acres_cleaned'] = acres_df['Cumulative Total'].iloc[-1]
            metrics['percent_forest_reached'] = min(100, (metrics['total_acres_cleaned'] / 4000) * 100)
        # Survey metrics
        survey_df = self.process_survey_response_details()
        if not survey_df.empty:
            metrics['total_survey_responses'] = len(survey_df)
            barrier_count = sum('yes' in str(x).lower() for x in survey_df['Barrier Statements'])
            metrics['percent_facing_barriers'] = (barrier_count / len(survey_df) * 100) if len(survey_df) > 0 else 0
        # Barrier rating average
        barrier_df = self.process_barrier_ratings()
        if not barrier_df.empty:
            metrics['average_barrier_rating'] = barrier_df['Rating'].mean()
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
def get_data_processor(spreadsheet_id: str, api_key: str):
    return GoogleSheetsDataProcessor(spreadsheet_id, api_key)

# Sidebar Navigation
with st.sidebar:
    st.markdown("🌲 **Friends of Shelby**")
    st.markdown("### Data Configuration")

    # -- keep your Refresh Data button exactly where it was --
    if st.button("Refresh Data"):
        st.cache_data.clear()

    st.markdown('<div class="nav-section">', unsafe_allow_html=True)
    st.markdown("### Navigation")
    volunteer_selected = st.button("Volunteer Program",            key="nav1", use_container_width=True)
    forest_selected    = st.button("Restore The Forest Program",    key="nav2", use_container_width=True)
    strategic_selected = st.button("Strategic Plan - Pillar 1",     key="nav3", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### General Filters")
    st.selectbox("Date Range", ["Last Month", "Last 3 Months", "Last Year"], key="sidebar_date")
    st.selectbox("Organization", ["All", "ICLR", "Cerecore HCA"], key="sidebar_org")
    st.multiselect("Metrics to Show", ["Volunteers", "Hours", "Accessibility", "Satisfaction"], key="sidebar_metrics")

# Connect to Google Sheets or fallback
if not api_key:
    st.warning("Please enter your Google Sheets API key in the sidebar to load real data. Using sample data for now.")
    data_processor = None
else:
    try:
        data_processor = get_data_processor(spreadsheet_id, api_key)
        sheet_names = data_processor.get_sheet_names()
        if not sheet_names:
            st.error("Could not connect to Google Sheets. Please check your API key and spreadsheet ID.")
            data_processor = None
        else:
            st.success(f"Connected to Google Sheets! Found {len(sheet_names)} sheets")
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {str(e)}")
        data_processor = None

# Page state
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Volunteer Program"
if volunteer_selected:
    st.session_state.current_page = "Volunteer Program"
elif forest_selected:
    st.session_state.current_page = "Restore The Forest Program"
elif strategic_selected:
    st.session_state.current_page = "Strategic Plan - Pillar 1"
page = st.session_state.current_page

# Load data or fallback
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
    # Sample fallback
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
    st.markdown('<div class="component-separator">', unsafe_allow_html=True)
    col1, col2 = st.columns([6, 2])
    with col1:
        st.title("Friends of Shelby Dashboard")
        st.markdown("**Volunteer Program**")
    with col2:
        st.markdown("**Sefika Ozturk** - *Admin*")
    st.markdown('</div>', unsafe_allow_html=True)

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Total Volunteers</h4>
            <h2>{metrics.get('total_volunteers', 0):,}</h2>
            <small>+2,031</small>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card-light">
            <h4>Total Hours</h4>
            <h2>{metrics.get('total_hours', 0):,}</h2>
            <small>+3,390</small>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card-light">
            <h4>Value of The Hours</h4>
            <h2>${metrics.get('value_of_hours', 0):,.2f}</h2>
            <small>+$23,456</small>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card-light">
            <h4>Change fr. Last Year</h4>
            <h2>12.8%</h2>
            <small>↑ 2.2%</small>
        </div>
        """, unsafe_allow_html=True)

    # Charts row
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Volunteer Participation Trends Over Time" )
        if not participation_df.empty:
            fig = go.Figure()
            for ev in participation_df['Event Name'].unique():
                d = participation_df[participation_df['Event Name']==ev]
                fig.add_trace(go.Scatter(x=d['Date'], y=d['Participant Count'], mode='lines+markers', name=ev))
        else:
            months = ['Jan','Feb','Mar','Apr','May']
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=months,y=[45,55,65,45,35],name='Invasive Removal'))
        fig.update_layout(plot_bgcolor='white',paper_bgcolor='white',height=400)
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        st.subheader("Popular Events")
        if not popular_events_df.empty:
            fig2 = go.Figure(data=[go.Pie(labels=popular_events_df['Event Name'][:3], values=popular_events_df['Total Participants'][:3], hole=0.5)])
        else:
            fig2 = go.Figure()
        fig2.update_layout(height=400)
        st.plotly_chart(fig2,use_container_width=True)

    # Satisfaction section
    st.subheader("Volunteer Satisfaction")
    if not satisfaction_df.empty:
        fig3 = px.bar(satisfaction_df, x='Event Name', y='Satisfaction Score', color='Event Name')
        fig3.update_layout(plot_bgcolor='white',paper_bgcolor='white',height=400)
        st.plotly_chart(fig3,use_container_width=True)
    else:
        st.write("No satisfaction data.")

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

    # Metrics row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
    <div class="metric-card">
        <h4>Acres Cleaned</h4>
        <h2>{metrics.get('total_acres_cleaned', 0):,}</h2>
        <small>Cumulative acres cleaned</small>
    </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
    <div class="metric-card-light">
        <h4>% of Forest Reached</h4>
        <h2>{metrics.get('percent_forest_reached', 0):.0f}%</h2>
        <small>Area % of the forest</small>
    </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
    <div class="metric-card-light">
        <h4>Volunteers</h4>
        <h2>{metrics.get('total_volunteers', 0):,}</h2>
        <small>Participating volunteers</small>
    </div>
        """, unsafe_allow_html=True)

    # Charts row
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Acres Cleaned Over Time")
        if not acres_df.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=acres_df['Date'], y=acres_df['Acres Cleaned'], mode='lines+markers'))
            fig.update_layout(plot_bgcolor='white',paper_bgcolor='white',height=400)
            st.plotly_chart(fig,use_container_width=True)
        else:
            st.write("No acres data.")
    with col2:
        st.subheader("Barrier Ratings Over Time")
        if not barrier_ratings_df.empty:
            fig4 = go.Figure()
            for org in barrier_ratings_df['Organization'].unique():
                d = barrier_ratings_df[barrier_ratings_df['Organization']==org]
                fig4.add_trace(go.Scatter(x=d['Date'], y=d['Rating'], mode='lines+markers', name=org))
            fig4.update_layout(plot_bgcolor='white',paper_bgcolor='white',height=400)
            st.plotly_chart(fig4,use_container_width=True)
        else:
            st.write("No barrier rating data.")

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

    # Survey metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Survey Responses", value=f"{metrics.get('total_survey_responses', 0)}")
    with col2:
        st.metric(label="% Facing Barriers", value=f"{metrics.get('percent_facing_barriers', 0):.1f}%")

    # Survey details table
    st.subheader("Survey Response Details")
    if not survey_df.empty:
        st.dataframe(survey_df)
    else:
        st.write("No survey data available.")

    # Accessibility ratings chart
    st.subheader("Barrier Ratings Over Time")
    if not barrier_ratings_df.empty:
        fig5 = go.Figure()
        for org in barrier_ratings_df['Organization'].unique():
            d = barrier_ratings_df[barrier_ratings_df['Organization']==org]
            fig5.add_trace(go.Scatter(x=d['Date'], y=d['Rating'], mode='lines+markers', name=org))
        fig5.update_layout(plot_bgcolor='white',paper_bgcolor='white',yaxis=dict(range=[0,100]),height=400)
        st.plotly_chart(fig5,use_container_width=True)
    else:
        st.write("No barrier rating data.")
