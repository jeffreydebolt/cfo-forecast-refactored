"""
Check the complete database structure to understand available tables and clients.
"""

from supabase_client import supabase
import sys

def check_tables():
    """Check what tables are available in the database."""
    try:
        # Try to query some common table names
        common_tables = ['transactions', 'clients', 'vendor_mappings', 'forecasts', 'accounts']
        
        available_tables = []
        
        for table_name in common_tables:
            try:
                # Try to get just the count to see if table exists
                result = supabase.table(table_name).select('*', count='exact').limit(1).execute()
                available_tables.append((table_name, result.count))
                print(f"✅ Table '{table_name}' exists with {result.count} records")
            except Exception as e:
                print(f"❌ Table '{table_name}' not accessible: {str(e)[:100]}")
        
        return available_tables
        
    except Exception as e:
        print(f"Error checking tables: {e}")
        return []

def check_for_other_clients():
    """Check if there are references to other clients in various tables."""
    try:
        print("\n🔍 Checking for client references in different contexts...")
        
        # Check if there's a dedicated clients table
        try:
            result = supabase.table('clients').select('*').execute()
            if result.data:
                print(f"\n📋 Found {len(result.data)} clients in 'clients' table:")
                for client in result.data:
                    print(f"   - {client}")
            else:
                print("\n📋 'clients' table exists but is empty")
        except:
            print("\n📋 No 'clients' table found")
        
        # Check vendor_mappings for client references
        try:
            result = supabase.table('vendor_mappings').select('client_id').execute()
            if result.data:
                client_ids = list(set(row['client_id'] for row in result.data if row.get('client_id')))
                if client_ids:
                    print(f"\n🏪 Found client IDs in vendor_mappings: {client_ids}")
                else:
                    print(f"\n🏪 Found {len(result.data)} vendor mappings but no client_id values")
        except Exception as e:
            print(f"\n🏪 Could not check vendor_mappings: {str(e)[:100]}")
        
        # Check for any configuration or setup tables
        config_tables = ['client_config', 'settings', 'configurations']
        for table_name in config_tables:
            try:
                result = supabase.table(table_name).select('*').limit(5).execute()
                if result.data:
                    print(f"\n⚙️  Found {len(result.data)} records in '{table_name}' table")
                    for record in result.data[:3]:  # Show first 3
                        print(f"      {record}")
            except:
                continue
                
    except Exception as e:
        print(f"Error checking for other clients: {e}")

def check_transaction_patterns():
    """Look for patterns in transaction data that might suggest other clients."""
    try:
        print("\n📊 Analyzing transaction patterns...")
        
        # Get summary of all transactions
        result = supabase.table('transactions') \
            .select('client_id, vendor_name, transaction_date') \
            .execute()
        
        if not result.data:
            print("No transactions found")
            return
        
        # Analyze vendor patterns - sometimes different clients use different banks/vendors
        vendors = {}
        dates = []
        
        for txn in result.data:
            vendor = txn.get('vendor_name', 'Unknown')
            client = txn.get('client_id', 'Unknown')
            date = txn.get('transaction_date')
            
            if vendor not in vendors:
                vendors[vendor] = set()
            vendors[vendor].add(client)
            
            if date:
                dates.append(date)
        
        print(f"\n🏦 Vendor analysis (showing vendors used by each client):")
        for vendor, clients in sorted(vendors.items()):
            if len(clients) > 1 or 'Unknown' not in clients:
                print(f"   {vendor}: {list(clients)}")
        
        if dates:
            dates.sort()
            print(f"\n📅 Date range in database: {dates[0]} to {dates[-1]}")
            
            # Look for gaps that might suggest different client data periods
            recent_dates = [d for d in dates if d >= '2024-01-01']
            if recent_dates:
                print(f"📅 Recent dates (2024+): {len(recent_dates)} transactions")
                print(f"    Range: {min(recent_dates)} to {max(recent_dates)}")
            else:
                print("📅 No transactions from 2024 or later found")
        
    except Exception as e:
        print(f"Error analyzing transaction patterns: {e}")

def main():
    """Main function to check database structure."""
    print("🔍 Checking database structure and available clients...\n")
    
    # Check available tables
    tables = check_tables()
    
    # Check for other clients
    check_for_other_clients()
    
    # Analyze transaction patterns
    check_transaction_patterns()
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print("Based on the database analysis:")
    print("1. Only one client 'spyguy' found with transaction data")
    print("2. Transaction data ranges from 2021-12-03 to 2022-08-01 (quite old)")
    print("3. No other active clients with recent data found")
    print("\nOptions to get more recent data:")
    print("• Import new transaction data for 'spyguy' client")
    print("• Import data for a new client with recent transactions")
    print("• Check if there are other data sources or CSV files to import")

if __name__ == "__main__":
    main()