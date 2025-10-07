import json
import sys
import os
from typing import List, Dict, Any, Optional, Tuple

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    ProductSpecification, SpecMatch, ProductRecommendation, 
    TechnicalAgentResponse, ProductCategory
)
from utils import (
    load_json_data, calculate_spec_match_percentage, 
    print_section_header, print_subsection_header
)

class TechnicalAgent:
    """
    Technical Agent responsible for:
    1. Receiving RFP product requirements from Master Agent
    2. Matching RFP requirements to product SKUs with spec matching
    3. Calculating match percentages and creating recommendations
    4. Generating comparison tables for top 3 product matches
    """
    
    def __init__(self, data_path: str = "data/"):
        self.data_path = data_path
        self.products = self._load_products()
    
    def _load_products(self) -> List[ProductSpecification]:
        """Load product specifications from JSON file"""
        product_data = load_json_data(os.path.join(self.data_path, "products.json"))
        products = []
        
        if "products" in product_data:
            for product_dict in product_data["products"]:
                product = ProductSpecification(**product_dict)
                products.append(product)
        
        return products
    
    def analyze_rfp_requirements(self, technical_summary: Dict[str, Any]) -> List[ProductRecommendation]:
        """
        Analyze each RFP requirement and find matching products
        """
        print_section_header("Technical Agent - Product Matching Analysis")
        
        recommendations = []
        
        for req in technical_summary["products_required"]:
            print_subsection_header(f"Analyzing Item {req['item_no']}: {req['description']}")
            
            # Find matching products for this requirement
            matches = self._find_matching_products(req)
            
            # Select top 3 matches
            top_matches = matches[:3] if len(matches) >= 3 else matches
            
            # Select the best match (highest percentage)
            selected_sku = top_matches[0].sku if top_matches else None
            selected_match_percentage = top_matches[0].match_percentage if top_matches else 0.0
            
            recommendation = ProductRecommendation(
                requirement_item_no=req["item_no"],
                requirement_description=req["description"],
                top_matches=top_matches,
                selected_sku=selected_sku,
                selected_match_percentage=selected_match_percentage
            )
            
            recommendations.append(recommendation)
            
            # Print analysis results
            print(f"📊 Found {len(matches)} potential matches")
            for i, match in enumerate(top_matches, 1):
                print(f"  {i}. {match.sku} - {match.product_name} ({match.match_percentage:.1f}% match)")
            
            if selected_sku:
                print(f"🎯 Selected: {selected_sku} ({selected_match_percentage:.1f}% match)")
            else:
                print("❌ No suitable match found")
        
        return recommendations
    
    def _find_matching_products(self, requirement: Dict[str, Any]) -> List[SpecMatch]:
        """
        Find products that match the RFP requirement specifications
        """
        matches = []
        rfp_specs = requirement["technical_specs"]
        
        for product in self.products:
            # Calculate specification match percentage
            match_percentage = calculate_spec_match_percentage(rfp_specs, product.specifications)
            
            # Only consider products with >30% match
            if match_percentage >= 30.0:
                # Identify matched, missing, and exceeded specs
                matched_specs = {}
                missing_specs = []
                exceeded_specs = []
                
                for spec_name, required_value in rfp_specs.items():
                    if spec_name in product.specifications:
                        product_value = product.specifications[spec_name]
                        matched_specs[spec_name] = {
                            "required": required_value,
                            "product": product_value
                        }
                        
                        # Check if product spec exceeds requirement (for numeric values)
                        if isinstance(required_value, (int, float)) and isinstance(product_value, (int, float)):
                            if product_value > required_value * 1.1:  # 10% tolerance
                                exceeded_specs.append(f"{spec_name}: {product_value} > {required_value}")
                    else:
                        missing_specs.append(spec_name)
                
                spec_match = SpecMatch(
                    sku=product.sku,
                    product_name=product.product_name,
                    match_percentage=match_percentage,
                    matched_specs=matched_specs,
                    missing_specs=missing_specs,
                    exceeded_specs=exceeded_specs
                )
                matches.append(spec_match)
        
        # Sort by match percentage (highest first)
        matches.sort(key=lambda x: x.match_percentage, reverse=True)
        return matches
    
    def create_comparison_table(self, recommendations: List[ProductRecommendation]) -> Dict[str, Any]:
        """
        Create detailed comparison table for all recommendations
        """
        print_section_header("Technical Agent - Comparison Table Generation")
        
        comparison_data = {
            "rfp_requirements": [],
            "product_comparisons": []
        }
        
        for rec in recommendations:
            # RFP requirement summary
            req_summary = {
                "item_no": rec.requirement_item_no,
                "description": rec.requirement_description,
                "selected_sku": rec.selected_sku,
                "selected_match_percentage": rec.selected_match_percentage
            }
            comparison_data["rfp_requirements"].append(req_summary)
            
            # Detailed product comparison
            if rec.top_matches:
                comparison = {
                    "requirement_item": rec.requirement_item_no,
                    "products": []
                }
                
                for i, match in enumerate(rec.top_matches, 1):
                    product_info = {
                        "rank": i,
                        "sku": match.sku,
                        "product_name": match.product_name,
                        "match_percentage": match.match_percentage,
                        "specification_comparison": match.matched_specs,
                        "missing_specifications": match.missing_specs,
                        "exceeded_specifications": match.exceeded_specs
                    }
                    comparison["products"].append(product_info)
                
                comparison_data["product_comparisons"].append(comparison)
        
        return comparison_data
    
    def generate_final_recommendation_table(self, recommendations: List[ProductRecommendation]) -> Dict[str, Any]:
        """
        Generate final table with selected products for all RFP items
        """
        print_section_header("Technical Agent - Final Recommendations")
        
        final_table = {
            "summary": {
                "total_items": len(recommendations),
                "items_matched": len([r for r in recommendations if r.selected_sku]),
                "average_match_percentage": 0.0
            },
            "selected_products": []
        }
        
        total_match_percentage = 0.0
        matched_count = 0
        
        for rec in recommendations:
            if rec.selected_sku:
                # Find the selected product details
                selected_product = None
                for product in self.products:
                    if product.sku == rec.selected_sku:
                        selected_product = product
                        break
                
                product_entry = {
                    "item_no": rec.requirement_item_no,
                    "requirement_description": rec.requirement_description,
                    "selected_sku": rec.selected_sku,
                    "selected_product_name": selected_product.product_name if selected_product else "Unknown",
                    "match_percentage": rec.selected_match_percentage,
                    "unit_price": selected_product.unit_price if selected_product else 0.0,
                    "manufacturer": selected_product.manufacturer if selected_product else "Unknown",
                    "category": selected_product.category if selected_product else "Unknown"
                }
                
                final_table["selected_products"].append(product_entry)
                total_match_percentage += rec.selected_match_percentage
                matched_count += 1
                
                print(f"✅ Item {rec.requirement_item_no}: {rec.selected_sku} ({rec.selected_match_percentage:.1f}% match)")
            else:
                print(f"❌ Item {rec.requirement_item_no}: No suitable product found")
        
        # Calculate average match percentage
        if matched_count > 0:
            final_table["summary"]["average_match_percentage"] = total_match_percentage / matched_count
        
        print(f"\n📊 Summary: {matched_count}/{len(recommendations)} items matched with {final_table['summary']['average_match_percentage']:.1f}% average match")
        
        return final_table
    
    def process(self, technical_summary: Dict[str, Any]) -> TechnicalAgentResponse:
        """
        Main processing function for the Technical Agent
        """
        try:
            # Step 1: Analyze RFP requirements and find matching products
            recommendations = self.analyze_rfp_requirements(technical_summary)
            
            # Step 2: Create detailed comparison table
            comparison_table = self.create_comparison_table(recommendations)
            
            # Step 3: Generate final recommendation table
            final_table = self.generate_final_recommendation_table(recommendations)
            
            # Prepare response
            response = TechnicalAgentResponse(
                agent_name="Technical Agent",
                success=True,
                message=f"Successfully analyzed {len(recommendations)} RFP requirements",
                product_recommendations=recommendations,
                comparison_table=comparison_table,
                data={
                    "final_recommendations": final_table,
                    "total_items": len(recommendations),
                    "matched_items": len([r for r in recommendations if r.selected_sku])
                }
            )
            
            return response
            
        except Exception as e:
            return TechnicalAgentResponse(
                agent_name="Technical Agent",
                success=False,
                message=f"Error in Technical Agent processing: {str(e)}",
                product_recommendations=[],
                comparison_table={}
            )
    
    def print_detailed_analysis(self, response: TechnicalAgentResponse) -> None:
        """
        Print detailed analysis results in a formatted way
        """
        if not response.success:
            print(f"❌ {response.message}")
            return
        
        print_section_header("TECHNICAL ANALYSIS RESULTS")
        
        # Print summary
        final_data = response.data.get("final_recommendations", {})
        summary = final_data.get("summary", {})
        
        print(f"📊 Analysis Summary:")
        print(f"   • Total RFP Items: {summary.get('total_items', 0)}")
        print(f"   • Successfully Matched: {summary.get('items_matched', 0)}")
        print(f"   • Average Match Score: {summary.get('average_match_percentage', 0):.1f}%")
        
        # Print detailed recommendations
        print_subsection_header("Selected Products")
        selected_products = final_data.get("selected_products", [])
        
        for product in selected_products:
            print(f"📦 Item {product['item_no']}: {product['requirement_description']}")
            print(f"   ✅ Selected: {product['selected_sku']} - {product['selected_product_name']}")
            print(f"   🎯 Match Score: {product['match_percentage']:.1f}%")
            print(f"   💰 Unit Price: ₹{product['unit_price']:.2f}")
            print(f"   🏭 Manufacturer: {product['manufacturer']}")
            print()
