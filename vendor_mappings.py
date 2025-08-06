import json
import os
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to the mappings file
MAPPINGS_FILE = 'data/vendor_mappings.json'

def load_mappings() -> Dict[str, str]:
    """Load existing vendor mappings from file."""
    if not os.path.exists(MAPPINGS_FILE):
        return {}
    
    try:
        with open(MAPPINGS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading mappings: {e}")
        return {}

def save_mappings(mappings: Dict[str, str]):
    """Save vendor mappings to file."""
    os.makedirs(os.path.dirname(MAPPINGS_FILE), exist_ok=True)
    with open(MAPPINGS_FILE, 'w') as f:
        json.dump(mappings, f, indent=2)

def get_display_name(vendor_name: str) -> Optional[str]:
    """Get the display name for a vendor, or None if not mapped."""
    mappings = load_mappings()
    return mappings.get(vendor_name)

def add_mapping(vendor_name: str, display_name: str):
    """Add a new vendor mapping."""
    mappings = load_mappings()
    mappings[vendor_name] = display_name
    save_mappings(mappings)
    logger.info(f"Added mapping: {vendor_name} → {display_name}")

def update_mapping(vendor_name: str, display_name: str):
    """Update an existing vendor mapping."""
    mappings = load_mappings()
    if vendor_name in mappings:
        old_name = mappings[vendor_name]
        mappings[vendor_name] = display_name
        save_mappings(mappings)
        logger.info(f"Updated mapping: {vendor_name} → {display_name} (was {old_name})")
    else:
        logger.warning(f"Cannot update non-existent mapping for {vendor_name}")

def list_mappings():
    """List all current vendor mappings."""
    mappings = load_mappings()
    for vendor, display in sorted(mappings.items()):
        print(f"{vendor} → {display}")

if __name__ == '__main__':
    # Example usage
    list_mappings() 