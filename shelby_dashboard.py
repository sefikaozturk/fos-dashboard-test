import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Any
import json

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
    
    def process_dashboard_data(self) -> Dict[str, Any]:
        """Process raw data into structured format for Dashboard"""
        dashboard_data = {
            'single_value_metrics': {},
            'chart_data': {}
        }
        
        try:
            # Fetch volunteer participation data
            volunteer_data = self.fetch_sheet_data('Volunteer Data')
            if volunteer_data:
                dashboard_data['single_value_metrics']['total_volunteers'] = self.calculate_total_volunteers(volunteer_data)
                dashboard_data['single_value_metrics']['total_hours'] = self.calculate_total_hours(volunteer_data)
            
            # Fetch acres cleaned data
            acres_data = self.fetch_sheet_data('Acres Cleaned')
            if acres_data:
                dashboard_data['single_value_metrics']['total_acres_cleaned'] = self.calculate_total_acres(acres_data)
            
            # Fetch survey data
            survey_data = self.fetch_sheet_data('Survey Responses')
            if survey_data:
                dashboard_data['single_value_metrics']['total_survey_responses'] = max(0, len(survey_data) - 1)
                dashboard_data['single_value_metrics']['percent_facing_barriers'] = self.calculate_barrier_percentage(survey_data)
            
            return dashboard_data
        except Exception as e:
            st.error(f"Error processing dashboard data: {str(e)}")
            return dashboard_data
    
    def process_volunteer_participation_trends(self) -> pd.DataFrame:
        """Process Volunteer Participation Trends"""
        raw_data = self.fetch_sheet_data('Volunteer Data')
        
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
        raw_data = self.fetch_sheet_data('Satisfaction Data')
        
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
        participation_df = self.process_volunteer_participation_trends()
        
        if participation_df.empty:
            return pd.DataFrame(columns=['Event Name', 'Total Participants', 'Percentage Share'])
        
        # Aggregate participation by event
        event_counts = participation_df.groupby('Event Name')['Participant Count'].sum().reset_index()
        total_participants = event_counts['Participant Count'].sum()
        
        if total_participants > 0:
            event_counts['Percentage Share'] = (event_counts['Participant Count'] / total_participants * 100).round(2)
        else:
            event_counts['Percentage Share'] = 0
        
        # Get top 3 events
        popular_events = event_counts.nlargest(3, 'Participant Count')
        popular_events.columns = ['Event Name', 'Total Participants', 'Percentage Share']
        
        return popular_events
    
    def process_acres_cleaned_timeline(self) -> pd.DataFrame:
        """Process Acres Cleaned Timeline"""
        raw_data = self.fetch_sheet_data('Acres Cleaned')
        
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
            # Filter to last 3 years
            three_years_ago = datetime.now() - timedelta(days=3*365)
            df = df[df['Date'] >= three_years_ago]
        
        return df
    
    def process_monthly_acres_cleaned(self) -> pd.DataFrame:
        """Process Monthly Acres Cleaned Data"""
        timeline_df = self.process_acres_cleaned_timeline()
        
        if timeline_df.empty:
            return pd.DataFrame(columns=['Month', 'Year', 'Acres'])
        
        # Group by month and year
        timeline_df['YearMonth'] = timeline_df['Date'].dt.to_period('M')
        monthly_data = timeline_df.groupby('YearMonth')['Acres Cleaned'].sum().reset_index()
        
        # Get last 7 months
        monthly_data = monthly_data.tail(7)
        monthly_data['Month'] = monthly_data['YearMonth'].dt.month
        monthly_data['Year'] = monthly_data['YearMonth'].dt.year
        monthly_data['Acres'] = monthly_data['Acres Cleaned']
        
        return monthly_data[['Month', 'Year', 'Acres']]
    
    def process_survey_response_details(self) -> pd.DataFrame:
        """Process Survey Response Details (Qualitative Data)"""
        raw_data = self.fetch_sheet_data('Survey Details')
        
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
    
    # Helper functions
    def calculate_total_volunteers(self, data: List[List[str]]) -> int:
        if not data or len(data) <= 1:
            return 0
        unique_volunteers = set()
        for i in range(1, len(data)):
            if len(data[i]) > 1 and data[i][1]:
                unique_volunteers.add(data[i][1])
        return len(unique_volunteers)
    
    def calculate_total_hours(self, data: List[List[str]]) -> float:
        if not data or len(data) <= 1:
            return 0
        total_hours = 0
        for i in range(1, len(data)):
            if len(data[i]) > 2 and data[i][2]:
                try:
                    total_hours += float(data[i][2])
                except ValueError:
                    continue
        return total_hours
    
    def calculate_total_acres(self, data: List[List[str]]) -> float:
        if not data or len(data) <= 1:
            return 0
        total_acres = 0
        for i in range(1, len(data)):
            if len(data[i]) > 1 and data[i][1]:
                try:
                    total_acres += float(data[i][1])
                except ValueError:
                    continue
        return total_acres
    
    def calculate_barrier_percentage(self, data: List[List[str]]) -> float:
        if not data or len(data) <= 1:
            return 0
        facing_barriers = 0
        total_responses = len(data) - 1
        
        for i in range(1, len(data)):
            if len(data[i]) > 3 and data[i][3] and 'yes' in data[i][3].lower():
                facing_barriers += 1
        
        return round((facing_barriers / total_responses * 100), 2) if total_responses > 0 else 0

def main():
    st.set_page_config(
        page_title="Forest Conservation Dashboard",
        page_icon="🌲",
        layout="wide"
    )
    
    st.title("🌲 Forest Conservation Dashboard")
    st.markdown("---")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Default spreadsheet ID from the URL
        default_spreadsheet_id = "1OgP1vp1OjiRgtisNrHoHxPIPbRxGjKtcegCS7ztVPr0"
        spreadsheet_id = st.text_input("Spreadsheet ID", value=default_spreadsheet_id)
        
        api_key = st.text_input("Google Sheets API Key", type="password", help="Enter your Google Sheets API key")
        
        if st.button("Refresh Data"):
            st.cache_data.clear()
    
    if not api_key:
        st.warning("Please enter your Google Sheets API key in the sidebar to proceed.")
        st.info("""
        To get a Google Sheets API key:
        1. Go to Google Cloud Console
        2. Enable the Google Sheets API
        3. Create credentials and get your API key
        4. Enter the key in the sidebar
        """)
        return
    
    # Initialize the processor
    processor = GoogleSheetsDataProcessor(spreadsheet_id, api_key)
    
    # Test connection
    with st.spinner("Testing connection to Google Sheets..."):
        sheet_names = processor.get_sheet_names()
    
    if not sheet_names:
        st.error("Could not connect to Google Sheets. Please check your API key and spreadsheet ID.")
        return
    
    st.success(f"Connected! Found {len(sheet_names)} sheets")
    
    # Dashboard Overview
    st.header("📊 Dashboard Overview")
    
    with st.spinner("Loading dashboard metrics..."):
        dashboard_data = processor.process_dashboard_data()
    
    # Display single value metrics
    col1, col2, col3, col4 = st.columns(4)
    
    metrics = dashboard_data.get('single_value_metrics', {})
    
    with col1:
        st.metric("Total Volunteers", metrics.get('total_volunteers', 0))
    
    with col2:
        st.metric("Total Hours", f"{metrics.get('total_hours', 0):.1f}")
    
    with col3:
        st.metric("Total Acres Cleaned", f"{metrics.get('total_acres_cleaned', 0):.2f}")
    
    with col4:
        st.metric("Survey Responses", metrics.get('total_survey_responses', 0))
    
    # Additional metrics row
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.metric("% Facing Barriers", f"{metrics.get('percent_facing_barriers', 0)}%")
    
    st.markdown("---")
    
    # Tabs for different data views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Participation Trends", 
        "⭐ Popular Events", 
        "🌍 Acres Cleaned", 
        "📝 Survey Data",
        "🔍 Raw Data"
    ])
    
    with tab1:
        st.subheader("Volunteer Participation Trends")
        
        with st.spinner("Loading participation data..."):
            participation_df = processor.process_volunteer_participation_trends()
        
        if not participation_df.empty:
            # Line chart for participation trends
            fig = px.line(participation_df, x='Date', y='Participant Count', 
                         color='Event Name', title='Volunteer Participation Over Time')
            st.plotly_chart(fig, use_container_width=True)
            
            # Data table
            st.subheader("Participation Data")
            st.dataframe(participation_df, use_container_width=True)
        else:
            st.info("No participation data available")
        
        # Satisfaction data
        st.subheader("Volunteer Satisfaction")
        satisfaction_df = processor.process_volunteer_satisfaction()
        
        if not satisfaction_df.empty:
            fig_sat = px.bar(satisfaction_df, x='Event Name', y='Satisfaction Score',
                           title='Volunteer Satisfaction by Event')
            st.plotly_chart(fig_sat, use_container_width=True)
            st.dataframe(satisfaction_df, use_container_width=True)
        else:
            st.info("No satisfaction data available")
    
    with tab2:
        st.subheader("Most Popular Events")
        
        popular_events_df = processor.process_most_popular_events()
        
        if not popular_events_df.empty:
            # Pie chart for popular events
            fig_pie = px.pie(popular_events_df, values='Total Participants', names='Event Name',
                           title='Distribution of Participants by Event')
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # Bar chart
            fig_bar = px.bar(popular_events_df, x='Event Name', y='Total Participants',
                           title='Top 3 Most Popular Events')
            st.plotly_chart(fig_bar, use_container_width=True)
            
            st.dataframe(popular_events_df, use_container_width=True)
        else:
            st.info("No event data available")
    
    with tab3:
        st.subheader("Acres Cleaned Analysis")
        
        # Timeline data
        acres_timeline_df = processor.process_acres_cleaned_timeline()
        
        if not acres_timeline_df.empty:
            # Cumulative acres cleaned over time
            fig_acres = px.line(acres_timeline_df, x='Date', y='Cumulative Total',
                              title='Cumulative Acres Cleaned Over Time')
            st.plotly_chart(fig_acres, use_container_width=True)
            
            # Monthly breakdown
            monthly_acres_df = processor.process_monthly_acres_cleaned()
            
            if not monthly_acres_df.empty:
                fig_monthly = px.bar(monthly_acres_df, x='Month', y='Acres',
                                   title='Monthly Acres Cleaned (Last 7 Months)')
                st.plotly_chart(fig_monthly, use_container_width=True)
            
            st.dataframe(acres_timeline_df, use_container_width=True)
        else:
            st.info("No acres cleaned data available")
    
    with tab4:
        st.subheader("Survey Response Details")
        
        survey_details_df = processor.process_survey_response_details()
        
        if not survey_details_df.empty:
            # Filter options
            col1, col2 = st.columns(2)
            
            with col1:
                selected_org = st.selectbox("Filter by Organization", 
                                          ["All"] + list(survey_details_df['Organization'].unique()))
            
            with col2:
                date_range = st.date_input("Filter by Date Range", 
                                         value=(survey_details_df['Date'].min().date(), 
                                               survey_details_df['Date'].max().date()),
                                         min_value=survey_details_df['Date'].min().date(),
                                         max_value=survey_details_df['Date'].max().date())
            
            # Apply filters
            filtered_df = survey_details_df.copy()
            
            if selected_org != "All":
                filtered_df = filtered_df[filtered_df['Organization'] == selected_org]
            
            if len(date_range) == 2:
                filtered_df = filtered_df[
                    (filtered_df['Date'].dt.date >= date_range[0]) & 
                    (filtered_df['Date'].dt.date <= date_range[1])
                ]
            
            st.dataframe(filtered_df, use_container_width=True)
            
            # Summary statistics
            st.subheader("Survey Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Responses", len(filtered_df))
            
            with col2:
                st.metric("Unique Organizations", filtered_df['Organization'].nunique())
            
            with col3:
                barrier_responses = len([x for x in filtered_df['Barrier Statements'] if x and len(x.strip()) > 0])
                st.metric("Responses with Barriers", barrier_responses)
        else:
            st.info("No survey data available")
    
    with tab5:
        st.subheader("Available Sheets")
        st.write("Sheets found in the spreadsheet:")
        
        for i, sheet_name in enumerate(sheet_names, 1):
            st.write(f"{i}. {sheet_name}")
        
        # Raw data viewer
        selected_sheet = st.selectbox("Select a sheet to view raw data:", sheet_names)
        
        if st.button("Load Raw Data"):
            with st.spinner(f"Loading data from {selected_sheet}..."):
                raw_data = processor.fetch_sheet_data(selected_sheet)
            
            if raw_data:
                df_raw = pd.DataFrame(raw_data)
                st.dataframe(df_raw, use_container_width=True)
                st.info(f"Loaded {len(raw_data)} rows from {selected_sheet}")
            else:
                st.warning(f"No data found in {selected_sheet}")

if __name__ == "__main__":
    main()
