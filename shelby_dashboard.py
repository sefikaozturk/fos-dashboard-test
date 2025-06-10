import streamlit as st
import plotly.express as px
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Streamlit page configuration - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Friends of Shelby Partnership",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for title styling
st.markdown("""
    <style>
        .main-title {
            font-size: 2.5em;
            font-weight: bold;
            color: #2E7D32;
            text-align: center;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# Function to load Google Sheet data
@st.cache_data
def load_google_sheet_data(spreadsheet_id, sheet_name):
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 
                 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(spreadsheet_id)
        sheet = spreadsheet.worksheet(sheet_name)
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error loading data from {sheet_name}: {e}")
        return pd.DataFrame()

# Title
st.markdown('<div class="main-title">🌳 Friends of Shelby Partnership Volunteer Dashboard</div>', unsafe_allow_html=True)

# Load data from Google Sheets
SPREADSHEET_ID = "1OgP1vp1OjiRgtisNrHoHxPIPbRxGjKtcegCS7ztVPr0"

# Load dashboard metrics
dashboard_data = load_google_sheet_data(SPREADSHEET_ID, "Overall Dashboard")

# Extract metrics from the "Overall Dashboard" tab
metrics = {
    "Total Volunteers": dashboard_data[dashboard_data['Single Value Metrics'] == 'Total Volunteers'][''].iloc[0] if not dashboard_data[dashboard_data['Single Value Metrics'] == 'Total Volunteers'].empty else 250,
    "Total Hours": dashboard_data[dashboard_data['Single Value Metrics'] == 'Total Hours'][''].iloc[0] if not dashboard_data[dashboard_data['Single Value Metrics'] == 'Total Hours'].empty else 1200,
    "Value of Hours": dashboard_data[dashboard_data['Single Value Metrics'] == 'Value of Hours'][''].iloc[0] if not dashboard_data[dashboard_data['Single Value Metrics'] == 'Value of Hours'].empty else 30000,
    "Total Acres Cleaned": dashboard_data[dashboard_data['Single Value Metrics'] == 'Total Acres Cleaned'][''].iloc[0] if not dashboard_data[dashboard_data['Single Value Metrics'] == 'Total Acres Cleaned'].empty else 150,
    "% of Forest Reached": dashboard_data[dashboard_data['Single Value Metrics'] == '% of Forest Reached'][''].iloc[0] if not dashboard_data[dashboard_data['Single Value Metrics'] == '% of Forest Reached'].empty else 15,
}

# Metrics
st.header("Key Metrics")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Volunteers", f"{int(metrics['Total Volunteers'])}", "10%", delta_color="inverse")
col2.metric("Total Hours", f"{int(metrics['Total Hours'])}", "15%", delta_color="inverse")
col3.metric("Value of Volunteer Hours", f"${int(metrics['Value of Hours']):,}", "12%", delta_color="inverse")
col4.metric("Total Acres Cleaned", f"{float(metrics['Total Acres Cleaned']):.2f}", "8%", delta_color="inverse")
col5.metric("% of Forest Reached", f"{float(metrics['% of Forest Reached']):.1f}%", "5%", delta_color="inverse")

# Load chart data from Google Sheets
volunteer_data = load_google_sheet_data(SPREADSHEET_ID, "Volunteer Participation Trends")
satisfaction_data = load_google_sheet_data(SPREADSHEET_ID, "Volunteer Satisfaction")
events_data = load_google_sheet_data(SPREADSHEET_ID, "Most Popular Events")
acres_data = load_google_sheet_data(SPREADSHEET_ID, "Acres Cleaned Timeline")

# Ensure data types are correct
if not volunteer_data.empty:
    volunteer_data['Date/Year'] = pd.to_datetime(volunteer_data['Date/Year'], errors='coerce')
    volunteer_data['Participant Count'] = pd.to_numeric(volunteer_data['Participant Count'], errors='coerce')
if not satisfaction_data.empty:
    satisfaction_data['Date'] = pd.to_datetime(satisfaction_data['Date'], errors='coerce')
    satisfaction_data['Satisfaction Score'] = pd.to_numeric(satisfaction_data['Satisfaction Score'], errors='coerce')
if not events_data.empty:
    events_data['Total Participants'] = pd.to_numeric(events_data['Total Participants'], errors='coerce')
if not acres_data.empty:
    acres_data['Date/Year'] = pd.to_datetime(acres_data['Date/Year'], errors='coerce')
    acres_data['Acres Cleaned'] = pd.to_numeric(acres_data['Acres Cleaned'], errors='coerce')

# Plot Volunteer Participation Over Time
st.header("Volunteer Participation Over Time")
if not volunteer_data.empty:
    fig1 = px.line(
        volunteer_data,
        x="Date/Year",
        y="Participant Count",
        color="Event Name",
        title="Volunteer Participation Trends",
        labels={"Participant Count": "Number of Volunteers", "Date/Year": "Date"}
    )
    fig1.update_layout(
        legend_title_text="Event Type",
        font=dict(size=14),
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor='LightGray'),
        yaxis=dict(showgrid=True, gridcolor='LightGray')
    )
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.warning("No data available for Volunteer Participation Trends.")

# Plot Volunteer Satisfaction
st.header("Volunteer Satisfaction")
if not satisfaction_data.empty:
    fig2 = px.line(
        satisfaction_data,
        x="Date",
        y="Satisfaction Score",
        color="Event Name",
        title="Volunteer Satisfaction Over Time",
        labels={"Satisfaction Score": "Average Satisfaction (1-5)", "Date": "Date"}
    )
    fig2.update_layout(
        legend_title_text="Event Type",
        font=dict(size=14),
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor='LightGray'),
        yaxis=dict(showgrid=True, gridcolor='LightGray')
    )
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("No data available for Volunteer Satisfaction.")

# Plot Most Popular Events
st.header("Most Popular Events")
if not events_data.empty:
    fig3 = px.bar(
        events_data,
        x="Event Name",
        y="Total Participants",
        title="Top Events by Participation",
        labels={"Total Participants": "Number of Participants"},
        text="Total Participants",
        color_discrete_sequence=["#4CAF50"]
    )
    fig3.update_traces(textposition='auto')
    fig3.update_layout(
        font=dict(size=14),
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor='LightGray'),
        yaxis=dict(showgrid=True, gridcolor='LightGray')
    )
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.warning("No data available for Most Popular Events.")

# Plot Acres Cleaned Over Time
st.header("Acres Cleaned Over Time")
if not acres_data.empty:
    fig4 = px.line(
        acres_data,
        x="Date/Year",
        y="Acres Cleaned",
        title="Acres Cleaned Timeline",
        labels={"Acres Cleaned": "Acres Cleaned", "Date/Year": "Date"},
        color_discrete_sequence=["#4CAF50"]
    )
    fig4.update_layout(
        font=dict(size=14),
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor='LightGray'),
        yaxis=dict(showgrid=True, gridcolor='LightGray')
    )
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.warning("No data available for Acres Cleaned Timeline.")
