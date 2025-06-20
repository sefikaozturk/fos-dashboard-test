import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import time
from typing import Dict, Any

class GoogleSheetsDataProcessor:
    def __init__(self, spreadsheet_id: str, api_key: str):
        self.spreadsheet_id = spreadsheet_id
        self.api_key        = api_key
        # no more batchGet here!
    
    @st.cache_data(ttl=3600)            # cache each sheet for 1 hour
    def fetch_sheet_data(_self, sheet_name: str):
        from urllib.parse import quote
        encoded = quote(sheet_name, safe='')
        url     = f"https://sheets.googleapis.com/v4/spreadsheets/{_self.spreadsheet_id}/values/{encoded}"
        params  = {'key': _self.api_key}

        # simple retry/backoff for 429s
        for i in range(3):
            resp = requests.get(url, params=params)
            if resp.status_code == 429:
                time.sleep(2 ** i)
                continue
            resp.raise_for_status()
            return resp.json().get('values', [])
        # if we still 429 after 3 tries, let it bubble
        resp.raise_for_status()
    
    def get_sheet_names(self):
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{self.spreadsheet_id}?fields=sheets.properties.title&key={self.api_key}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            sheets = response.json().get('sheets', [])
            return [s['properties']['title'] for s in sheets]
        except requests.exceptions.HTTPError as e:
            st.error(f"Error fetching sheet names: {e}")
            return []

    def process_volunteer_participation_trends(self) -> pd.DataFrame:
        raw = self.fetch_sheet_data('Volunteer Participation Trends')
        if len(raw) <= 1:
            return pd.DataFrame(columns=['Date','Event Name','Participant Count','Hours'])
        df = pd.DataFrame(raw[1:], columns=raw[0])
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Participant Count'] = pd.to_numeric(df['Participant Count'], errors='coerce').fillna(0).astype(int)
        df['Hours'] = pd.to_numeric(df['Hours'], errors='coerce').fillna(0).astype(int)
        return df.sort_values('Date')

    def process_most_popular_events(self) -> pd.DataFrame:
        raw = self.fetch_sheet_data('Most Popular Events')
        if len(raw) <= 1:
            return pd.DataFrame(columns=['Event Name','Participant Count'])
        df = pd.DataFrame(raw[1:], columns=raw[0])
        df['Participant Count'] = pd.to_numeric(df['Participant Count'], errors='coerce').fillna(0).astype(int)
        return df

    def process_volunteer_satisfaction(self) -> pd.DataFrame:
        raw = self.fetch_sheet_data('Volunteer Satisfaction')
        if len(raw) <= 1:
            return pd.DataFrame(columns=['Event Name','Satisfaction Score'])
        df = pd.DataFrame(raw[1:], columns=raw[0])
        df['Satisfaction Score'] = pd.to_numeric(df['Satisfaction Score'], errors='coerce').fillna(0)
        return df

    def process_acres_cleaned_timeline(self) -> pd.DataFrame:
        raw = self.fetch_sheet_data('Acres Cleaned Timeline')
        if len(raw) <= 1:
            return pd.DataFrame(columns=['Date','Acres Cleaned','Cumulative Total'])
        df = pd.DataFrame(raw[1:], columns=raw[0])
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Acres Cleaned'] = pd.to_numeric(df['Acres Cleaned'], errors='coerce').fillna(0)
        df['Cumulative Total'] = pd.to_numeric(df['Cumulative Total'], errors='coerce').fillna(0)
        return df.sort_values('Date')

    def process_survey_response_details(self) -> pd.DataFrame:
        raw = self.fetch_sheet_data('Survey Response Details')
        if len(raw) <= 1:
            return pd.DataFrame(columns=raw[0] if raw else [])
        return pd.DataFrame(raw[1:], columns=raw[0])

    def process_barrier_ratings(self) -> pd.DataFrame:
        raw = self.fetch_sheet_data('Barrier Ratings Over Time')
        if len(raw) <= 1:
            return pd.DataFrame(columns=['Date','Organization Name',' Barrier Rating'])
        df = pd.DataFrame(raw[1:], columns=raw[0])
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Rating'] = pd.to_numeric(df['Barrier Rating'], errors='coerce').fillna(0)
        return df.sort_values('Date')
    
    def _make_df(self, raw: list[list]) -> pd.DataFrame:
        """
        Safely turns a raw API list-of-lists into a DataFrame,
        allowing rows with missing cells to become NaN instead of erroring.
        """
        if len(raw) <= 1:
            # no data → empty DF with the header columns (or no columns if even header is missing)
            return pd.DataFrame(columns=raw[0] if raw else [])
        header = raw[0]
        # zip will pair only up to the shorter of header vs row, leaving missing cells as NaN
        records = [dict(zip(header, row)) for row in raw[1:]]
        return pd.DataFrame.from_records(records, columns=header)

    def process_diy_google_form_log(self) -> pd.DataFrame:
        raw = self.fetch_sheet_data("DIY Volunteers Check-in")
        df  = self._make_df(raw)
        if df.empty: 
            return df
        # parse and sort
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        return df.sort_values("Date", ascending=False)

    def process_wildspotter_log(self) -> pd.DataFrame:
        raw = self.fetch_sheet_data("WildSpotter Submissions")
        df  = self._make_df(raw)
        if df.empty:
            return df
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        return df.sort_values("Date", ascending=False)
    
    def process_accessibility_ratings(self) -> pd.DataFrame:
        raw = self.fetch_sheet_data('Park Accessibility Ratings')
        if len(raw) <= 1:
            return pd.DataFrame(columns=['Date','Organization','Rating'])
        df = self._make_df(raw)
        df['Date']     = pd.to_datetime(df['Date'], errors='coerce')
        df['Rating']   = pd.to_numeric(df['Rating'], errors='coerce').fillna(0)
        return df[['Date','Organization','Rating']].sort_values('Date')

    def process_park_visit_ratings(self) -> pd.DataFrame:
        raw = self.fetch_sheet_data('Park Visits Data')
        if len(raw) <= 1:
            return pd.DataFrame(columns=['Date','Organization','Visits'])
        df = self._make_df(raw)
        df['Date']     = pd.to_datetime(df['Date'], errors='coerce')
        df['Visits']   = pd.to_numeric(df['Visits'], errors='coerce').fillna(0)
        return df[['Date','Organization','Visits']].sort_values('Date')

    def calculate_dashboard_metrics(self) -> Dict[str, Any]:
        metrics: Dict[str, Any] = {}
        df = self.process_volunteer_participation_trends()
        if 'Date' in df and not df.empty:
            current_year = pd.Timestamp.now().year
            this = df[df['Date'].dt.year == current_year]
            last = df[df['Date'].dt.year == current_year-1]
            metrics['total_volunteers'] = this['Participant Count'].sum()
            metrics['volunteers_change'] = metrics['total_volunteers'] - 0 #last['Participant Count'].sum()
            metrics['total_hours'] = this['Hours'].sum()
            metrics['hours_change'] = metrics['total_hours'] - last['Hours'].sum()
            metrics['value_of_hours'] = metrics['total_hours'] * 13.2
        acres = self.process_acres_cleaned_timeline()
        if 'Cumulative Total' in acres and not acres.empty:
            metrics['total_acres_cleaned'] = acres['Cumulative Total'].iloc[-1]
            metrics['percent_forest_reached'] = min(100, (metrics['total_acres_cleaned']/4000)*100)
        survey = self.process_survey_response_details()
        if not survey.empty:
            metrics['total_survey_responses'] = len(survey)
            if 'Barrier Statements' in survey:
                barrier_count = survey['Barrier Statements'].str.contains('yes', case=False, na=False).sum()
                metrics['percent_facing_barriers'] = (barrier_count/len(survey)*100)
        br = self.process_barrier_ratings()
        if 'Rating' in br and not br.empty:
            metrics['average_barrier_rating'] = br['Rating'].mean()
        return metrics
    
# Page config
st.set_page_config(
    page_title="Friends of Shelby Dashboard",
    page_icon="🌲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to match the design
st.markdown("""
<style>
.main > div {
    padding-top: 2rem;
}
/* Optimized KPI card styling - reduced padding and height */
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
/* Component separation styling */
.component-separator {
    margin: 1rem 0;
    #border-bottom: 1px solid #e1e5e9;
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
/* Sidebar navigation styling */
.nav-section {
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e1e5e9;
}
/* Reduce gap between columns */
.block-container {
    padding-top: 1rem;
}
/* Tighter spacing for metric cards */
div[data-testid="column"] {
    padding: 0 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation
with st.sidebar:
    # Add Friends of Shelby title at the top
    st.markdown("🌲 **Friends of Shelby**")
    st.markdown('<div class="nav-section">', unsafe_allow_html=True)
    st.markdown("### Navigation")
    
    # Navigation buttons in sidebar
    volunteer_selected = st.button("Volunteer Program", key="nav1", use_container_width=True)
    forest_selected = st.button("Restore The Forest Program", key="nav2", use_container_width=True)
    strategic_selected = st.button("Strategic Plan - Pillar 1", key="nav3", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Filters section
    st.markdown("### General Filters")
    st.selectbox("Date Range", ["Last Month", "Last 3 Months", "Last Year"], key="sidebar_date")
    st.selectbox("Organization", ["All", "ICLR", "Cerecore HCA"], key="sidebar_org")
    st.multiselect("Metrics to Show", ["Volunteers", "Hours", "Accessibility", "Satisfaction"], key="sidebar_metrics")
    
    # Data refresh button
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Load credentials from secrets
try:
    spreadsheet_id = st.secrets["SPREADSHEET_ID"]
    api_key = st.secrets["GOOGLE_SHEETS_API_KEY"]
except Exception:
    st.error("Missing Google Sheets credentials. Please add 'spreadsheet_id' and 'api_key' under [google_sheets] in your secrets.toml.")
    st.stop()

# Data retrieval
proc = GoogleSheetsDataProcessor(spreadsheet_id, api_key)
try:
    snames = proc.get_sheet_names()
    st.success(f"Connected: {len(snames)} sheets")

    time.sleep(1)
    metrics = proc.calculate_dashboard_metrics()
    part_df = proc.process_volunteer_participation_trends()
    pop_df  = proc.process_most_popular_events()
    sat_df  = proc.process_volunteer_satisfaction()
    acres_df = proc.process_acres_cleaned_timeline()
    surv_df = proc.process_survey_response_details()
    br_df   = proc.process_barrier_ratings()
    diy_df  = proc.process_diy_google_form_log()
    ws_df   = proc.process_wildspotter_log()
    acc_df = proc.process_accessibility_ratings()
    pv_df = proc.process_park_visit_ratings()

    page = "Volunteer Program" if volunteer_btn else ("Restore The Forest Program" if forest_btn else "Strategic Plan")

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
        
        # Top metrics row with REAL DATA
        col1, col2, col3, col4 = st.columns(4)
    
        with col1:
            with st.container():
                st.markdown(f"""
                <div style="background: #4a4a4a; color: white; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center;">
                    <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Total Volunteers</div>
                    <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{f"{metrics.get('total_volunteers',0):,}"}</div>
                    <div style="font-size: 0.72rem; opacity: 0.8;">delta=f"{metrics.get('volunteers_change',0):+,}</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            with st.container():
                st.markdown(f"""
                <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
                    <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Total Hours</div>
                    <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{f"{metrics.get('total_hours',0):,}"}</div>
                    <div style="font-size: 0.72rem; opacity: 0.8;">delta=f"{metrics.get('hours_change',0):+,}</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            with st.container():
                st.markdown(f"""
                <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
                    <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Value of The Hours</div>
                    <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">${0:,.2f}</div>
                    <div style="font-size: 0.72rem; opacity: 0.8;">Real Data</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col4:
            change_display = f"{0}%" if 0 != 0 else "No Change"
            with st.container():
                st.markdown(f"""
                <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
                    <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Change fr. Last Year</div>
                    <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{0}</div>
                    <div style="font-size: 0.72rem; opacity: 0.8;">Real Data</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Charts row with proper containers (keeping sample data for visualization)
        col1, col2 = st.columns([2, 1])

        with col1:
            chart_container = st.container(border=True)
            with chart_container:
                if not part_df.empty:
                    # 1) Compute the daily total
                    daily = (
                        part_df
                        .groupby("Date")["Participant Count"]
                        .sum()
                        .reset_index()
                        .sort_values("Date")
                    )

                    # 2) Build a combined figure
                    fig = go.Figure()

                    # 3) One trace per event
                    for event_name, grp in part_df.groupby("Event Name"):
                        fig.add_trace(go.Scatter(
                            x=grp["Date"],
                            y=grp["Participant Count"],
                            mode="lines+markers",
                            name=event_name,
                            legendgroup=event_name,
                        ))

                    # 4) A bold trace for the total
                    fig.add_trace(go.Scatter(
                        x=daily["Date"],
                        y=daily["Participant Count"],
                        mode="lines+markers",
                        name="Total",
                        line=dict(color="black", width=4),
                        legendgroup="Total",
                    ))

                    # 5) Set x-axis range to start from the first date and end at the last date of the data
                    fig.update_layout(
                        xaxis_range=[daily["Date"].min(), daily["Date"].max()],
                        xaxis_title='Date',
                        yaxis_title='Number of Participants',
                        title='Participation Trends (per event + overall)',
                    )

                    # Display the figure
                    st.plotly_chart(fig)

                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.write("No participation data available.")

            
        with col2:
            chart_container = st.container(border=True)
            with chart_container:
                st.subheader("Popular Events")
                if not pop_df.empty:
                    # ─── pie chart instead of bar ───
                    fig = px.pie(
                        pop_df,
                        names='Event Name',
                        values='Participant Count',
                        title="Most Popular Events (by Participation)",
                        hole=0.3                       # optional: gives you a donut instead of full pie
                    )
                    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.write("No event data available.")
        
        # Bottom section - Combined container for chart and filters
        chart_container = st.container(border=True)
        with chart_container:
            # Create columns within the same container
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader("Volunteer Satisfaction")
                if not sat_df.empty:
                    # 1) compute per-event averages
                    avg = sat_df.groupby('Event Name')['Satisfaction Score'] \
                                .mean() \
                                .reset_index()

                    # 2) build the bar chart
                    fig = px.bar(
                        avg,
                        x='Event Name',
                        y='Satisfaction Score',
                        color='Event Name',
                        title="Volunteer Satisfaction by Event"
                    )

                    # 3) tighten the y-axis to just your scores ± a sliver of padding
                    min_score = avg['Satisfaction Score'].min()
                    max_score = avg['Satisfaction Score'].max()
                    padding   = (max_score - min_score) * 0.1  # 10% of the range
                    fig.update_yaxes(range=[min_score - padding, max_score + padding])

                    # 4) render
                    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                else:
                    st.write("No volunteer satisfaction data available.")
                
            
            with col2:
                st.markdown("### Filters")
                st.selectbox("Pick date", ["Overall"])
                st.selectbox("Pick organization", ["Overall"])
                st.checkbox("Show multiple")


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
        
        # Top metrics with REAL DATA
        col1, col2, col3 = st.columns(3)
        
        with col1:
            with st.container():
                st.markdown(f"""
                <div style="background: #4a4a4a; color: white; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center;">
                    <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Acres Cleaned</div>
                    <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{f"{metrics.get('total_acres_cleaned',0):,}":.2f}</div>
                    <div style="font-size: 0.72rem; opacity: 0.8;">Real Data - Current Total</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            with st.container():
                st.markdown(f"""
                <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
                    <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">% of Forest Reached</div>
                    <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{f"{metrics.get('percent_forest_reached',0):.0f}%"}%</div>
                    <div style="font-size: 0.72rem; opacity: 0.8;">Real Data - Forest Coverage</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            with st.container():
                st.markdown(f"""
                <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
                    <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">RTF Volunteers</div>
                    <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{f"{rtf}"}</div>
                    <div style="font-size: 0.72rem; opacity: 0.8;">Real Data - Active Volunteers</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Charts row with proper containers
        col1, col2 = st.columns([2, 1])

        with col1:
            chart_container = st.container(border=True)
            with chart_container:
                st.subheader("Acres Cleaned Over Time")
                
                if not acres_df.empty:
                    fig = go.Figure()
                    # incremental acres cleaned each date
                    fig.add_trace(go.Scatter(
                        x=acres_df['Date'], 
                        y=acres_df['Acres Cleaned'], 
                        mode='lines+markers', 
                        name='Acres Cleaned'
                    ))
                    # cumulative total
                    fig.add_trace(go.Scatter(
                        x=acres_df['Date'], 
                        y=acres_df['Cumulative Total'], 
                        mode='lines+markers', 
                        name='Cumulative Total'
                    ))
                    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.write("No acres-cleaned data available.")

        with col2:
            chart_container = st.container(border=True)
            with chart_container:
                st.subheader("Acres Cleaned per Month")
                
                # TODO: I need code for this. I currently only have a placeholder
                if not acres_df.empty:
                    fig = go.Figure()
                    # incremental acres cleaned each date
                    fig.add_trace(go.Bar(
                        x=acres_df['Date'], 
                        y=acres_df['Acres Cleaned'], 
                        name='Acres Cleaned',
                        marker_color='#d5b895'
                    ))
                    # cumulative total
                    fig.add_trace(go.Scatter(
                        x=acres_df['Date'], 
                        y=acres_df['Cumulative Total'], 
                        name='Cumulative Total'
                    ))
                    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.write("No acres-cleaned data available.")
        
        # Bottom section - Logs with proper containers
        col1, col2 = st.columns(2)
            
        with col1:
            log_container = st.container(border=True)
            with log_container:
                st.subheader("DIY Volunteers Check-in Log")
                if not diy_df.empty:
                    st.dataframe(diy_df)   # interactive table
                else:
                    st.write("No check-in entries found.")
        
        with col2:
            log_container = st.container(border=True)
            with log_container:
                st.subheader("WildSpotter Submissions")
                if not ws_df.empty:
                    st.dataframe(ws_df)
                else:
                    st.write("No WildSpotter submissions found.")

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
        
        # Top metrics with REAL DATA
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            with st.container():
                st.markdown(f"""
                <div style="background: #4a4a4a; color: white; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center;">
                    <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Total Responses</div>
                    <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{f"{metrics.get('total_survey_responses',0)}"}</div>
                    <div style="font-size: 0.72rem; opacity: 0.8;">Real Data</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            with st.container():
                st.markdown(f"""
                <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
                    <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">% Facing Barriers</div>
                    <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">{f"{metrics.get('percent_facing_barriers',0):.1f}%"}%</div>
                    <div style="font-size: 0.72rem; opacity: 0.8;">Real Data</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            with st.container():
                st.markdown(f"""
                <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
                    <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Accessibility</div>
                    <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">+{0}%</div>
                    <div style="font-size: 0.72rem; opacity: 0.8;">Real Data</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col4:
            with st.container():
                st.markdown(f"""
                <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
                    <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Park Visits</div>
                    <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">+{0}%</div>
                    <div style="font-size: 0.72rem; opacity: 0.8;">↑ 2.2%</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Main chart with proper container
        col1, col2 = st.columns([3, 1])

        # Main chart with filters in same container
        chart_container = st.container(border=True)
        with chart_container:
            # Create columns within the same container
            col1, col2 = st.columns([3, 1])
            
            st.subheader("Survey Details")
            if not surv_df.empty:
                st.dataframe(surv_df)
            else:
                st.write("No survey details available.")

            choice = st.radio("Select Chart", ["Barrier","Accessibility","Park Visits"], horizontal=True)

            if choice == "Barrier":
                # your existing barrier code
                if not br_df.empty:
                    fig = px.line(
                        br_df, x="Date", y="Rating", color="Organization",
                        markers=True, title="Barrier Ratings Over Time"
                    )
                    fig.update_layout(yaxis=dict(range=[0, br_df['Rating'].max()*1.1]))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write("No barrier rating data.")

            elif choice == "Accessibility":
                # 1) grab all orgs
                orgs = sorted(acc_df['Organization'].unique())
                # 2) let user pick
                sel = st.multiselect(
                    "Filter by organization", 
                    options=orgs, 
                    default=orgs,
                    key="accessibility_orgs"
                )
                # 3) filter
                plot_df = acc_df[acc_df['Organization'].isin(sel)]
                # 4) draw
                if not plot_df.empty:
                    fig = px.line(
                        plot_df, x="Date", y="Rating", color="Organization",
                        markers=True, title="Accessibility Ratings Over Time"
                    )
                    fig.update_layout(legend_title_text="Organization")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write("No accessibility rating data for that selection.")

            else:  # Park Visits
                orgs = sorted(pv_df['Organization'].unique())
                sel = st.multiselect(
                    "Filter by organization", 
                    options=orgs, 
                    default=orgs,
                    key="parkvisits_orgs"
                )
                plot_df = pv_df[pv_df['Organization'].isin(sel)]
                if not plot_df.empty:
                    fig = px.line(
                        plot_df, x="Date", y="Visits", color="Organization",
                        markers=True, title="Park Visit Ratings Over Time"
                    )
                    fig.update_layout(legend_title_text="Organization")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write("No park visit data for that selection.")

except Exception as e:
    st.error(f"Error connecting to Google Sheets: {str(e)}")
