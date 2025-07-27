import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sqlite3
import calendar
from utils.style_utils import inject_global_styles
inject_global_styles()

# Page config
st.set_page_config(
    page_title="Your Spiral Trends",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for the trends page
st.markdown("""
<style>
    :root {
        --primary: #ff9ff3;
        --secondary: #f368e0;
        --accent: #ff6b6b;
        --background: #fff9ff;
        --text: #5f27cd;
    }
    
    .stApp {
        background-color: var(--background);
    }
    
    h1, h2, h3 {
        color: var(--text) !important;
        font-family: 'Arial Rounded MT Bold', sans-serif;
    }
    
    .stDataFrame {
        border: 1px solid var(--primary) !important;
        border-radius: 10px !important;
    }
    
    .css-1d391kg {
        background-color: #fde8ff !important;
    }
    
    .metric-card {
        background-color: #fef6ff !important;
        border-radius: 15px !important;
        padding: 15px !important;
        border-left: 4px solid var(--accent) !important;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .plot-container {
        background-color: white;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

def load_journal_data():
    """Load journal data from SQLite database"""
    conn = sqlite3.connect("user_journal.db")
    query = "SELECT timestamp, spiral_level, mood, pattern, emotion FROM journal"
    df = pd.read_sql(query, conn)
    conn.close()
    
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.day_name()
        df['month'] = df['timestamp'].dt.month_name()
        df['week'] = df['timestamp'].dt.isocalendar().week
    return df

def create_trend_plots(df):
    """Create all visualization plots"""
    if df.empty:
        st.warning("No journal data available yet. Keep using the app to see your trends!")
        return
    
    # Metrics row
    st.markdown("### 🌸 Your Spiral Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">'
                    f'<h3>📅 Total Entries</h3>'
                    f'<h2>{len(df)}</h2>'
                    '</div>', unsafe_allow_html=True)
    
    with col2:
        avg_spiral = df['spiral_level'].mean()
        st.markdown('<div class="metric-card">'
                    f'<h3>🌀 Average Spiral</h3>'
                    f'<h2>{avg_spiral:.1f}/10</h2>'
                    '</div>', unsafe_allow_html=True)
    
    with col3:
        common_mood = df['mood'].mode()[0] if not df['mood'].mode().empty else "N/A"
        st.markdown('<div class="metric-card">'
                    f'<h3>🌈 Most Common Mood</h3>'
                    f'<h2>{common_mood}</h2>'
                    '</div>', unsafe_allow_html=True)
    
    with col4:
        common_pattern = df['pattern'].mode()[0] if not df['pattern'].mode().empty else "N/A"
        st.markdown('<div class="metric-card">'
                    f'<h3>🔄 Common Pattern</h3>'
                    f'<h2>{common_pattern.replace("_", " ").title()}</h2>'
                    '</div>', unsafe_allow_html=True)
    
    # Weekly trends
    st.markdown("---")
    st.markdown("### 📆 Weekly Patterns")
    weekly_df = df.groupby(['day_of_week', 'hour']).agg({'spiral_level':'mean'}).reset_index()
    
    # Ensure all days are present
    days_order = list(calendar.day_name)
    weekly_df['day_of_week'] = pd.Categorical(weekly_df['day_of_week'], categories=days_order, ordered=True)
    weekly_df = weekly_df.sort_values(['day_of_week', 'hour'])
    
    fig = px.density_heatmap(
        weekly_df, 
        x="day_of_week", 
        y="hour", 
        z="spiral_level",
        title="When Do You Spiral Most? (Darker = Higher Spiral)",
        color_continuous_scale="magma",
        height=500
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#5f27cd')
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Monthly trends
    st.markdown("---")
    st.markdown("### 🌙 Monthly Insights")
    col1, col2 = st.columns(2)
    
    with col1:
        monthly_df = df.groupby('month').agg({'spiral_level':'mean'}).reset_index()
        months_order = list(calendar.month_name)[1:]
        monthly_df['month'] = pd.Categorical(monthly_df['month'], categories=months_order, ordered=True)
        monthly_df = monthly_df.sort_values('month')
        
        fig = px.line(
            monthly_df, 
            x="month", 
            y="spiral_level",
            title="Average Spiral Level by Month",
            markers=True,
            height=400
        )
        fig.update_traces(line_color='#f368e0', marker_color='#ff6b6b')
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#5f27cd')
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        mood_counts = df['mood'].value_counts().reset_index()
        mood_counts.columns = ['mood', 'count']
        
        fig = px.pie(
            mood_counts,
            names='mood',
            values='count',
            title="Your Mood Distribution",
            height=400,
            color_discrete_sequence=px.colors.sequential.Magenta_r
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#5f27cd'),
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Pattern trends
    st.markdown("---")
    st.markdown("### 🔄 Your Thought Patterns")
    pattern_df = df['pattern'].value_counts().reset_index()
    pattern_df.columns = ['pattern', 'count']
    pattern_df['pattern'] = pattern_df['pattern'].str.replace('_', ' ').str.title()
    
    fig = px.bar(
        pattern_df,
        x='pattern',
        y='count',
        title="How Often Each Pattern Appears",
        color='count',
        color_continuous_scale='magma',
        height=500
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#5f27cd'),
        xaxis_title="Pattern Type",
        yaxis_title="Count"
    )
    st.plotly_chart(fig, use_container_width=True)

def main():
    st.title("🌸 Your Spiral Trends")
    st.markdown("""
    <style>
        .title {
            color: #f368e0;
        }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("Visualizing your thought patterns to help you understand yourself better.")
    
    df = load_journal_data()
    create_trend_plots(df)
    
    st.markdown("---")
    st.markdown("### 💡 Insights & Recommendations")
    
    if not df.empty:
        # Generate some insights
        avg_spiral = df['spiral_level'].mean()
        worst_day = df.groupby('day_of_week')['spiral_level'].mean().idxmax()
        worst_hour = df.groupby('hour')['spiral_level'].mean().idxmax()
        common_pattern = df['pattern'].mode()[0].replace('_', ' ')
        
        st.markdown(f"""
        - 🌟 Your average spiral intensity is **{avg_spiral:.1f}/10**
        - 📅 **{worst_day}s** tend to be your most challenging days
        - 🕒 Around **{worst_hour}:00** is when you spiral most intensely
        - 🔄 Your most common thought pattern is **{common_pattern}**
        
        *Consider planning self-care activities during these vulnerable times.*
        """)
    else:
        st.info("Keep using the app to generate personalized insights!")

if __name__ == "__main__":
    main()