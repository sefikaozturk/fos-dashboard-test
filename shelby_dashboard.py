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
        margin: 1.5rem 0;
        border-bottom: 1px solid #e1e5e9;
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
    st.markdown('<div class="nav-section">', unsafe_allow_html=True)
    st.markdown("🌲 **Navigation**")
    
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
    st.markdown('<div class="component-separator">', unsafe_allow_html=True)
    col1, col2 = st.columns([6, 2])
    with col1:
        st.title("Friends of Shelby Dashboard")
        st.markdown("**Volunteer Program**")
    with col2:
        st.markdown("**Sefika Ozturk** - *Admin*")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Top metrics row with equal sizing
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        with st.container():
            st.markdown("""
            <div style="background: #4a4a4a; color: white; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Total Volunteers</div>
                <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">21,324</div>
                <div style="font-size: 0.72rem; opacity: 0.8;">+2,031</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown("""
            <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
                <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Total Hours</div>
                <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">16,769</div>
                <div style="font-size: 0.72rem; opacity: 0.8;">+3,390</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        with st.container():
            st.markdown("""
            <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
                <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Value of The Hours</div>
                <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">$221,324.50</div>
                <div style="font-size: 0.72rem; opacity: 0.8;">+$23,456</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col4:
        with st.container():
            st.markdown("""
            <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
                <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Change fr. Last Year</div>
                <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">12.8%</div>
                <div style="font-size: 0.72rem; opacity: 0.8;">↑ 2.2%</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Charts row with proper containers
    col1, col2 = st.columns([2, 1])
    
    with col1:
        chart_container = st.container(border=True)
        with chart_container:
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
    
    with col2:
        chart_container = st.container(border=True)
        with chart_container:
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
    
    # Bottom section with proper containers
    col1, col2 = st.columns([3, 1])
    
    with col1:
        chart_container = st.container(border=True)
        with chart_container:
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
    
    with col2:
        filter_container = st.container(border=True)
        with filter_container:
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
    
    # Top metrics with equal sizing
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container():
            st.markdown("""
            <div style="background: #4a4a4a; color: white; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Acres Cleaned</div>
                <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">1,340</div>
                <div style="font-size: 0.72rem; opacity: 0.8;">Acreage for the current month</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown("""
            <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
                <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">% of Forest Reached</div>
                <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">34%</div>
                <div style="font-size: 0.72rem; opacity: 0.8;">Area % of the forest covered by RTF</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        with st.container():
            st.markdown("""
            <div style="background: #f0f2f6; color: #333; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid #e1e5e9;">
                <div style="font-size: 0.8rem; font-weight: 500; margin-bottom: 0.4rem; opacity: 0.9;">Volunteers</div>
                <div style="font-size: 1.7rem; font-weight: 600; margin-bottom: 0.2rem;">76</div>
                <div style="font-size: 0.72rem; opacity: 0.8;">Volunteers participating in RTF</div>
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
