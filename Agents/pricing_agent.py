import json
import sys
import os
from typing import List, Dict, Any, Optional, Tuple

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import PricingBreakdown, PricingAgentResponse, ProductRecommendation
from utils import (
    load_json_data, format_currency, 
    print_section_header, print_subsection_header
)

class PricingAgent:
    """
    Pricing Agent responsible for:
    1. Receiving test/acceptance requirements from Master Agent
    2. Receiving product recommendations from Technical Agent
    3. Calculating material costs based on quantity and unit prices
    4. Calculating testing and service costs
    5. Providing consolidated pricing breakdown
    """
    
    def __init__(self, data_path: str = "data/"):
        self.data_path = data_path
        self.pricing_data = self._load_pricing_data()
        self.test_requirements = self._load_test_requirements()
    
    def _load_pricing_data(self) -> Dict[str, Any]:
        """Load pricing data from JSON file"""
        return load_json_data(os.path.join(self.data_path, "pricing.json"))
    
    def _load_test_requirements(self) -> Dict[str, Any]:
        """Load test requirements mapping from JSON file"""
        return load_json_data(os.path.join(self.data_path, "test_requirements.json"))
    
    def calculate_material_costs(self, 
                               technical_recommendations: List[ProductRecommendation],
                               rfp_requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate material costs for all selected products
        """
        print_section_header("Pricing Agent - Material Cost Calculation")
        
        material_costs = []
        base_prices = self.pricing_data.get("material_pricing", {}).get("base_prices", {})
        quantity_discounts = self.pricing_data.get("material_pricing", {}).get("quantity_discounts", {})
        
        # Create a mapping of item_no to quantity from RFP requirements
        quantity_map = {}
        for req in rfp_requirements:
            quantity_map[req["item_no"]] = req["quantity"]
        
        for recommendation in technical_recommendations:
            if recommendation.selected_sku:
                item_no = recommendation.requirement_item_no
                quantity = quantity_map.get(item_no, 0)
                base_price = base_prices.get(recommendation.selected_sku, 0.0)
                
                # Calculate discount based on quantity
                discount_rate = self._get_quantity_discount(quantity, quantity_discounts)
                unit_price_after_discount = base_price * (1 - discount_rate)
                total_material_cost = unit_price_after_discount * quantity
                
                material_cost = {
                    "item_no": item_no,
                    "sku": recommendation.selected_sku,
                    "quantity": quantity,
                    "base_unit_price": base_price,
                    "discount_rate": discount_rate,
                    "unit_price_after_discount": unit_price_after_discount,
                    "total_material_cost": total_material_cost
                }
                
                material_costs.append(material_cost)
                
                print(f"💰 Item {item_no} ({recommendation.selected_sku}):")
                print(f"   • Quantity: {quantity:,} units")
                print(f"   • Base Price: {format_currency(base_price)} per unit")
                print(f"   • Discount: {discount_rate:.1%}")
                print(f"   • Final Price: {format_currency(unit_price_after_discount)} per unit")
                print(f"   • Total Cost: {format_currency(total_material_cost)}")
        
        return material_costs
    
    def _get_quantity_discount(self, quantity: int, discount_tiers: Dict[str, float]) -> float:
        """
        Calculate discount rate based on quantity
        """
        for tier, rate in discount_tiers.items():
            if tier.endswith("+"):
                min_qty = int(tier[:-1])
                if quantity >= min_qty:
                    return rate
            elif "-" in tier:
                min_qty, max_qty = map(int, tier.split("-"))
                if min_qty <= quantity <= max_qty:
                    return rate
        return 0.0
    
    def calculate_testing_costs(self, 
                              testing_requirements: List[str],
                              material_costs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate testing costs based on RFP testing requirements
        """
        print_section_header("Pricing Agent - Testing Cost Calculation")
        
        testing_costs = []
        routine_tests = self.pricing_data.get("testing_services", {}).get("routine_tests", {})
        type_tests = self.pricing_data.get("testing_services", {}).get("type_tests", {})
        specialized_tests = self.pricing_data.get("testing_services", {}).get("specialized_tests", {})
        
        all_test_services = {**routine_tests, **type_tests, **specialized_tests}
        
        for material in material_costs:
            item_testing_costs = {}
            total_testing_cost = 0.0
            
            print(f"🧪 Testing costs for Item {material['item_no']} ({material['sku']}):")
            
            for test_requirement in testing_requirements:
                if test_requirement in all_test_services:
                    test_info = all_test_services[test_requirement]
                    cost_per_sample = test_info["cost_per_sample"]
                    
                    # Calculate number of samples needed
                    if "samples_per_1000m" in test_info:
                        # For routine tests
                        samples_needed = max(1, int(material["quantity"] / 1000 * test_info["samples_per_1000m"]))
                    elif "samples_required" in test_info:
                        # For type tests
                        samples_needed = test_info["samples_required"]
                    else:
                        samples_needed = 1
                    
                    test_cost = cost_per_sample * samples_needed
                    item_testing_costs[test_requirement] = {
                        "cost_per_sample": cost_per_sample,
                        "samples_needed": samples_needed,
                        "total_cost": test_cost
                    }
                    total_testing_cost += test_cost
                    
                    print(f"   • {test_requirement}:")
                    print(f"     - Samples needed: {samples_needed}")
                    print(f"     - Cost per sample: {format_currency(cost_per_sample)}")
                    print(f"     - Total cost: {format_currency(test_cost)}")
            
            testing_cost_entry = {
                "item_no": material["item_no"],
                "sku": material["sku"],
                "test_breakdown": item_testing_costs,
                "total_testing_cost": total_testing_cost
            }
            
            testing_costs.append(testing_cost_entry)
            print(f"   📊 Total testing cost: {format_currency(total_testing_cost)}")
        
        return testing_costs
    
    def calculate_additional_costs(self, 
                                 pricing_summary: Dict[str, Any],
                                 total_material_cost: float) -> Dict[str, Any]:
        """
        Calculate additional costs like certification, logistics, etc.
        """
        print_section_header("Pricing Agent - Additional Costs")
        
        additional_costs = {}
        
        # Certification costs
        certifications = pricing_summary.get("delivery_requirements", {}).get("certifications_required", [])
        cert_costs = self.test_requirements.get("certification_requirements", {})
        
        certification_cost = 0.0
        for cert_req in certifications:
            for cert_type, cert_info in cert_costs.items():
                if cert_type.replace("_", " ") in cert_req.lower():
                    certification_cost += cert_info["cost"]
        
        additional_costs["certification"] = certification_cost
        
        # Delivery costs based on delivery requirements
        delivery_days = pricing_summary.get("delivery_requirements", {}).get("delivery_days", 45)
        delivery_reqs = self.test_requirements.get("delivery_requirements", {})
        
        delivery_multiplier = 1.0
        if delivery_days <= 20:
            delivery_multiplier = delivery_reqs.get("express_delivery", {}).get("cost_multiplier", 1.25)
        elif delivery_days <= 30:
            delivery_multiplier = delivery_reqs.get("expedited_delivery", {}).get("cost_multiplier", 1.15)
        
        logistics_costs = self.pricing_data.get("logistics_costs", {})
        base_logistics = logistics_costs.get("transportation_base", 2500.0)
        delivery_cost = base_logistics * delivery_multiplier
        
        additional_costs["delivery"] = delivery_cost
        
        # Margin calculation
        margin_settings = self.pricing_data.get("margin_settings", {})
        margin_rate = margin_settings.get("government_tender_margin", 0.10)  # 10% for govt tenders
        margin_amount = total_material_cost * margin_rate
        
        additional_costs["margin"] = margin_amount
        additional_costs["margin_rate"] = margin_rate
        
        print(f"📋 Certification costs: {format_currency(certification_cost)}")
        print(f"🚚 Delivery costs: {format_currency(delivery_cost)} (delivery in {delivery_days} days)")
        print(f"💼 Business margin ({margin_rate:.1%}): {format_currency(margin_amount)}")
        
        return additional_costs
    
    def create_pricing_breakdown(self, 
                               material_costs: List[Dict[str, Any]],
                               testing_costs: List[Dict[str, Any]],
                               additional_costs: Dict[str, Any]) -> List[PricingBreakdown]:
        """
        Create detailed pricing breakdown for each item
        """
        pricing_breakdowns = []
        
        for material in material_costs:
            item_no = material["item_no"]
            
            # Find corresponding testing cost
            testing_cost_data = next(
                (test for test in testing_costs if test["item_no"] == item_no), 
                {"total_testing_cost": 0.0, "test_breakdown": {}}
            )
            
            # Create testing costs dict for this item
            item_testing_costs = {}
            for test_name, test_info in testing_cost_data["test_breakdown"].items():
                item_testing_costs[test_name] = test_info["total_cost"]
            
            # Calculate proportional additional costs based on material cost
            total_material_cost_all_items = sum(m["total_material_cost"] for m in material_costs)
            proportion = material["total_material_cost"] / total_material_cost_all_items if total_material_cost_all_items > 0 else 0
            
            proportional_cert_cost = additional_costs["certification"] * proportion
            proportional_delivery_cost = additional_costs["delivery"] * proportion
            proportional_margin = additional_costs["margin"] * proportion
            
            total_additional = proportional_cert_cost + proportional_delivery_cost + proportional_margin
            total_cost = material["total_material_cost"] + testing_cost_data["total_testing_cost"] + total_additional
            
            breakdown = PricingBreakdown(
                sku=material["sku"],
                quantity=material["quantity"],
                unit_price=material["unit_price_after_discount"],
                total_material_cost=material["total_material_cost"],
                testing_costs=item_testing_costs,
                total_testing_cost=testing_cost_data["total_testing_cost"],
                total_cost=total_cost
            )
            
            pricing_breakdowns.append(breakdown)
        
        return pricing_breakdowns
    
    def process(self, 
              pricing_summary: Dict[str, Any],
              technical_recommendations: List[ProductRecommendation]) -> PricingAgentResponse:
        """
        Main processing function for the Pricing Agent
        """
        try:
            # Extract RFP requirements from technical recommendations context
            # In a real implementation, this would come from the pricing summary
            rfp_requirements = pricing_summary.get("products_required", [])
            
            # Step 1: Calculate material costs
            material_costs = self.calculate_material_costs(technical_recommendations, rfp_requirements)
            
            # Step 2: Calculate testing costs
            testing_costs = self.calculate_testing_costs(
                pricing_summary["testing_requirements"], 
                material_costs
            )
            
            # Step 3: Calculate additional costs
            total_material_cost = sum(m["total_material_cost"] for m in material_costs)
            additional_costs = self.calculate_additional_costs(pricing_summary, total_material_cost)
            
            # Step 4: Create detailed pricing breakdown
            pricing_breakdown = self.create_pricing_breakdown(
                material_costs, testing_costs, additional_costs
            )
            
            # Step 5: Calculate totals
            total_testing_cost = sum(p.total_testing_cost for p in pricing_breakdown)
            grand_total = sum(p.total_cost for p in pricing_breakdown)
            
            response = PricingAgentResponse(
                agent_name="Pricing Agent",
                success=True,
                message=f"Successfully calculated pricing for {len(pricing_breakdown)} items",
                pricing_breakdown=pricing_breakdown,
                total_material_cost=total_material_cost,
                total_testing_cost=total_testing_cost,
                grand_total=grand_total,
                data={
                    "material_costs": material_costs,
                    "testing_costs": testing_costs,
                    "additional_costs": additional_costs
                }
            )
            
            return response
            
        except Exception as e:
            return PricingAgentResponse(
                agent_name="Pricing Agent",
                success=False,
                message=f"Error in Pricing Agent processing: {str(e)}",
                pricing_breakdown=[],
                total_material_cost=0.0,
                total_testing_cost=0.0,
                grand_total=0.0
            )
    
    def print_pricing_summary(self, response: PricingAgentResponse) -> None:
        """
        Print comprehensive pricing summary
        """
        if not response.success:
            print(f"❌ {response.message}")
            return
        
        print_section_header("PRICING ANALYSIS RESULTS")
        
        # Overall summary
        print("💰 Cost Summary:")
        print(f"   • Total Material Cost: {format_currency(response.total_material_cost)}")
        print(f"   • Total Testing Cost: {format_currency(response.total_testing_cost)}")
        print(f"   • Grand Total: {format_currency(response.grand_total)}")
        
        # Detailed breakdown by item
        print_subsection_header("Detailed Pricing Breakdown")
        
        for breakdown in response.pricing_breakdown:
            print(f"📦 SKU: {breakdown.sku}")
            print(f"   • Quantity: {breakdown.quantity:,} units")
            print(f"   • Unit Price: {format_currency(breakdown.unit_price)}")
            print(f"   • Material Cost: {format_currency(breakdown.total_material_cost)}")
            print(f"   • Testing Cost: {format_currency(breakdown.total_testing_cost)}")
            print(f"   • Total Cost: {format_currency(breakdown.total_cost)}")
            
            if breakdown.testing_costs:
                print("   🧪 Testing Breakdown:")
                for test_name, cost in breakdown.testing_costs.items():
                    print(f"      - {test_name}: {format_currency(cost)}")
            print()
