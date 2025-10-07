#!/usr/bin/env python3
"""
RFP AI - Multi-Agent System for B2B RFP Response Automation

This is the main entry point for the RFP AI system that orchestrates
multiple AI agents to automate the RFP response process.

Agents:
- Sales Agent: Scans URLs, identifies RFPs due within 3 months
- Technical Agent: Matches RFP requirements to product SKUs with spec matching
- Pricing Agent: Calculates material and service costs
- Master Agent: Orchestrates the entire process and consolidates responses

Usage:
    python main.py
"""

import json
import sys
import os
import argparse
from datetime import datetime

# Add the Agents directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'Agents'))

from master_agent import MasterAgent
from utils import print_section_header

def main():
    """
    Main function to run the RFP AI system
    """
    parser = argparse.ArgumentParser(description='RFP AI - Multi-Agent System for RFP Response Automation')
    parser.add_argument('--data-path', default='data/', help='Path to data directory (default: data/)')
    parser.add_argument('--save-response', action='store_true', help='Save RFP response to JSON file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Print welcome banner
    print_section_header("RFP AI - MULTI-AGENT SYSTEM")
    print("🤖 Automated B2B RFP Response System")
    print("📋 Industrial Cables & Electrical Products")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Initialize Master Agent with data path
        print("🚀 Initializing RFP AI System...")
        master_agent = MasterAgent(data_path=args.data_path)
        print("✅ All agents loaded successfully")
        print()
        
        # Execute the complete RFP response process
        print("🎯 Starting RFP response process...")
        response = master_agent.orchestrate_rfp_response()
        
        # Handle response
        if response.success:
            print("\n" + "="*80)
            print("🎉 RFP RESPONSE PROCESS COMPLETED SUCCESSFULLY!")
            print("="*80)
            
            # Save response if requested
            if args.save_response:
                output_file = master_agent.save_rfp_response(response)
                print(f"📄 Response saved to: {output_file}")
            
            # Print final status
            if response.final_recommendation:
                final_rec = response.final_recommendation
                cost_summary = final_rec.get("commercial_proposal", {}).get("cost_summary", {})
                if cost_summary:
                    print(f"\n💰 Final Bid Value: ₹{cost_summary.get('grand_total', 0):,.2f}")
                
                tech_summary = final_rec.get("technical_proposal", {}).get("summary", {})
                if tech_summary:
                    print(f"🎯 Match Success Rate: {tech_summary.get('match_success_rate', '0%')}")
            
            print("\n🏆 System is ready for RFP submission!")
            
        else:
            print("\n" + "="*80)
            print("❌ RFP RESPONSE PROCESS FAILED")
            print("="*80)
            print(f"Error: {response.message}")
            
            # Print debug information if verbose
            if args.verbose:
                if response.rfp_summary:
                    print(f"\nRFP ID: {response.rfp_summary.rfp_id}")
                if response.technical_analysis:
                    print(f"Technical Analysis: {'Success' if response.technical_analysis.success else 'Failed'}")
                if response.pricing_analysis:
                    print(f"Pricing Analysis: {'Success' if response.pricing_analysis.success else 'Failed'}")
            
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        return 1
        
    except Exception as e:
        print("\n" + "="*80)
        print("💥 SYSTEM ERROR")
        print("="*80)
        print(f"Unexpected error: {str(e)}")
        
        if args.verbose:
            import traceback
            print("\nFull traceback:")
            traceback.print_exc()
        
        return 1
    
    return 0

def demo_mode():
    """
    Run a quick demo of the system capabilities
    """
    print_section_header("RFP AI - DEMO MODE")
    print("🎭 Running demonstration with sample data...")
    print()
    
    # Initialize with sample data
    master_agent = MasterAgent(data_path="data/")
    
    # Show available RFPs
    print("📋 Sample RFPs in system:")
    sales_agent = master_agent.sales_agent
    rfps = sales_agent.scan_rfps()
    
    for i, rfp in enumerate(rfps, 1):
        print(f"  {i}. {rfp.rfp_id}: {rfp.title}")
        print(f"     Organization: {rfp.organization}")
        print(f"     Deadline: {rfp.submission_deadline}")
        print(f"     Value: ₹{rfp.project_value:,.0f}")
        print()
    
    print(f"🎯 System will automatically select the best RFP and generate complete response")
    
    # Run the process
    response = master_agent.orchestrate_rfp_response()
    
    if response.success:
        print("\n🎉 Demo completed successfully!")
        print("💡 The system has demonstrated end-to-end RFP response automation")
    else:
        print(f"\n❌ Demo failed: {response.message}")

if __name__ == "__main__":
    # Check if demo mode is requested
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_mode()
    else:
        exit_code = main()
        sys.exit(exit_code)
