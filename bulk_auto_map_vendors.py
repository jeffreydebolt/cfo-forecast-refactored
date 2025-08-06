"""
Bulk Auto-Map Vendors
Processes all existing vendors for auto-mapping based on pattern rules.

Usage:
    python3 bulk_auto_map_vendors.py --client bestself
    python3 bulk_auto_map_vendors.py --client bestself --preview  # Show what would be mapped
"""

import argparse
import logging
from core.vendor_auto_mapping import auto_mapper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def preview_mappings(client_id: str):
    """Show what would be auto-mapped without making changes"""
    from supabase_client import supabase
    
    logger.info(f"🔍 PREVIEW: Auto-mapping analysis for {client_id}")
    
    # Get all unique vendor names from transactions
    result = supabase.table('transactions').select('vendor_name').eq('client_id', client_id).execute()
    unique_vendors = list(set(txn['vendor_name'] for txn in result.data))
    
    print(f"\n📊 ANALYSIS RESULTS:")
    print(f"Total unique vendors: {len(unique_vendors)}")
    print("=" * 80)
    
    auto_mappable = []
    needs_review = []
    
    for vendor_name in sorted(unique_vendors):
        rule = auto_mapper.find_matching_rule(vendor_name)
        
        if rule:
            auto_mappable.append((vendor_name, rule.display_name, rule.description))
        else:
            needs_review.append(vendor_name)
    
    print(f"\n✅ AUTO-MAPPABLE ({len(auto_mappable)} vendors):")
    current_group = None
    for vendor, display_name, description in auto_mappable:
        if display_name != current_group:
            print(f"\n📁 {display_name}:")
            current_group = display_name
        print(f"  • {vendor}")
    
    print(f"\n⚠️  NEEDS MANUAL REVIEW ({len(needs_review)} vendors):")
    for vendor in needs_review[:20]:  # Show first 20
        print(f"  • {vendor}")
    
    if len(needs_review) > 20:
        print(f"  ... and {len(needs_review) - 20} more")
    
    print(f"\n📈 IMPACT SUMMARY:")
    print(f"  • {len(auto_mappable)} vendors ({len(auto_mappable)/len(unique_vendors)*100:.1f}%) will be auto-mapped")
    print(f"  • {len(needs_review)} vendors ({len(needs_review)/len(unique_vendors)*100:.1f}%) need manual review")
    
    return len(auto_mappable), len(needs_review)

def main():
    parser = argparse.ArgumentParser(description='Bulk auto-map vendors using pattern rules')
    parser.add_argument('--client', required=True, help='Client ID to process')
    parser.add_argument('--preview', action='store_true', help='Preview mappings without applying')
    
    args = parser.parse_args()
    
    logger.info(f"Starting bulk vendor mapping for client: {args.client}")
    
    if args.preview:
        auto_mappable, needs_review = preview_mappings(args.client)
        print(f"\n🤔 Ready to auto-map {auto_mappable} vendors?")
        print(f"Run without --preview flag to apply these mappings.")
        
    else:
        print(f"🚀 Processing auto-mappings for {args.client}...")
        
        # Run bulk processing
        stats = auto_mapper.bulk_process_vendors(args.client)
        
        print(f"\n✅ BULK MAPPING COMPLETE!")
        print(f"📊 Results:")
        print(f"  • Processed: {stats['processed']} vendors")
        print(f"  • Auto-mapped: {stats['auto_mapped']} vendors")
        print(f"  • Needs review: {stats['needs_review']} vendors") 
        print(f"  • Errors: {stats['errors']} vendors")
        
        if stats['needs_review'] > 0:
            print(f"\n⚠️  {stats['needs_review']} vendors need manual review.")
            print(f"Check unmapped vendors with: python3 review_unmapped_vendors.py --client {args.client}")
        
        if stats['auto_mapped'] > 0:
            print(f"\n🎯 Ready to test forecast accuracy!")
            print(f"Run: python3 run_calendar_forecast.py --client {args.client} --detect-patterns")

if __name__ == "__main__":
    main()