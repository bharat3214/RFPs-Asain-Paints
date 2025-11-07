import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import sys
import os
from datetime import datetime, date
import time

# Add the Agents directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'Agents'))

from master_agent import MasterAgent
from utils import format_currency, days_until_deadline

# Page configuration
st.set_page_config(
    page_title="RFP AI - Multi-Agent System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .agent-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 0.25rem;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 0.25rem;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'master_agent' not in st.session_state:
        st.session_state.master_agent = None
    if 'current_response' not in st.session_state:
        st.session_state.current_response = None
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'selected_rfp_details' not in st.session_state:
        st.session_state.selected_rfp_details = None

def load_sample_data():
    """Load sample data for display"""
    try:
        with open('data/rfps.json', 'r') as f:
            rfp_data = json.load(f)
        with open('data/products.json', 'r') as f:
            product_data = json.load(f)
        with open('data/pricing.json', 'r') as f:
            pricing_data = json.load(f)
        return rfp_data, product_data, pricing_data
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None, None

def display_agent_status(agent_name, status, message="", progress=0):
    """Display agent processing status"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if status == "running":
            st.info(f"🔄 {agent_name} is processing...")
            if progress > 0:
                st.progress(progress)
        elif status == "success":
            st.success(f"✅ {agent_name} completed successfully")
            if message:
                st.write(message)
        elif status == "error":
            st.error(f"❌ {agent_name} failed: {message}")

def create_rfp_overview_chart(rfps):
    """Create RFP overview visualization"""
    if not rfps or 'sample_rfps' not in rfps:
        return None
        
    rfp_list = rfps['sample_rfps']
    
    # Create DataFrame for visualization
    df = pd.DataFrame([{
        'RFP_ID': rfp['rfp_id'],
        'Organization': rfp['organization'],
        'Project_Value': rfp['project_value'],
        'Days_Until_Deadline': days_until_deadline(datetime.strptime(rfp['submission_deadline'], '%Y-%m-%d').date()),
        'Status': 'Available'
    } for rfp in rfp_list])
    
    # Create bubble chart
    fig = px.scatter(df, 
                    x='Days_Until_Deadline', 
                    y='Project_Value',
                    size='Project_Value',
                    color='Organization',
                    hover_name='RFP_ID',
                    title="RFP Portfolio Overview",
                    labels={'Days_Until_Deadline': 'Days Until Deadline',
                           'Project_Value': 'Project Value (₹)'})
    
    fig.update_layout(height=400)
    return fig

def create_technical_analysis_chart(technical_response):
    """Create technical analysis visualization"""
    if not technical_response or not technical_response.success:
        return None
    
    # Extract match percentages
    matches = []
    for rec in technical_response.product_recommendations:
        matches.append({
            'Item': rec.requirement_item_no,
            'Product': rec.selected_sku,
            'Match_Percentage': rec.selected_match_percentage,
            'Description': rec.requirement_description[:30] + "..."
        })
    
    df = pd.DataFrame(matches)
    
    # Create bar chart
    fig = px.bar(df, 
                x='Item', 
                y='Match_Percentage',
                color='Match_Percentage',
                title="Product Specification Match Analysis",
                labels={'Match_Percentage': 'Match Percentage (%)',
                       'Item': 'RFP Item Number'},
                color_continuous_scale='RdYlGn')
    
    fig.update_layout(height=400)
    return fig

def create_cost_breakdown_chart(pricing_response):
    """Create cost breakdown visualization"""
    if not pricing_response or not pricing_response.success:
        return None
    
    # Create pie chart for cost breakdown
    costs = {
        'Material Costs': pricing_response.total_material_cost,
        'Testing Costs': pricing_response.total_testing_cost,
        'Margin & Others': pricing_response.grand_total - pricing_response.total_material_cost - pricing_response.total_testing_cost
    }
    
    fig = px.pie(values=list(costs.values()), 
                names=list(costs.keys()),
                title="Cost Breakdown Analysis")
    
    fig.update_layout(height=400)
    return fig

def main():
    """Main Streamlit application"""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🤖 RFP AI - Multi-Agent System</h1>', unsafe_allow_html=True)
    st.markdown("### Automated B2B RFP Response for Industrial Cables & Electrical Products")
    
    # Sidebar
    st.sidebar.title("🎛️ Control Panel")
    
    # Navigation
    page = st.sidebar.selectbox("Navigate to:", [
        "🏠 Dashboard", 
        "📋 RFP Analysis", 
        "🔧 Technical Matching", 
        "💰 Pricing Analysis",
        "📊 Data Explorer",
        "⚙️ System Settings"
    ])
    
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "📋 RFP Analysis":
        show_rfp_analysis()
    elif page == "🔧 Technical Matching":
        show_technical_analysis()
    elif page == "💰 Pricing Analysis":
        show_pricing_analysis()
    elif page == "📊 Data Explorer":
        show_data_explorer()
    elif page == "⚙️ System Settings":
        show_system_settings()

def show_dashboard():
    """Main dashboard view"""
    st.header("📊 System Dashboard")
    
    # Load sample data
    rfp_data, product_data, pricing_data = load_sample_data()
    
    if rfp_data:
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>Available RFPs</h3>
                <h2>{}</h2>
            </div>
            """.format(len(rfp_data.get('sample_rfps', []))), unsafe_allow_html=True)
        
        with col2:
            total_value = sum([rfp.get('project_value', 0) for rfp in rfp_data.get('sample_rfps', [])])
            st.markdown("""
            <div class="metric-card">
                <h3>Total Pipeline</h3>
                <h2>{}</h2>
            </div>
            """.format(format_currency(total_value)), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>Product SKUs</h3>
                <h2>{}</h2>
            </div>
            """.format(len(product_data.get('products', [])) if product_data else 0), unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-card">
                <h3>System Status</h3>
                <h2>🟢 Active</h2>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # RFP Overview Chart
        fig = create_rfp_overview_chart(rfp_data)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        # Quick Actions
        st.subheader("🚀 Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔍 Run Complete RFP Analysis", key="run_analysis", help="Execute the full multi-agent RFP analysis"):
                run_complete_analysis()
        
        with col2:
            if st.button("📊 View Sample Reports", key="sample_reports"):
                show_sample_reports()
        
        with col3:
            if st.button("⚙️ System Configuration", key="system_config"):
                st.switch_page("⚙️ System Settings")

def run_complete_analysis():
    """Run the complete RFP analysis process"""
    st.subheader("🔄 Running Complete RFP Analysis")
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Initialize Master Agent
        status_text.text("Initializing RFP AI System...")
        progress_bar.progress(10)
        time.sleep(1)
        
        if not st.session_state.master_agent:
            st.session_state.master_agent = MasterAgent(data_path="data/")
        
        # Phase 1: Sales Agent
        status_text.text("Phase 1: Scanning and selecting RFPs...")
        progress_bar.progress(25)
        time.sleep(1)
        
        # Phase 2: Technical Agent
        status_text.text("Phase 2: Analyzing product specifications...")
        progress_bar.progress(50)
        time.sleep(1)
        
        # Phase 3: Pricing Agent
        status_text.text("Phase 3: Calculating costs and pricing...")
        progress_bar.progress(75)
        time.sleep(1)
        
        # Phase 4: Consolidation
        status_text.text("Phase 4: Consolidating final response...")
        progress_bar.progress(90)
        
        # Execute the analysis
        response = st.session_state.master_agent.orchestrate_rfp_response()
        
        progress_bar.progress(100)
        status_text.text("✅ Analysis completed successfully!")
        
        # Store response in session state
        st.session_state.current_response = response
        st.session_state.processing_complete = True
        
        if response.success:
            st.success("🎉 RFP Analysis Completed Successfully!")
            
            # Display key results
            if response.final_recommendation:
                final_rec = response.final_recommendation
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Selected RFP",
                        final_rec["rfp_information"]["rfp_id"],
                        final_rec["rfp_information"]["organization"]
                    )
                
                with col2:
                    cost_summary = final_rec.get("commercial_proposal", {}).get("cost_summary", {})
                    st.metric(
                        "Total Bid Value",
                        format_currency(cost_summary.get("grand_total", 0)),
                        "Ready for submission"
                    )
                
                with col3:
                    tech_summary = final_rec.get("technical_proposal", {}).get("summary", {})
                    st.metric(
                        "Match Success Rate",
                        tech_summary.get("match_success_rate", "0%"),
                        "Specification compliance"
                    )
                
                # Show detailed results button
                if st.button("📋 View Detailed Results"):
                    show_detailed_results(response)
        else:
            st.error(f"❌ Analysis failed: {response.message}")
            
    except Exception as e:
        st.error(f"💥 System error: {str(e)}")
        progress_bar.progress(0)
        status_text.text("❌ Analysis failed")

def show_detailed_results(response):
    """Show detailed analysis results"""
    st.subheader("📋 Detailed Analysis Results")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Executive Summary", "🔧 Technical Analysis", "💰 Pricing Breakdown", "📄 Raw Data"])
    
    with tab1:
        show_executive_summary(response)
    
    with tab2:
        show_technical_details(response)
    
    with tab3:
        show_pricing_details(response)
    
    with tab4:
        show_raw_data(response)

def show_executive_summary(response):
    """Show executive summary of results"""
    if not response.success:
        st.error("Analysis was not successful")
        return
    
    final_rec = response.final_recommendation
    rfp_info = final_rec["rfp_information"]
    
    st.markdown("### 📋 RFP Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**RFP ID:** {rfp_info['rfp_id']}")
        st.write(f"**Organization:** {rfp_info['organization']}")
        st.write(f"**Submission Deadline:** {rfp_info['submission_deadline']}")
    
    with col2:
        st.write(f"**Project Value:** {format_currency(rfp_info['project_value'])}")
        st.write(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"**Status:** ✅ Ready for Submission")
    
    st.markdown("### 🎯 Key Recommendations")
    
    business_metrics = final_rec.get("business_metrics", {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Bid Value", format_currency(business_metrics.get("total_bid_value", 0)))
    
    with col2:
        st.metric("Estimated Margin", business_metrics.get("margin_percentage", "0%"))
    
    with col3:
        st.metric("Competitive Position", "Strong", "High win probability")
    
    # Recommendation
    st.markdown("### 🏆 Final Recommendation")
    st.success("**PROCEED WITH RFP SUBMISSION** - All requirements can be fulfilled with competitive pricing and healthy margins.")
    
    # Competitive advantages
    if "competitive_advantages" in business_metrics:
        st.markdown("### 💪 Competitive Advantages")
        for advantage in business_metrics["competitive_advantages"]:
            st.write(f"✅ {advantage}")

def show_technical_details(response):
    """Show technical analysis details"""
    if not response.technical_analysis or not response.technical_analysis.success:
        st.error("Technical analysis was not successful")
        return
    
    technical_response = response.technical_analysis
    
    st.markdown("### 🔧 Product Matching Results")
    
    # Create visualization
    fig = create_technical_analysis_chart(technical_response)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed product recommendations
    st.markdown("### 📦 Selected Products")
    
    for rec in technical_response.product_recommendations:
        with st.expander(f"Item {rec.requirement_item_no}: {rec.requirement_description}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Selected SKU:** {rec.selected_sku}")
                st.write(f"**Match Score:** {rec.selected_match_percentage:.1f}%")
            
            with col2:
                if rec.top_matches:
                    selected_product = rec.top_matches[0]
                    st.write(f"**Product Name:** {selected_product.product_name}")
                    st.write(f"**Match Details:** {len(selected_product.matched_specs)} specs matched")
            
            # Show all top matches
            if rec.top_matches:
                st.markdown("**Top 3 Matches:**")
                match_data = []
                for i, match in enumerate(rec.top_matches[:3], 1):
                    match_data.append({
                        'Rank': i,
                        'SKU': match.sku,
                        'Product Name': match.product_name,
                        'Match %': f"{match.match_percentage:.1f}%"
                    })
                
                st.dataframe(pd.DataFrame(match_data), use_container_width=True)

def show_pricing_details(response):
    """Show pricing analysis details"""
    if not response.pricing_analysis or not response.pricing_analysis.success:
        st.error("Pricing analysis was not successful")
        return
    
    pricing_response = response.pricing_analysis
    
    st.markdown("### 💰 Cost Analysis")
    
    # Create cost breakdown visualization
    fig = create_cost_breakdown_chart(pricing_response)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Material Costs", format_currency(pricing_response.total_material_cost))
    
    with col2:
        st.metric("Testing Costs", format_currency(pricing_response.total_testing_cost))
    
    with col3:
        st.metric("Grand Total", format_currency(pricing_response.grand_total))
    
    # Detailed breakdown
    st.markdown("### 📋 Detailed Pricing Breakdown")
    
    pricing_data = []
    for breakdown in pricing_response.pricing_breakdown:
        pricing_data.append({
            'SKU': breakdown.sku,
            'Quantity': f"{breakdown.quantity:,}",
            'Unit Price': format_currency(breakdown.unit_price),
            'Material Cost': format_currency(breakdown.total_material_cost),
            'Testing Cost': format_currency(breakdown.total_testing_cost),
            'Total Cost': format_currency(breakdown.total_cost)
        })
    
    st.dataframe(pd.DataFrame(pricing_data), use_container_width=True)
    
    # Testing breakdown
    st.markdown("### 🧪 Testing Cost Details")
    for breakdown in pricing_response.pricing_breakdown:
        if breakdown.testing_costs:
            with st.expander(f"Testing costs for {breakdown.sku}"):
                for test_name, cost in breakdown.testing_costs.items():
                    st.write(f"**{test_name}:** {format_currency(cost)}")

def show_raw_data(response):
    """Show raw response data"""
    if not response:
        st.error("No response data available")
        return
    
    st.markdown("### 📄 Raw Response Data")
    st.json(response.final_recommendation)

def show_rfp_analysis():
    """RFP Analysis page"""
    st.header("📋 RFP Analysis & Selection")
    
    # Load and display RFP data
    rfp_data, _, _ = load_sample_data()
    
    if rfp_data and 'sample_rfps' in rfp_data:
        st.subheader("Available RFPs")
        
        # Create RFP overview table
        rfp_list = rfp_data['sample_rfps']
        rfp_df = pd.DataFrame([{
            'RFP ID': rfp['rfp_id'],
            'Title': rfp['title'],
            'Organization': rfp['organization'],
            'Deadline': rfp['submission_deadline'],
            'Project Value': format_currency(rfp['project_value']),
            'Days Remaining': days_until_deadline(datetime.strptime(rfp['submission_deadline'], '%Y-%m-%d').date())
        } for rfp in rfp_list])
        
        st.dataframe(rfp_df, use_container_width=True)
        
        # RFP selection
        st.subheader("🎯 RFP Selection Criteria")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Selection Algorithm", "Multi-factor Scoring")
            st.write("**Factors:**")
            st.write("- Project value (40%)")
            st.write("- Time availability (30%)")
            st.write("- Organization type (20%)")
            st.write("- Product complexity (10%)")
        
        with col2:
            if st.button("🔍 Run RFP Selection Analysis"):
                with st.spinner("Analyzing RFPs..."):
                    # Simulate RFP analysis
                    time.sleep(2)
                    st.success("Analysis complete! RFP-2024-001 selected based on highest score.")
                    
                    # Show selection details
                    st.write("**Selection Results:**")
                    selection_data = [
                        {'RFP': 'RFP-2024-001', 'Score': 72.0, 'Recommendation': '🏆 Selected'},
                        {'RFP': 'RFP-2024-002', 'Score': 54.3, 'Recommendation': '⚠️ Backup'},
                        {'RFP': 'RFP-2024-003', 'Score': 47.7, 'Recommendation': '❌ Not selected'}
                    ]
                    st.dataframe(pd.DataFrame(selection_data), use_container_width=True)

def show_technical_analysis():
    """Technical Analysis page"""
    st.header("🔧 Technical Specification Matching")
    
    # Load product data
    _, product_data, _ = load_sample_data()
    
    if product_data and 'products' in product_data:
        st.subheader("Product Catalog Overview")
        
        # Create product overview
        products = product_data['products']
        product_df = pd.DataFrame([{
            'SKU': product['sku'],
            'Product Name': product['product_name'],
            'Category': product['category'].title(),
            'Manufacturer': product['manufacturer'],
            'Unit Price': format_currency(product['unit_price']),
            'Availability': '✅' if product['availability'] else '❌'
        } for product in products])
        
        st.dataframe(product_df, use_container_width=True)
        
        # Specification matching demo
        st.subheader("🎯 Specification Matching Algorithm")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Matching Criteria:**")
            st.write("- Voltage rating compatibility")
            st.write("- Conductor material match")
            st.write("- Cross-section adequacy")
            st.write("- Standard compliance")
            st.write("- Temperature rating")
        
        with col2:
            st.write("**Scoring Method:**")
            st.code("""
def calculate_match_score(rfp_spec, product_spec):
    total_specs = len(rfp_spec)
    matched = 0
    
    for spec, value in rfp_spec.items():
        if spec in product_spec:
            if meets_requirement(value, product_spec[spec]):
                matched += 1
    
    return (matched / total_specs) * 100
            """)
        
        # Interactive matching test
        st.subheader("🧪 Interactive Specification Test")
        
        selected_product = st.selectbox("Select a product to analyze:", 
                                      [p['sku'] + " - " + p['product_name'] for p in products])
        
        if selected_product:
            sku = selected_product.split(" - ")[0]
            product = next((p for p in products if p['sku'] == sku), None)
            
            if product:
                st.write("**Product Specifications:**")
                spec_df = pd.DataFrame([
                    {'Specification': k, 'Value': v} 
                    for k, v in product['specifications'].items()
                ])
                st.dataframe(spec_df, use_container_width=True)

def show_pricing_analysis():
    """Pricing Analysis page"""
    st.header("💰 Pricing & Cost Analysis")
    
    # Load pricing data
    _, _, pricing_data = load_sample_data()
    
    if pricing_data:
        st.subheader("Pricing Structure Overview")
        
        # Base prices
        if 'material_pricing' in pricing_data and 'base_prices' in pricing_data['material_pricing']:
            st.write("**Base Product Prices:**")
            base_prices = pricing_data['material_pricing']['base_prices']
            price_df = pd.DataFrame([
                {'SKU': sku, 'Base Price': format_currency(price)}
                for sku, price in base_prices.items()
            ])
            st.dataframe(price_df, use_container_width=True)
        
        # Quantity discounts
        st.subheader("📊 Quantity Discount Structure")
        
        if 'material_pricing' in pricing_data and 'quantity_discounts' in pricing_data['material_pricing']:
            discounts = pricing_data['material_pricing']['quantity_discounts']
            discount_df = pd.DataFrame([
                {'Quantity Range': qty_range, 'Discount %': f"{discount*100:.0f}%"}
                for qty_range, discount in discounts.items()
            ])
            st.dataframe(discount_df, use_container_width=True)
        
        # Testing costs
        st.subheader("🧪 Testing & Certification Costs")
        
        if 'testing_services' in pricing_data:
            testing_services = pricing_data['testing_services']
            
            tab1, tab2, tab3 = st.tabs(["Routine Tests", "Type Tests", "Specialized Tests"])
            
            with tab1:
                if 'routine_tests' in testing_services:
                    routine_df = pd.DataFrame([
                        {'Test Name': name, 'Cost per Sample': format_currency(details['cost_per_sample'])}
                        for name, details in testing_services['routine_tests'].items()
                    ])
                    st.dataframe(routine_df, use_container_width=True)
            
            with tab2:
                if 'type_tests' in testing_services:
                    type_df = pd.DataFrame([
                        {'Test Name': name, 'Cost per Sample': format_currency(details['cost_per_sample'])}
                        for name, details in testing_services['type_tests'].items()
                    ])
                    st.dataframe(type_df, use_container_width=True)
            
            with tab3:
                if 'specialized_tests' in testing_services:
                    spec_df = pd.DataFrame([
                        {'Test Name': name, 'Cost per Sample': format_currency(details['cost_per_sample'])}
                        for name, details in testing_services['specialized_tests'].items()
                    ])
                    st.dataframe(spec_df, use_container_width=True)
        
        # Cost calculation simulator
        st.subheader("🧮 Cost Calculator")
        
        col1, col2 = st.columns(2)
        
        with col1:
            quantity = st.number_input("Quantity", min_value=1, max_value=50000, value=5000)
            base_price = st.number_input("Base Price (₹)", min_value=1.0, max_value=10000.0, value=850.0)
        
        with col2:
            # Calculate discount
            discount = 0.0
            if quantity >= 25000:
                discount = 0.15
            elif quantity >= 10000:
                discount = 0.12
            elif quantity >= 5000:
                discount = 0.08
            elif quantity >= 1000:
                discount = 0.05
            
            discounted_price = base_price * (1 - discount)
            total_cost = discounted_price * quantity
            
            st.metric("Applicable Discount", f"{discount*100:.0f}%")
            st.metric("Final Unit Price", format_currency(discounted_price))
            st.metric("Total Material Cost", format_currency(total_cost))

def show_data_explorer():
    """Data Explorer page"""
    st.header("📊 Data Explorer")
    
    tab1, tab2, tab3 = st.tabs(["RFP Data", "Product Catalog", "Pricing Matrix"])
    
    with tab1:
        st.subheader("RFP Database")
        rfp_data, _, _ = load_sample_data()
        if rfp_data:
            st.json(rfp_data)
    
    with tab2:
        st.subheader("Product Specifications")
        _, product_data, _ = load_sample_data()
        if product_data:
            st.json(product_data)
    
    with tab3:
        st.subheader("Pricing Configuration")
        _, _, pricing_data = load_sample_data()
        if pricing_data:
            st.json(pricing_data)

def show_system_settings():
    """System Settings page"""
    st.header("⚙️ System Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Agent Configuration")
        st.selectbox("Sales Agent Lookahead", ["30 days", "60 days", "90 days"], index=2)
        st.slider("Technical Match Threshold", 0, 100, 30, help="Minimum match percentage to consider")
        st.selectbox("Pricing Margin Strategy", ["Conservative (15%)", "Standard (10%)", "Aggressive (8%)"], index=1)
    
    with col2:
        st.subheader("Data Sources")
        st.text_input("RFP Data Path", value="data/rfps.json")
        st.text_input("Product Data Path", value="data/products.json")
        st.text_input("Pricing Data Path", value="data/pricing.json")
        
        st.subheader("Output Settings")
        st.checkbox("Auto-save responses", value=True)
        st.checkbox("Enable detailed logging", value=False)
        st.selectbox("Output format", ["JSON", "Excel", "PDF"])
    
    if st.button("💾 Save Configuration"):
        st.success("Configuration saved successfully!")

def show_sample_reports():
    """Show sample reports from previous analyses"""
    st.subheader("📊 Sample Analysis Reports")
    
    # Check if we have a saved response
    try:
        with open('data/rfp_response_RFP-2024-001_20251007_221044.json', 'r') as f:
            sample_response = json.load(f)
        
        st.success("Found previous analysis report!")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Analysis Date", "2025-10-07")
        with col2:
            st.metric("RFP Processed", "RFP-2024-001")
        with col3:
            st.metric("Status", "✅ Successful")
        
        if st.button("📋 View Full Report"):
            st.json(sample_response)
            
    except FileNotFoundError:
        st.info("No previous analysis reports found. Run an analysis to generate reports.")

if __name__ == "__main__":
    main()