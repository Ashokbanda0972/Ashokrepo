#!/usr/bin/env python3
"""
🏠 Real Estate Intelligence Dashboard
Interactive Streamlit dashboard for real estate data analysis and pipeline management
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
import os
import subprocess
import sys
from datetime import datetime, timedelta
import json
import time

# Page configuration
st.set_page_config(
    page_title="Real Estate Intelligence Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .property-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: #f9f9f9;
    }
    .sidebar-header {
        color: #2E86AB;
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    """Load data from CSV and database with caching"""
    data = {}
    
    # Try to load from CSV first
    csv_path = "./data/classified_listings.csv"
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        data['csv'] = df
        data['csv_modified'] = datetime.fromtimestamp(os.path.getmtime(csv_path))
    else:
        data['csv'] = None
        data['csv_modified'] = None
    
    # Try to load from database
    db_path = "./data/development_leads.db"
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            query = """
            SELECT source, url, address, price, beds, baths, living_area, 
                   raw_json, classified_label, score, created_at as processed_at
            FROM listings 
            ORDER BY created_at DESC
            """
            df_db = pd.read_sql_query(query, conn)
            conn.close()
            data['database'] = df_db
            data['db_modified'] = datetime.fromtimestamp(os.path.getmtime(db_path))
        except Exception as e:
            st.error(f"Database error: {e}")
            data['database'] = None
            data['db_modified'] = None
    else:
        data['database'] = None
        data['db_modified'] = None
    
    return data

def format_currency(value):
    """Format currency values"""
    if pd.isna(value):
        return "N/A"
    return f"${value:,.0f}"

def create_overview_metrics(df):
    """Create overview metrics cards"""
    if df is None or df.empty:
        st.warning("No data available")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🏠 Total Properties</h3>
            <h2>{}</h2>
        </div>
        """.format(len(df)), unsafe_allow_html=True)
    
    with col2:
        avg_price = df['price'].mean()
        st.markdown("""
        <div class="metric-card">
            <h3>💰 Average Price</h3>
            <h2>{}</h2>
        </div>
        """.format(format_currency(avg_price)), unsafe_allow_html=True)
    
    with col3:
        price_range = f"{format_currency(df['price'].min())} - {format_currency(df['price'].max())}"
        st.markdown("""
        <div class="metric-card">
            <h3>📊 Price Range</h3>
            <h2>{}</h2>
        </div>
        """.format(price_range), unsafe_allow_html=True)
    
    with col4:
        sources = df['source'].nunique()
        st.markdown("""
        <div class="metric-card">
            <h3>🔍 Data Sources</h3>
            <h2>{}</h2>
        </div>
        """.format(sources), unsafe_allow_html=True)

def create_price_distribution_chart(df):
    """Create price distribution visualization"""
    if df is None or df.empty:
        return
    
    fig = px.histogram(
        df, 
        x='price', 
        nbins=20,
        title="💰 Price Distribution",
        labels={'price': 'Price ($)', 'count': 'Number of Properties'},
        color_discrete_sequence=['#667eea']
    )
    
    fig.update_layout(
        title_font_size=20,
        title_x=0.5,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    return fig

def create_classification_chart(df):
    """Create classification pie chart"""
    if df is None or df.empty:
        return
    
    classification_counts = df['classified_label'].value_counts()
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
    
    fig = px.pie(
        values=classification_counts.values,
        names=classification_counts.index,
        title="🏷️ Property Classifications",
        color_discrete_sequence=colors
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        title_font_size=20,
        title_x=0.5,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def create_source_comparison_chart(df):
    """Create source comparison chart"""
    if df is None or df.empty:
        return
    
    source_stats = df.groupby('source').agg({
        'price': ['count', 'mean'],
        'score': 'mean'
    }).round(2)
    
    source_stats.columns = ['Count', 'Avg_Price', 'Avg_Score']
    source_stats = source_stats.reset_index()
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Properties by Source', 'Average Score by Source'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Properties count
    fig.add_trace(
        go.Bar(
            x=source_stats['source'],
            y=source_stats['Count'],
            name='Count',
            marker_color='#667eea'
        ),
        row=1, col=1
    )
    
    # Average score
    fig.add_trace(
        go.Bar(
            x=source_stats['source'],
            y=source_stats['Avg_Score'],
            name='Avg Score',
            marker_color='#764ba2'
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title_text="📈 Source Performance Analysis",
        title_font_size=20,
        title_x=0.5,
        showlegend=False
    )
    
    return fig

def create_scatter_plot(df):
    """Create price vs living area scatter plot"""
    if df is None or df.empty:
        return
    
    fig = px.scatter(
        df,
        x='living_area',
        y='price',
        color='classified_label',
        size='score',
        hover_data=['address', 'beds', 'baths'],
        title="🏡 Price vs Living Area Analysis",
        labels={
            'living_area': 'Living Area (sq ft)',
            'price': 'Price ($)',
            'classified_label': 'Classification'
        }
    )
    
    fig.update_layout(
        title_font_size=20,
        title_x=0.5,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    return fig

def run_pipeline():
    """Run the complete pipeline"""
    try:
        with st.spinner("🚀 Running real estate scraping pipeline..."):
            result = subprocess.run([
                sys.executable, "run_complete_pipeline.py"
            ], capture_output=True, text=True, cwd=".")
            
        if result.returncode == 0:
            st.success("✅ Pipeline completed successfully!")
            st.info("🔄 Data cache will refresh automatically in a few moments...")
            # Clear the cache to force data reload
            st.cache_data.clear()
            time.sleep(2)  # Give time for file system to update
            return True
        else:
            st.error(f"❌ Pipeline failed with error: {result.stderr}")
            return False
            
    except Exception as e:
        st.error(f"❌ Error running pipeline: {str(e)}")
        return False

def main():
    """Main dashboard function"""
    
    # Header
    st.markdown('<h1 class="main-header">🏠 Real Estate Intelligence Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown('<h2 class="sidebar-header">🎛️ Dashboard Controls</h2>', unsafe_allow_html=True)
        
        # Data refresh
        if st.button("🔄 Refresh Data", type="primary"):
            st.cache_data.clear()
            st.rerun()
        
        # Pipeline controls
        st.markdown("---")
        st.markdown("### 🕷️ Data Pipeline")
        
        if st.button("🚀 Run Pipeline", type="secondary"):
            if run_pipeline():
                st.rerun()
        
        st.markdown("---")
        
        # Data source selection
        st.markdown("### 📊 Data Source")
        data_source = st.radio(
            "Choose data source:",
            ["CSV File", "Database"],
            index=0
        )
        
        # Filters
        st.markdown("---")
        st.markdown("### 🔍 Filters")
        
    # Load data
    data = load_data()
    
    # Select data source
    if data_source == "CSV File":
        df = data['csv']
        last_updated = data['csv_modified']
        source_info = "📄 CSV File"
    else:
        df = data['database']
        last_updated = data['db_modified']
        source_info = "🗄️ Database"
    
    # Data status
    col1, col2 = st.columns([3, 1])
    with col1:
        if df is not None:
            st.markdown(f"""
            <div class="success-box">
                <strong>{source_info}</strong> - {len(df)} properties loaded
                {f"<br><small>Last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')}</small>" if last_updated else ""}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="warning-box">
                <strong>⚠️ No data available from {source_info}</strong><br>
                Run the pipeline to collect fresh data
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        if last_updated:
            time_diff = datetime.now() - last_updated
            if time_diff < timedelta(hours=1):
                st.success("🟢 Fresh")
            elif time_diff < timedelta(hours=24):
                st.warning("🟡 Recent")
            else:
                st.error("🔴 Stale")
    
    # Main content
    if df is not None and not df.empty:
        
        # Add filters to sidebar
        with st.sidebar:
            # Price range filter
            price_min, price_max = st.slider(
                "Price Range",
                min_value=int(df['price'].min()),
                max_value=int(df['price'].max()),
                value=(int(df['price'].min()), int(df['price'].max())),
                format="$%d"
            )
            
            # Classification filter
            classifications = ["All"] + list(df['classified_label'].unique())
            selected_classification = st.selectbox(
                "Classification",
                classifications
            )
            
            # Source filter
            sources = ["All"] + list(df['source'].unique())
            selected_source = st.selectbox(
                "Source",
                sources
            )
        
        # Apply filters
        filtered_df = df.copy()
        filtered_df = filtered_df[
            (filtered_df['price'] >= price_min) & 
            (filtered_df['price'] <= price_max)
        ]
        
        if selected_classification != "All":
            filtered_df = filtered_df[filtered_df['classified_label'] == selected_classification]
        
        if selected_source != "All":
            filtered_df = filtered_df[filtered_df['source'] == selected_source]
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📋 Properties", "📈 Analytics", "⚙️ Settings"])
        
        with tab1:
            st.markdown("## 📊 Property Overview")
            
            # Metrics
            create_overview_metrics(filtered_df)
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                fig1 = create_price_distribution_chart(filtered_df)
                if fig1:
                    st.plotly_chart(fig1, width='stretch')
            
            with col2:
                fig2 = create_classification_chart(filtered_df)
                if fig2:
                    st.plotly_chart(fig2, width='stretch')
            
            # Source comparison
            fig3 = create_source_comparison_chart(filtered_df)
            if fig3:
                st.plotly_chart(fig3, width='stretch')
        
        with tab2:
            st.markdown("## 📋 Property Listings")
            
            # Search
            search_term = st.text_input("🔍 Search properties (address, classification, etc.)")
            
            display_df = filtered_df.copy()
            if search_term:
                mask = display_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
                display_df = display_df[mask]
            
            # Sort options
            col1, col2 = st.columns(2)
            with col1:
                sort_by = st.selectbox("Sort by:", ["price", "score", "processed_at", "beds", "baths"])
            with col2:
                sort_order = st.selectbox("Order:", ["Descending", "Ascending"])
            
            ascending = sort_order == "Ascending"
            display_df = display_df.sort_values(by=sort_by, ascending=ascending)
            
            # Display properties
            st.markdown(f"**Showing {len(display_df)} properties**")
            
            for idx, row in display_df.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.markdown(f"""
                        **📍 {row['address']}**  
                        🏠 {row['beds']} bed, {row['baths']} bath  
                        📐 {row['living_area']} sq ft
                        """)
                    
                    with col2:
                        st.markdown(f"""
                        💰 **{format_currency(row['price'])}**  
                        🏷️ {row['classified_label']}  
                        ⭐ Score: {row['score']:.1f}
                        """)
                    
                    with col3:
                        st.markdown(f"""
                        📊 {row['source'].title()}  
                        🕐 {pd.to_datetime(row['processed_at']).strftime('%m/%d')}
                        """)
                    
                    st.markdown("---")
        
        with tab3:
            st.markdown("## 📈 Advanced Analytics")
            
            # Price vs Living Area scatter
            fig4 = create_scatter_plot(filtered_df)
            if fig4:
                st.plotly_chart(fig4, width='stretch')
            
            # Statistical summary
            st.markdown("### 📊 Statistical Summary")
            st.dataframe(filtered_df[['price', 'beds', 'baths', 'living_area', 'score']].describe(), width='stretch')
            
            # Correlation matrix
            if len(filtered_df) > 1:
                st.markdown("### 🔗 Correlation Analysis")
                corr_cols = ['price', 'beds', 'baths', 'living_area', 'score']
                corr_matrix = filtered_df[corr_cols].corr()
                
                fig_corr = px.imshow(
                    corr_matrix,
                    text_auto=True,
                    aspect="auto",
                    title="Property Features Correlation Matrix",
                    color_continuous_scale="RdBu_r"
                )
                st.plotly_chart(fig_corr, width='stretch')
        
        with tab4:
            st.markdown("## ⚙️ Settings & Configuration")
            
            # Export options
            st.markdown("### 📤 Export Data")
            col1, col2 = st.columns(2)
            
            with col1:
                csv_data = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📄 Download CSV",
                    data=csv_data,
                    file_name=f"real_estate_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                json_data = filtered_df.to_json(orient='records', indent=2)
                st.download_button(
                    label="📋 Download JSON",
                    data=json_data,
                    file_name=f"real_estate_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            # Pipeline settings
            st.markdown("### 🔧 Pipeline Configuration")
            
            # Show current .env settings
            env_path = "./.env"
            if os.path.exists(env_path):
                st.markdown("**Current Configuration:**")
                with open(env_path, 'r') as f:
                    env_content = f.read()
                st.code(env_content, language='bash')
            
            # Database info
            st.markdown("### 🗄️ Database Information")
            db_path = "./data/development_leads.db"
            if os.path.exists(db_path):
                db_size = os.path.getsize(db_path)
                db_modified = datetime.fromtimestamp(os.path.getmtime(db_path))
                st.info(f"""
                **Database Status:** ✅ Available  
                **Size:** {db_size / 1024:.1f} KB  
                **Last Modified:** {db_modified.strftime('%Y-%m-%d %H:%M:%S')}
                """)
            else:
                st.warning("⚠️ Database not found. Run the pipeline to create it.")
    
    else:
        # No data available - show getting started
        st.markdown("## 🚀 Getting Started")
        
        st.markdown("""
        ### Welcome to the Real Estate Intelligence Dashboard!
        
        It looks like you don't have any property data yet. Here's how to get started:
        
        1. **📥 Run the Pipeline**: Click the "🚀 Run Pipeline" button in the sidebar to scrape fresh property data
        2. **⏳ Wait for Processing**: The pipeline will collect data from multiple sources (Zillow, Redfin, Realtor)
        3. **📊 Explore Data**: Once complete, use the dashboard to analyze property trends and insights
        
        The pipeline includes:
        - 🕷️ **Web Scraping**: Automated data collection from real estate websites
        - 🏷️ **Classification**: AI-powered property categorization 
        - 📊 **Scoring**: Investment potential analysis
        - 💾 **Storage**: Data saved to CSV and SQLite database
        """)
        
        # Large run button
        if st.button("🚀 Run Your First Pipeline", type="primary", width='stretch'):
            if run_pipeline():
                st.rerun()

if __name__ == "__main__":
    main()