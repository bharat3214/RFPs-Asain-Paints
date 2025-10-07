from typing import List, Dict, Any, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field
from enum import Enum

class RFPStatus(str, Enum):
    IDENTIFIED = "identified"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SUBMITTED = "submitted"

class ProductCategory(str, Enum):
    WIRES = "wires"
    CABLES = "cables"
    ELECTRICAL_GOODS = "electrical_goods"

class RFPRequirement(BaseModel):
    """Individual product requirement within an RFP"""
    item_no: str
    description: str
    quantity: int
    unit: str
    technical_specs: Dict[str, Any]
    
class RFP(BaseModel):
    """Main RFP data model"""
    rfp_id: str
    title: str
    organization: str
    submission_deadline: date
    project_value: Optional[float] = None
    requirements: List[RFPRequirement]
    testing_requirements: List[str]
    acceptance_criteria: List[str]
    status: RFPStatus = RFPStatus.IDENTIFIED
    source_url: Optional[str] = None
    
class ProductSpecification(BaseModel):
    """Product specification data model"""
    sku: str
    product_name: str
    category: ProductCategory
    manufacturer: str
    specifications: Dict[str, Any]  # Technical specifications
    unit_price: Optional[float] = None
    availability: bool = True
    
class SpecMatch(BaseModel):
    """Specification matching result"""
    sku: str
    product_name: str
    match_percentage: float
    matched_specs: Dict[str, Any]
    missing_specs: List[str]
    exceeded_specs: List[str]
    
class ProductRecommendation(BaseModel):
    """Product recommendation for RFP requirement"""
    requirement_item_no: str
    requirement_description: str
    top_matches: List[SpecMatch]
    selected_sku: str
    selected_match_percentage: float
    
class PricingBreakdown(BaseModel):
    """Pricing breakdown for a product"""
    sku: str
    quantity: int
    unit_price: float
    total_material_cost: float
    testing_costs: Dict[str, float]  # test_name: cost
    total_testing_cost: float
    total_cost: float
    
class AgentResponse(BaseModel):
    """Base response model for agent communications"""
    agent_name: str
    timestamp: datetime = Field(default_factory=datetime.now)
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    
class SalesAgentResponse(AgentResponse):
    """Sales agent specific response"""
    identified_rfps: List[RFP]
    selected_rfp: Optional[RFP] = None
    
class TechnicalAgentResponse(AgentResponse):
    """Technical agent specific response"""
    product_recommendations: List[ProductRecommendation]
    comparison_table: Dict[str, Any]
    
class PricingAgentResponse(AgentResponse):
    """Pricing agent specific response"""
    pricing_breakdown: List[PricingBreakdown]
    total_material_cost: float
    total_testing_cost: float
    grand_total: float
    
class MasterAgentResponse(AgentResponse):
    """Master agent consolidated response"""
    rfp_summary: Optional[RFP] = None
    technical_analysis: Optional[TechnicalAgentResponse] = None
    pricing_analysis: Optional[PricingAgentResponse] = None
    final_recommendation: Dict[str, Any]