from typing import Dict, List, Any
import json
from datetime import datetime, timedelta
import random

def calculate_spec_match_percentage(rfp_specs: Dict[str, Any], product_specs: Dict[str, Any]) -> float:
    """
    Calculate the percentage match between RFP specifications and product specifications.
    All specs have equal weightage.
    """
    if not rfp_specs:
        return 0.0
    
    total_specs = len(rfp_specs)
    matched_specs = 0
    
    for spec_name, required_value in rfp_specs.items():
        if spec_name in product_specs:
            product_value = product_specs[spec_name]
            
            # Handle different types of specifications
            if isinstance(required_value, (int, float)) and isinstance(product_value, (int, float)):
                # For numeric values, consider a match if within 5% tolerance
                tolerance = abs(required_value * 0.05)
                if abs(product_value - required_value) <= tolerance:
                    matched_specs += 1
            elif isinstance(required_value, str) and isinstance(product_value, str):
                # For string values, exact match or contains
                if required_value.lower() in product_value.lower() or product_value.lower() in required_value.lower():
                    matched_specs += 1
            elif str(required_value).lower() == str(product_value).lower():
                matched_specs += 1
    
    return (matched_specs / total_specs) * 100

def format_currency(amount: float) -> str:
    """Format amount as Indian Rupees"""
    return f"₹{amount:,.2f}"

def days_until_deadline(deadline_date) -> int:
    """Calculate days until deadline"""
    if isinstance(deadline_date, str):
        deadline_date = datetime.strptime(deadline_date, "%Y-%m-%d").date()
    return (deadline_date - datetime.now().date()).days

def load_json_data(file_path: str) -> Dict[str, Any]:
    """Load JSON data from file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_json_data(data: Dict[str, Any], file_path: str) -> None:
    """Save data to JSON file"""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def generate_rfp_id() -> str:
    """Generate unique RFP ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = random.randint(1000, 9999)
    return f"RFP-{timestamp}-{random_suffix}"

def print_section_header(title: str) -> None:
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f" {title.upper()}")
    print("="*80)

def print_subsection_header(title: str) -> None:
    """Print formatted subsection header"""
    print(f"\n--- {title} ---")

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."