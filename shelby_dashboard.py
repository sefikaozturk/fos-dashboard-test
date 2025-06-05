import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

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
.metric-card {
    background: #4a4a4a;
    color: white;
    padding: 1.5rem;
    border-radius: 10px;
    margin-bottom: 1rem;
    height: 150px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.metric-card-light {
    background: #f0f2f6;
    color: #333;
    padding: 1.5rem;
    border-radius: 10px;
    margin-bottom: 1rem;
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
/* Section divider */
.section-divider {
    border-top: 1px solid #e1e5e9;
    margin: 2rem 0;
}
/* Make sidebar thinner */
[data-testid="stSidebar"] {
    min-width: 250px;
    max-width: 250px;
}
/* Dashboard component containers */
.dashboard-component {
    background: white;
    padding: 1.5rem;
    border-radius: 10px;
    border: 1px solid #e1e5e9;
    margin-bottom: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# Sidebar navigation - changed from dropdown to radio buttons
st.sidebar.title("🌲 Friends of Shelby")
st.sidebar.markdown("### Navigation")
page = st.sidebar.radio(
    "Select a page:",
    ["Volunteer Program", "Restore The Forest Program", "Strategic Plan - Pillar 1"]
)

# Sample data generation
def generate_volunteer_data():
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May']
    invasive_removal = [45, 55, 65, 45, 35]
    trail_maintenance = [35, 75, 55, 65, 45]
    painting = [25, 45, 55, 85, 65]
    lake_cleaning = [55, 35, 45, 75, 55]
    return months, invasive_removal, trail_maintenance, painting, lake_cleaning

def generate_forest_data():
    months = ['Jan', 'Feb', 'March', 'April', 'May', 'June', 'July']
    acres_data = [18, 15, 16, 17, 13, 19, 17]
    return months, acres_data

def generate_accessibility_data():
    months = ['01/25', '02/25', '03/25', '04/25', '05/25', '06/25', '07/25', '08/25']
    iclr = [30, 58, 43, 30, 20, 55, 25, 68]
    cerecore = [85, 82, 65, 55, 75, 60, 54, 60]
    return months, iclr, cerecore

# Page 1: Volunteer Program
if page == "Volunteer Program":
    # Header
    col1, col2 = st.columns([6, 2])
    with col1:
        st.title("Friends of Shelby Dashboard")
        st.markdown("Volunteer Program")
    with col2:
        st.markdown("Sefika Ozturk - Admin")
    
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    
    # Top metrics row with equal-sized cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>Total Volunteers</h3>
            <h1>21,324</h1>
            <p>+2,031</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>Total Hours</h3>
            <h1>16,769</h1>
            <p>+3,390</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>Value of The Hours</h3>
            <h1>$221,324.50</h1>
            <p>+$23,456</p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>Change fr. Last Year</h3>
            <h1>12.8%</h1>
            <p>↑ 2.2%</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    
    # Charts row
    col1, col2 = st.columns([2, 1])
    with col1:
        with st.container():
            st.markdown("<div class='dashboard-component'>", unsafe_allow_html=True)
            st.subheader("Volunteer Participation Trends Over Time")
            months, invasive, trail, painting, lake = generate_volunteer_data()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=months, y=invasive, name='Invasive Removal', line=dict(color='#333')))
            fig.add_trace(go.Scatter(x=months, y=trail, name='Trail Maintenance', line=dict(color='#666')))
            fig.add_trace(go.Scatter(x=months, y=painting, name='Painting', line=dict(color='#999')))
            fig.add_trace(go.Scatter(x=months, y=lake, name='Lake Cleaning', line=dict(color='#ccc')))
            fig.update_layout(
                showlegend=True,
                height=400,
                xaxis_title="",
                yaxis_title="",
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
    with col2:
        with st.container():
            st.markdown("<div class='dashboard-component'>", unsafe_allow_html=True)
            st.subheader("Popular Events")
            # Pie chart
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
            st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    
    # Bottom section
    col1, col2 = st.columns([3, 1])
    with col1:
        with st.container():
            st.markdown("<div class='dashboard-component'>", unsafe_allow_html=True)
            st.subheader("Volunteer Satisfaction")
            # Bar chart data
            categories = ['Invasive Removal', 'Trail Maintenance', 'Painting', 'Lake Cleaning']
            months_bar = ['Jan', 'Feb', 'Mar', 'Apr', 'May']
            fig_bar = go.Figure()
            # Add bars for each month
            for i, month in enumerate(months_bar):
                values = np.random.randint(60, 90, len(categories))
                fig_bar.add_trace(go.Bar(
                    name=month,
                    x=categories,
                    y=values,
                    marker_color=['#333', '#666', '#999', '#ccc'][i % 4]
                ))
            fig_bar.update_layout(
                barmode='group',
                height=400,
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
    with col2:
        with st.container():
            st.markdown("<div class='dashboard-component'>", unsafe_allow_html=True)
            st.markdown("### Filters")
            st.selectbox("Pick date", ["Overall"])
            st.selectbox("Pick organization", ["Overall"])
            st.checkbox("Show multiple")
            st.markdown("</div>", unsafe_allow_html=True)

# Page 2: Restore The Forest Program
elif page == "Restore The Forest Program":
    # Header
    col1, col2 = st.columns([6, 2])
    with col1:
        st.title("Friends of Shelby Dashboard")
        st.markdown("Restore The Forest Program")
    with col2:
        st.markdown("Renee McKelvey - Community Member")
    
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    
    # Top metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>Acres Cleaned</h3>
            <h1>1,340</h1>
            <p>Acreage for the current month</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>% of Forest Reached</h3>
            <h1>34%</h1>
            <p>Area % of the forest covered by RTF</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>Volunteers</h3>
            <h1>76</h1>
            <p>Volunteers participating in RTF</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    
    # Charts row
    col1, col2 = st.columns([2, 1])
    with col1:
        with st.container():
            st.markdown("<div class='dashboard-component'>", unsafe_allow_html=True)
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
            st.markdown("</div>", unsafe_allow_html=True)
            
    with col2:
        with st.container():
            st.markdown("<div class='dashboard-component'>", unsafe_allow_html=True)
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
            st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    
    # Bottom section - Logs
    col1, col2 = st.columns(2)
    with col1:
        with st.container():
            st.markdown("<div class='dashboard-component'>", unsafe_allow_html=True)
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
                cola, colb = st.columns([3, 1])
                with cola:
                    st.write(f"• {item}")
                with colb:
                    st.write(time)
            st.write("🔄 view all")
            st.markdown("</div>", unsafe_allow_html=True)
            
    with col2:
        with st.container():
            st.markdown("<div class='dashboard-component'>", unsafe_allow_html=True)
            st.subheader("DIY Volunteers & WildSpotter Submissions Log")
            # Log entries
            st.markdown("""
            **Christan Bilney - 2 days ago**<br>
            Low priority | V 3.20<br>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisl ut aliquip ex ea commodo consequat. More...
            
            **Hady Vanetti - 4 days ago**<br>
            Critical | V 3.13<br>
            Aliquam vel nibh iaculis, ornare purus sit amet, euismod dui. Cras sed tristique neque. Cras ornare dui lorem, vel rhoncus elit venenatis sit amet. Suspendisse varius massa in gravida commodo. More...
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# Page 3: Strategic Plan - Pillar 1
else:
    # Header
    col1, col2 = st.columns([6, 2])
    with col1:
        st.title("Friends of Shelby Dashboard")
        st.markdown("Strategic Plan - Pillar 1")
    with col2:
        st.markdown("Sefika Ozturk - Admin")
    
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>Total Responses</h3>
            <h1>25</h1>
            <p>+2</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>% Facing Barriers</h3>
            <h1>75%</h1>
            <p>+3%</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>Accessibility</h3>
            <h1>+23%</h1>
            <p>+5%</p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>Park Visits</h3>
            <h1>+14.8%</h1>
            <p>↑ 2.2%</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    
    # Main chart
    col1, col2 = st.columns([3, 1])
    with col1:
        with st.container():
            st.markdown("<div class='dashboard-component'>", unsafe_allow_html=True)
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
            st.markdown("</div>", unsafe_allow_html=True)
            
    with col2:
        with st.container():
            st.markdown("<div class='dashboard-component'>", unsafe_allow_html=True)
            st.markdown("### Filters")
            colq4, colq5, col_q6 = st.columns(3)
            with colq4:
                st.button("Q4", type="secondary")
            with colq5:
                st.button("Q5", type="secondary")
            with col_q6:
                st.button("Q6", type="primary")
            st.selectbox("Pick date", ["04/2025"])
            st.selectbox("Pick organization", ["ICLR, Cerecore HCA"])
            st.checkbox("Show multiple", value=True)
            st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    
    # Bottom section - Horizontal bar chart
    st.subheader("Park Accessibility Statements")
    col1, col2 = st.columns([4, 1])
    with col1:
        with st.container():
            st.markdown("<div class='dashboard-component'>", unsafe_allow_html=True)
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
            st.markdown("</div>", unsafe_allow_html=True)
            
    with col2:
        with st.container():
            st.markdown("<div class='dashboard-component'>", unsafe_allow_html=True)
            colq4b, colq5b, col_q6b = st.columns(3)
            with colq4b:
                st.button("Q4", type="secondary", key="q4b")
            with colq5b:
                st.button("Q5", type="secondary", key="q5b")
            with col_q6b:
                st.button("Q6", type="primary", key="q6b")
            st.markdown("</div>", unsafe_allow_html=True)
