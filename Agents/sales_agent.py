import json
import requests
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import sys
import os

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import RFP, RFPRequirement, RFPStatus, SalesAgentResponse
from utils import load_json_data, days_until_deadline, print_section_header, print_subsection_header

class SalesAgent:
    """
    Sales Agent responsible for:
    1. Scanning predefined URLs for RFPs
    2. Identifying RFPs due within next 3 months
    3. Summarizing RFP requirements
    4. Selecting one RFP for processing
    """
    
    def __init__(self, data_path: str = "data/"):
        self.data_path = data_path
        self.rfp_urls = [
            "https://dmrc.gov.in/tenders",
            "https://punesmartcity.gov.in/tenders", 
            "https://bhel.gov.in/tenders",
            "https://ntpc.gov.in/tenders"
        ]
    
    def scan_rfps(self) -> List[RFP]:
        """
        Scan URLs for RFPs. In production, this would parse actual websites.
        For demo purposes, we'll use our synthetic data and simulate URL scanning.
        """
        print_section_header("Sales Agent - Scanning for RFPs")
        
        # Load sample RFPs (simulating web scraping)
        rfp_data = load_json_data(os.path.join(self.data_path, "rfps.json"))
        identified_rfps = []
        
        if "sample_rfps" in rfp_data:
            for rfp_dict in rfp_data["sample_rfps"]:
                # Convert dictionary to RFP object
                requirements = []
                for req in rfp_dict["requirements"]:
                    requirements.append(RFPRequirement(**req))
                
                # Parse date string to date object
                submission_date = datetime.strptime(rfp_dict["submission_deadline"], "%Y-%m-%d").date()
                
                rfp = RFP(
                    rfp_id=rfp_dict["rfp_id"],
                    title=rfp_dict["title"],
                    organization=rfp_dict["organization"],
                    submission_deadline=submission_date,
                    project_value=rfp_dict.get("project_value"),
                    requirements=requirements,
                    testing_requirements=rfp_dict["testing_requirements"],
                    acceptance_criteria=rfp_dict["acceptance_criteria"],
                    status=RFPStatus.IDENTIFIED,
                    source_url=rfp_dict.get("source_url")
                )
                identified_rfps.append(rfp)
        
        print(f"📋 Found {len(identified_rfps)} RFPs from scanning URLs")
        return identified_rfps
    
    def filter_rfps_by_deadline(self, rfps: List[RFP], max_days: int = 90) -> List[RFP]:
        """
        Filter RFPs that are due within the specified number of days (default: 3 months)
        """
        print_subsection_header(f"Filtering RFPs due within {max_days} days")
        
        filtered_rfps = []
        for rfp in rfps:
            days_remaining = days_until_deadline(rfp.submission_deadline)
            
            if 0 <= days_remaining <= max_days:
                filtered_rfps.append(rfp)
                print(f"✅ {rfp.rfp_id}: {rfp.title[:50]}... - Due in {days_remaining} days")
            else:
                print(f"❌ {rfp.rfp_id}: {rfp.title[:50]}... - Due in {days_remaining} days (excluded)")
        
        print(f"\n📊 {len(filtered_rfps)} out of {len(rfps)} RFPs are due within {max_days} days")
        return filtered_rfps
    
    def summarize_rfp_requirements(self, rfp: RFP) -> Dict[str, Any]:
        """
        Create a summary of RFP requirements for technical and pricing agents
        """
        technical_summary = {
            "rfp_id": rfp.rfp_id,
            "title": rfp.title,
            "organization": rfp.organization,
            "submission_deadline": rfp.submission_deadline.isoformat(),
            "products_required": []
        }
        
        # Summarize product requirements for technical agent
        for req in rfp.requirements:
            product_summary = {
                "item_no": req.item_no,
                "description": req.description,
                "quantity": req.quantity,
                "unit": req.unit,
                "technical_specs": req.technical_specs
            }
            technical_summary["products_required"].append(product_summary)
        
        # Summarize testing requirements for pricing agent
        pricing_summary = {
            "rfp_id": rfp.rfp_id,
            "testing_requirements": rfp.testing_requirements,
            "acceptance_criteria": rfp.acceptance_criteria,
            "project_value": rfp.project_value,
            "delivery_requirements": self._extract_delivery_requirements(rfp.acceptance_criteria)
        }
        
        return {
            "technical_summary": technical_summary,
            "pricing_summary": pricing_summary
        }
    
    def _extract_delivery_requirements(self, acceptance_criteria: List[str]) -> Dict[str, Any]:
        """
        Extract delivery-related requirements from acceptance criteria
        """
        delivery_info = {
            "delivery_days": 45,  # default
            "certifications_required": [],
            "special_requirements": []
        }
        
        for criteria in acceptance_criteria:
            if "days" in criteria.lower():
                # Extract delivery days
                words = criteria.split()
                for i, word in enumerate(words):
                    if word.isdigit() and i+1 < len(words) and "day" in words[i+1].lower():
                        delivery_info["delivery_days"] = int(word)
                        break
            
            if "certification" in criteria.lower() or "mark" in criteria.lower():
                delivery_info["certifications_required"].append(criteria)
            else:
                delivery_info["special_requirements"].append(criteria)
        
        return delivery_info
    
    def select_rfp_for_processing(self, rfps: List[RFP]) -> Optional[RFP]:
        """
        Select one RFP for processing based on business logic:
        1. Highest project value
        2. Most time available (days until deadline)
        3. Organization preference (government > PSU > private)
        """
        if not rfps:
            return None
        
        print_subsection_header("Selecting RFP for Processing")
        
        # Score each RFP
        scored_rfps = []
        for rfp in rfps:
            score = self._calculate_rfp_score(rfp)
            scored_rfps.append((rfp, score))
            print(f"🎯 {rfp.rfp_id}: Score = {score:.2f}")
        
        # Sort by score (highest first)
        scored_rfps.sort(key=lambda x: x[1], reverse=True)
        selected_rfp = scored_rfps[0][0]
        
        print(f"\n🏆 Selected RFP: {selected_rfp.rfp_id} - {selected_rfp.title}")
        return selected_rfp
    
    def _calculate_rfp_score(self, rfp: RFP) -> float:
        """
        Calculate a score for RFP selection
        """
        score = 0.0
        
        # Project value score (normalized to 0-40 points)
        if rfp.project_value:
            value_score = min(rfp.project_value / 1000000, 40)  # ₹1M = 1 point, max 40
            score += value_score
        
        # Time availability score (0-30 points)
        days_remaining = days_until_deadline(rfp.submission_deadline)
        time_score = min(days_remaining / 3, 30)  # 3 days = 1 point, max 30
        score += time_score
        
        # Organization type score (0-20 points)
        org_lower = rfp.organization.lower()
        if any(keyword in org_lower for keyword in ["government", "metro", "railway", "corporation"]):
            score += 20
        elif any(keyword in org_lower for keyword in ["limited", "ltd", "bhel", "ntpc"]):
            score += 15
        else:
            score += 10
        
        # Product complexity score (0-10 points)
        complex_keywords = ["xlpe", "33kv", "11kv", "armoured"]
        complexity_score = 0
        for req in rfp.requirements:
            desc_lower = req.description.lower()
            if any(keyword in desc_lower for keyword in complex_keywords):
                complexity_score += 2
        score += min(complexity_score, 10)
        
        return score
    
    def process(self) -> SalesAgentResponse:
        """
        Main processing function for the Sales Agent
        """
        try:
            # Step 1: Scan URLs for RFPs
            all_rfps = self.scan_rfps()
            
            # Step 2: Filter RFPs due within 3 months
            filtered_rfps = self.filter_rfps_by_deadline(all_rfps, max_days=90)
            
            # Step 3: Select one RFP for processing
            selected_rfp = self.select_rfp_for_processing(filtered_rfps)
            
            if selected_rfp:
                # Step 4: Create summaries for other agents
                summaries = self.summarize_rfp_requirements(selected_rfp)
                
                response = SalesAgentResponse(
                    agent_name="Sales Agent",
                    success=True,
                    message=f"Successfully identified and selected RFP: {selected_rfp.rfp_id}",
                    identified_rfps=filtered_rfps,
                    selected_rfp=selected_rfp,
                    data={
                        "technical_summary": summaries["technical_summary"],
                        "pricing_summary": summaries["pricing_summary"]
                    }
                )
            else:
                response = SalesAgentResponse(
                    agent_name="Sales Agent",
                    success=False,
                    message="No suitable RFPs found within the deadline criteria",
                    identified_rfps=filtered_rfps,
                    selected_rfp=None
                )
            
            return response
            
        except Exception as e:
            return SalesAgentResponse(
                agent_name="Sales Agent", 
                success=False,
                message=f"Error in Sales Agent processing: {str(e)}",
                identified_rfps=[],
                selected_rfp=None
            )
