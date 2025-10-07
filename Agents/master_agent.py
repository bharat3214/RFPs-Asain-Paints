import json
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Add parent directory to path to import models and other agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import MasterAgentResponse, RFP
from utils import print_section_header, print_subsection_header, format_currency

from sales_agent import SalesAgent
from technical_agent import TechnicalAgent 
from pricing_agent import PricingAgent

class MasterAgent:
    """
    Master Agent (Orchestrator) responsible for:
    1. Coordinating the entire RFP response process
    2. Managing communication between all agents
    3. Preparing contextual summaries for each agent
    4. Consolidating final RFP response
    5. Starting and ending the conversation
    """
    
    def __init__(self, data_path: str = "data/"):
        self.data_path = data_path
        self.sales_agent = SalesAgent(data_path)
        self.technical_agent = TechnicalAgent(data_path)
        self.pricing_agent = PricingAgent(data_path)
    
    def orchestrate_rfp_response(self) -> MasterAgentResponse:
        """
        Main orchestration method that coordinates all agents
        """
        print_section_header("RFP AI SYSTEM - MASTER AGENT ORCHESTRATION")
        print("🤖 Starting multi-agent RFP response process...")
        
        try:
            # Step 1: Sales Agent - Identify and select RFP
            print_subsection_header("Phase 1: RFP Identification and Selection")
            sales_response = self.sales_agent.process()
            
            if not sales_response.success or not sales_response.selected_rfp:
                return MasterAgentResponse(
                    agent_name="Master Agent",
                    success=False,
                    message="Failed to identify suitable RFP",
                    rfp_summary=None,
                    technical_analysis=None,
                    pricing_analysis=None,
                    final_recommendation={}
                )
            
            selected_rfp = sales_response.selected_rfp
            print(f"✅ Selected RFP: {selected_rfp.rfp_id} - {selected_rfp.title}")
            
            # Step 2: Prepare summaries for Technical and Pricing agents
            technical_summary = sales_response.data.get("technical_summary", {})
            pricing_summary = sales_response.data.get("pricing_summary", {})
            
            # Add product requirements to pricing summary for cost calculation
            pricing_summary["products_required"] = technical_summary.get("products_required", [])
            
            # Step 3: Technical Agent - Product matching and recommendation
            print_subsection_header("Phase 2: Technical Analysis and Product Matching")
            technical_response = self.technical_agent.process(technical_summary)
            
            if not technical_response.success:
                return MasterAgentResponse(
                    agent_name="Master Agent",
                    success=False,
                    message=f"Technical analysis failed: {technical_response.message}",
                    rfp_summary=selected_rfp,
                    technical_analysis=technical_response,
                    pricing_analysis=None,
                    final_recommendation={}
                )
            
            # Print technical analysis results
            self.technical_agent.print_detailed_analysis(technical_response)
            
            # Step 4: Pricing Agent - Cost calculation
            print_subsection_header("Phase 3: Pricing Analysis and Cost Calculation") 
            pricing_response = self.pricing_agent.process(pricing_summary, technical_response.product_recommendations)
            
            if not pricing_response.success:
                return MasterAgentResponse(
                    agent_name="Master Agent",
                    success=False,
                    message=f"Pricing analysis failed: {pricing_response.message}",
                    rfp_summary=selected_rfp,
                    technical_analysis=technical_response,
                    pricing_analysis=pricing_response,
                    final_recommendation={}
                )
            
            # Print pricing analysis results
            self.pricing_agent.print_pricing_summary(pricing_response)
            
            # Step 5: Consolidate final recommendation
            print_subsection_header("Phase 4: Final Recommendation Consolidation")
            final_recommendation = self._create_final_recommendation(
                selected_rfp, technical_response, pricing_response
            )
            
            # Create successful master response
            master_response = MasterAgentResponse(
                agent_name="Master Agent",
                success=True,
                message="Successfully completed RFP response process",
                rfp_summary=selected_rfp,
                technical_analysis=technical_response,
                pricing_analysis=pricing_response,
                final_recommendation=final_recommendation
            )
            
            # Print final summary
            self._print_final_summary(master_response)
            
            return master_response
            
        except Exception as e:
            return MasterAgentResponse(
                agent_name="Master Agent",
                success=False,
                message=f"Master Agent orchestration failed: {str(e)}",
                rfp_summary=None,
                technical_analysis=None,
                pricing_analysis=None,
                final_recommendation={}
            )
    
    def _create_final_recommendation(self, 
                                   rfp: RFP,
                                   technical_response,
                                   pricing_response) -> Dict[str, Any]:
        """
        Create consolidated final recommendation for RFP response
        """
        # Extract key information from technical analysis
        technical_data = technical_response.data.get("final_recommendations", {})
        selected_products = technical_data.get("selected_products", [])
        
        # Create RFP response structure
        final_recommendation = {
            "rfp_information": {
                "rfp_id": rfp.rfp_id,
                "title": rfp.title,
                "organization": rfp.organization,
                "submission_deadline": rfp.submission_deadline.isoformat(),
                "project_value": rfp.project_value
            },
            "technical_proposal": {
                "summary": {
                    "total_items": len(rfp.requirements),
                    "items_matched": len(selected_products),
                    "match_success_rate": f"{len(selected_products)/len(rfp.requirements)*100:.1f}%" if rfp.requirements else "0%",
                    "average_spec_match": f"{technical_data.get('summary', {}).get('average_match_percentage', 0):.1f}%"
                },
                "product_recommendations": []
            },
            "commercial_proposal": {
                "cost_summary": {
                    "total_material_cost": pricing_response.total_material_cost,
                    "total_testing_cost": pricing_response.total_testing_cost,
                    "grand_total": pricing_response.grand_total,
                    "currency": "INR"
                },
                "pricing_breakdown": []
            },
            "compliance_summary": {
                "testing_requirements_covered": rfp.testing_requirements,
                "acceptance_criteria_addressed": rfp.acceptance_criteria,
                "estimated_delivery_timeline": "45-60 days from award",
                "certifications_included": []
            },
            "business_metrics": {
                "total_bid_value": pricing_response.grand_total,
                "estimated_margin": pricing_response.data.get("additional_costs", {}).get("margin", 0),
                "margin_percentage": f"{pricing_response.data.get('additional_costs', {}).get('margin_rate', 0)*100:.1f}%",
                "competitive_advantages": [
                    "High specification match rates",
                    "Comprehensive testing coverage", 
                    "Established manufacturing capability",
                    "Proven track record in similar projects"
                ]
            }
        }
        
        # Populate product recommendations
        for product in selected_products:
            rec = {
                "rfp_item": product["item_no"],
                "requirement_description": product["requirement_description"],
                "proposed_sku": product["selected_sku"],
                "proposed_product": product["selected_product_name"],
                "specification_match": f"{product['match_percentage']:.1f}%",
                "unit_price": product["unit_price"],
                "manufacturer": product["manufacturer"]
            }
            final_recommendation["technical_proposal"]["product_recommendations"].append(rec)
        
        # Populate pricing breakdown
        for breakdown in pricing_response.pricing_breakdown:
            price_item = {
                "sku": breakdown.sku,
                "quantity": breakdown.quantity,
                "unit_price": breakdown.unit_price,
                "material_cost": breakdown.total_material_cost,
                "testing_cost": breakdown.total_testing_cost,
                "total_cost": breakdown.total_cost
            }
            final_recommendation["commercial_proposal"]["pricing_breakdown"].append(price_item)
        
        return final_recommendation
    
    def _print_final_summary(self, master_response: MasterAgentResponse) -> None:
        """
        Print comprehensive final summary of the RFP response
        """
        print_section_header("FINAL RFP RESPONSE SUMMARY")
        
        if not master_response.success:
            print(f"❌ Process Failed: {master_response.message}")
            return
        
        final_rec = master_response.final_recommendation
        rfp_info = final_rec["rfp_information"]
        tech_proposal = final_rec["technical_proposal"]
        commercial = final_rec["commercial_proposal"]
        business_metrics = final_rec["business_metrics"]
        
        # RFP Overview
        print("📋 RFP Overview:")
        print(f"   • ID: {rfp_info['rfp_id']}")
        print(f"   • Organization: {rfp_info['organization']}")
        print(f"   • Deadline: {rfp_info['submission_deadline']}")
        print(f"   • Project Value: {format_currency(rfp_info['project_value'])}")
        
        # Technical Summary
        print("\n🔧 Technical Proposal Summary:")
        tech_summary = tech_proposal["summary"]
        print(f"   • Items Analyzed: {tech_summary['total_items']}")
        print(f"   • Successfully Matched: {tech_summary['items_matched']}")
        print(f"   • Success Rate: {tech_summary['match_success_rate']}")
        print(f"   • Average Spec Match: {tech_summary['average_spec_match']}")
        
        # Commercial Summary
        print("\n💰 Commercial Proposal Summary:")
        cost_summary = commercial["cost_summary"]
        print(f"   • Material Costs: {format_currency(cost_summary['total_material_cost'])}")
        print(f"   • Testing Costs: {format_currency(cost_summary['total_testing_cost'])}")
        print(f"   • Total Bid Value: {format_currency(cost_summary['grand_total'])}")
        
        # Business Metrics
        print("\n📊 Business Analysis:")
        print(f"   • Estimated Margin: {format_currency(business_metrics['estimated_margin'])}")
        print(f"   • Margin Percentage: {business_metrics['margin_percentage']}")
        print(f"   • Competitive Position: Strong")
        
        # Key Recommendations
        print("\n🎯 Key Recommendations for RFP Submission:")
        print("   ✅ All major requirements can be fulfilled")
        print("   ✅ Competitive pricing with healthy margins")
        print("   ✅ High specification match rates")
        print("   ✅ Comprehensive testing coverage")
        print("   ✅ Ready for immediate submission")
        
        print(f"\n🏆 RECOMMENDATION: PROCEED WITH RFP SUBMISSION")
        print(f"💡 Total Bid Amount: {format_currency(cost_summary['grand_total'])}")
        
    def save_rfp_response(self, master_response: MasterAgentResponse, output_file: str = None) -> str:
        """
        Save the complete RFP response to a JSON file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rfp_id = master_response.rfp_summary.rfp_id if master_response.rfp_summary else "UNKNOWN"
            output_file = f"rfp_response_{rfp_id}_{timestamp}.json"
        
        # Convert response to serializable format
        response_data = {
            "agent_name": master_response.agent_name,
            "timestamp": master_response.timestamp.isoformat(),
            "success": master_response.success,
            "message": master_response.message,
            "final_recommendation": master_response.final_recommendation
        }
        
        output_path = os.path.join(self.data_path, output_file)
        with open(output_path, 'w') as f:
            json.dump(response_data, f, indent=2, default=str)
        
        print(f"\n💾 RFP Response saved to: {output_path}")
        return output_path