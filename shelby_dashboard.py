import streamlit as st
import plotly.express as px
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Function to load Google Sheet data
def load_google_sheet_data(spreadsheet_id, sheet_name):
    scope = ['https://www.googleapis.com/auth/spreadsheets', 
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('arcgis-fos-a2e12f56c5d8.json', scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(spreadsheet_id)
    sheet = spreadsheet.worksheet(sheet_name)
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Custom CSS for styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&family=Montserrat:wght@600&display=swap');
    
    body {
        font-family: 'Roboto', sans-serif;
        background-color: #F5F5F5;
    }
    .stApp {
        background-color: #F5F5F5;
    }
    h1, h2, h3 {
        font-family: 'Montserrat', sans-serif;
        color: #2E7D32;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    .metric-title {
        font-size: 16px;
        color: #555;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #2E7D32;
    }
    .metric-delta {
        font-size: 14px;
        color: #F44336;
    }
    .sidebar .sidebar-content {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-family: 'Roboto', sans-serif;
        border: none;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    </style>
""", unsafe_allow_html=True)

# Streamlit page configuration
st.set_page_config(
    page_title="Friends of Shelby Partnership",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/150x50.png?text=Logo", use_column_width=True)
    st.markdown("## Navigation")
    st.markdown("[About Us](https://www.example.com/about)")
    st.markdown("[Volunteer Opportunities](https://www.example.com/volunteer)")
    st.markdown("[Contact Us](https://www.example.com/contact)")
    st.markdown("---")
    if st.button("Refresh Data"):
        st.experimental_rerun()

# Title
st.markdown("<h1 style='text-align: center;'>🌳 Friends of Shelby Partnership Volunteer Dashboard</h1>", unsafe_allow_html=True)

# Load data from Google Sheets
SPREADSHEET_ID = "1OgP1vp1OjiRgtisNrHoHxPIPbRxGjKtcegCS7ztVPr0"

try:
    # Load dashboard metrics
    dashboard_data = load_google_sheet_data(SPREADSHEET_ID, "Overall Dashboard")

    # Extract metrics from the "Overall Dashboard" tab
    metrics = {
        "Total Volunteers": dashboard_data[dashboard_data['Single Value Metrics'] == 'Total Volunteers'][''].iloc[0] if not dashboard_data[dashboard_data['Single Value Metrics'] == 'Total Volunteers'].empty else 0,
        "Total Hours": dashboard_data[dashboard_data['Single Value Metrics'] == 'Total Hours'][''].iloc[0] if not dashboard_data[dashboard_data['Single Value Metrics'] == 'Total Hours'].empty else 0,
        "Value of Hours": dashboard_data[dashboard_data['Single Value Metrics'] == 'Value of Hours'][''].iloc[0] if not dashboard_data[dashboard_data['Single Value Metrics'] == 'Value of Hours'].empty else 0,
        "Total Acres Cleaned": dashboard_data[dashboard_data['Single Value Metrics'] == 'Total Acres Cleaned'][''].iloc[0] if not dashboard_data[dashboard_data['Single Value Metrics'] == 'Total Acres Cleaned'].empty else 0,
        "% of Forest Reached": dashboard_data[dashboard_data['Single Value Metrics'] == '% of Forest Reached'][''].iloc[0] if not dashboard_data[dashboard_data['Single Value Metrics'] == '% of Forest Reached'].empty else 0,
    }
except Exception as e:
    st.error(f"Error loading dashboard data: {e}")
    metrics = {
        "Total Volunteers": 0,
        "Total Hours": 0,
        "Value of Hours": 0,
        "Total Acres Cleaned": 0,
        "% of Forest Reached": 0,
    }

# Display metrics
st.markdown("<h2 style='text-align: center;'>Key Metrics</h2>", unsafe_allow_html=True)
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown("<div class='metric-card'><div class='metric-title'>Total Volunteers</div><div class='metric-value'>{}</div><div class='metric-delta'>+5% from last year</div></div>".format(metrics["Total Volunteers"]), unsafe_allow_html=True)
with col2:
    st.markdown("<div class='metric-card'><div class='metric-title'>Total Hours</div><div class='metric-value'>{}</div><div class='metric-delta'>+10% from last year</div></div>".format(metrics["Total Hours"]), unsafe_allow_html=True)
with col3:
    st.markdown("<div class='metric-card'><div class='metric-title'>Value of Volunteer Hours</div><div class='metric-value'>${}</div><div class='metric-delta'>+8% from last year</div></div>".format(metrics["Value of Hours"]), unsafe_allow_html=True)
with col4:
    st.markdown("<div class='metric-card'><div class='metric-title'>Total Acres Cleaned</div><div class='metric-value'>{}</div><div class='metric-delta'>+12% from last year</div></div>".format(metrics["Total Acres Cleaned"]), unsafe_allow_html=True)
with col5:
    st.markdown("<div class='metric-card'><div class='metric-title'>% of Forest Reached</div><div class='metric-value'>{}%</div><div class='metric-delta'>+15% from last year</div></div>".format(metrics["% of Forest Reached"]), unsafe_allow_html=True)

# Load data for charts
try:
    participation_data = load_google_sheet_data(SPREADSHEET_ID, "Volunteer Participation Trends")
    satisfaction_data = load_google_sheet_data(SPREADSHEET_ID, "Volunteer Satisfaction")
    popular_events_data = load_google_sheet_data(SPREADSHEET_ID, "Most Popular Events")
    acres_cleaned_data = load_google_sheet_data(SPREADSHEET_ID, "Acres Cleaned Timeline")

    # Ensure data types are correct
    participation_data['Date/Year'] = pd.to_datetime(participation_data['Date/Year'], errors='coerce')
    satisfaction_data['Date'] = pd.to_datetime(satisfaction_data['Date'], errors='coerce')
    acres_cleaned_data['Date/Year'] = pd.to_datetime(acres_cleaned_data['Date/Year'], errors='coerce')
    popular_events_data['Total Participants'] = pd.to_numeric(popular_events_data['Total Participants'], errors='coerce')
    satisfaction_data['Satisfaction Score'] = pd.to_numeric(satisfaction_data['Satisfaction Score'], errors='coerce')
    acres_cleaned_data['Acres Cleaned'] = pd.to_numeric(acres_cleaned_data['Acres Cleaned'], errors='coerce')
except Exception as e:
    st.error(f"Error loading chart data: {e}")
    # Fallback to empty DataFrames to prevent crashes
    participation_data = pd.DataFrame(columns=['Date/Year', 'Event Name', 'Participant Count'])
    satisfaction_data = pd.DataFrame(columns=['Date', 'Event Name', 'Satisfaction Score'])
    popular_events_data = pd.DataFrame(columns=['Event Name', 'Total Participants'])
    acres_cleaned_data = pd.DataFrame(columns=['Date/Year', 'Acres Cleaned'])

# Volunteer Participation Over Time
st.markdown("<h2 style='text-align: center;'>Volunteer Participation Over Time</h2>", unsafe_allow_html=True)
fig1 = px.line(
    participation_data,
    x="Date/Year",
    y="Participant Count",
    color="Event Name",
    title="Volunteer Participation Trends",
    labels={"Participant Count": "Number of Volunteers", "Date/Year": "Date"},
    template="plotly_white"
)
fig1.update_layout(
    font=dict(family="Roboto", size=12),
    title_font=dict(family="Montserrat", size=20),
    legend_title_text="Event Type",
    xaxis_title="Date",
    yaxis_title="Number of Volunteers",
    hovermode="x unified",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.1)"),
    yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.1)")
)
fig1.update_traces(line=dict(width=3), hovertemplate="%{y} volunteers<extra>%{fullData.name}</extra>")
st.plotly_chart(fig1, use_container_width=True)

# Volunteer Satisfaction
st.markdown("<h2 style='text-align: center;'>Volunteer Satisfaction</h2>", unsafe_allow_html=True)
fig2 = px.line(
    satisfaction_data,
    x="Date",
    y="Satisfaction Score",
    color="Event Name",
    title="Volunteer Satisfaction Over Time",
    labels={"Satisfaction Score": "Average Satisfaction (1-5)", "Date": "Date"},
    template="plotly_white"
)
fig2.update_layout(
    font=dict(family="Roboto", size=12),
    title_font=dict(family="Montserrat", size=20),
    legend_title_text="Event Type",
    xaxis_title="Date",
    yaxis_title="Satisfaction Score",
    hovermode="x unified",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.1)"),
    yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.1)")
)
fig2.update_traces(line=dict(width=3), hovertemplate="%{y:.2f}<extra>%{fullData.name}</extra>")
st.plotly_chart(fig2, use_container_width=True)

# Most Popular Events
st.markdown("<h2 style='text-align: center;'>Most Popular Events</h2>", unsafe_allow_html=True)
fig3 = px.bar(
    popular_events_data,
    x="Event Name",
    y="Total Participants",
    title="Top Events by Participation",
    labels={"Total Participants": "Number of Participants"},
    template="plotly_white",
    color_discrete_sequence=["#4CAF50"]
)
fig3.update_layout(
    font=dict(family="Roboto", size=12),
    title_font=dict(family="Montserrat", size=20),
    xaxis_title="Event Name",
    yaxis_title="Number of Participants",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.1)")
)
fig3.update_traces(texttemplate="%{y}", textposition="auto", hovertemplate="%{x}: %{y} participants<extra></extra>")
st.plotly_chart(fig3, use_container_width=True)

# Acres Cleaned Over Time
st.markdown("<h2 style='text-align: center;'>Acres Cleaned Over Time</h2>", unsafe_allow_html=True)
fig4 = px.line(
    acres_cleaned_data,
    x="Date/Year",
    y="Acres Cleaned",
    title="Acres Cleaned Timeline",
    labels={"Acres Cleaned": "Acres Cleaned", "Date/Year": "Date"},
    template="plotly_white",
    color_discrete_sequence=["#2E7D32"]
)
fig4.update_layout(
    font=dict(family="Roboto", size=12),
    title_font=dict(family="Montserrat", size=20),
    xaxis_title="Date",
    yaxis_title="Acres Cleaned",
    hovermode="x unified",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.1)"),
    yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.1)")
)
fig4.update_traces(line=dict(width=3), hovertemplate="%{y:.2f} acres<extra></extra>")
st.plotly_chart(fig4, use_container_width=True)
