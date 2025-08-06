"""
Search for BestSelf-related vendors in the existing transaction data.
"""

from supabase_client import supabase
import re

def search_bestself_vendors():
    """Search for vendors that might be related to BestSelf."""
    try:
        print("🔍 Searching for BestSelf-related vendors...")
        print("=" * 60)
        
        # Get all transactions
        result = supabase.table('transactions') \
            .select('vendor_name, description, amount, transaction_date') \
            .eq('client_id', 'spyguy') \
            .execute()
        
        if not result.data:
            print("❌ No transactions found")
            return
        
        transactions = result.data
        print(f"📊 Searching through {len(transactions)} transactions...")
        
        # Search terms related to BestSelf
        search_terms = [
            'bestself',
            'best self',
            'best-self',
            'beast',  # Could be abbreviated
            'self',
            'journal',
            'planner',
            'productivity',
            'habit',
            'wellness'
        ]
        
        matches = []
        
        for txn in transactions:
            vendor_name = (txn.get('vendor_name') or '').lower()
            description = (txn.get('description') or '').lower()
            
            # Check if any search term matches
            for term in search_terms:
                if term in vendor_name or term in description:
                    matches.append({
                        'transaction_date': txn['transaction_date'],
                        'vendor_name': txn['vendor_name'],
                        'description': txn['description'],
                        'amount': txn['amount'],
                        'matched_term': term
                    })
                    break
        
        if matches:
            print(f"🎯 Found {len(matches)} potential BestSelf-related transactions:")
            print()
            
            # Group by vendor
            vendor_groups = {}
            for match in matches:
                vendor = match['vendor_name']
                if vendor not in vendor_groups:
                    vendor_groups[vendor] = []
                vendor_groups[vendor].append(match)
            
            for vendor, vendor_matches in vendor_groups.items():
                print(f"📁 {vendor} ({len(vendor_matches)} transactions):")
                
                # Show a few examples
                for i, match in enumerate(sorted(vendor_matches, key=lambda x: x['transaction_date'], reverse=True)[:5]):
                    print(f"  {match['transaction_date']} | ${match['amount']:>10,.2f} | {match['matched_term']}")
                    if match['description'] and match['description'] != match['vendor_name']:
                        print(f"    Description: {match['description'][:60]}")
                
                if len(vendor_matches) > 5:
                    print(f"    ... and {len(vendor_matches) - 5} more")
                print()
        else:
            print("❌ No BestSelf-related vendors found in existing transactions")
            
            # Show some sample vendor names to help identify the pattern
            print("\n📝 Sample vendor names from recent transactions:")
            recent_vendors = set()
            for txn in sorted(transactions, key=lambda x: x['transaction_date'], reverse=True)[:50]:
                if txn['vendor_name']:
                    recent_vendors.add(txn['vendor_name'])
            
            for vendor in sorted(list(recent_vendors))[:20]:
                print(f"  • {vendor}")
            
            if len(recent_vendors) > 20:
                print(f"  ... and {len(recent_vendors) - 20} more unique vendors")
        
        return matches
        
    except Exception as e:
        print(f"❌ Error searching vendors: {e}")
        return None

if __name__ == "__main__":
    search_bestself_vendors()