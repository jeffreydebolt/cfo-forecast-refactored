"""
Analyze all available clients and their transaction data to help user choose
a client with more recent data.
"""

from supabase_client import supabase
from datetime import datetime
import sys

def get_all_clients():
    """Get all unique client IDs from the transactions table."""
    try:
        result = supabase.table('transactions') \
            .select('client_id') \
            .execute()
        
        if not result.data:
            print("No transactions found in database")
            return []
        
        # Get unique client IDs
        client_ids = list(set(txn['client_id'] for txn in result.data if txn['client_id']))
        return sorted(client_ids)
        
    except Exception as e:
        print(f"Error getting clients: {e}")
        return []

def analyze_client_transactions(client_id: str):
    """Analyze transaction data for a specific client."""
    try:
        # Get transaction summary for this client
        result = supabase.table('transactions') \
            .select('transaction_date, amount') \
            .eq('client_id', client_id) \
            .order('transaction_date', desc=False) \
            .execute()
        
        if not result.data:
            return {
                'client_id': client_id,
                'transaction_count': 0,
                'earliest_date': None,
                'latest_date': None,
                'total_amount': 0,
                'error': 'No transactions found'
            }
        
        transactions = result.data
        dates = [txn['transaction_date'] for txn in transactions]
        amounts = [float(txn['amount']) for txn in transactions]
        
        return {
            'client_id': client_id,
            'transaction_count': len(transactions),
            'earliest_date': min(dates),
            'latest_date': max(dates),
            'total_amount': sum(amounts),
            'avg_monthly_transactions': len(transactions) / max(1, len(set(date[:7] for date in dates))),
            'recent_activity': len([d for d in dates if d >= '2025-06-01'])  # Transactions since June 2025
        }
        
    except Exception as e:
        return {
            'client_id': client_id,
            'transaction_count': 0,
            'earliest_date': None,
            'latest_date': None,
            'total_amount': 0,
            'error': str(e)
        }

def main():
    """Main function to analyze all clients."""
    print("🔍 Analyzing all available clients and their transaction data...\n")
    
    # Get all clients
    clients = get_all_clients()
    
    if not clients:
        print("❌ No clients found in database")
        return
    
    print(f"Found {len(clients)} clients: {', '.join(clients)}\n")
    
    # Analyze each client
    client_analyses = []
    for client_id in clients:
        print(f"Analyzing {client_id}...")
        analysis = analyze_client_transactions(client_id)
        client_analyses.append(analysis)
    
    # Sort by latest transaction date (most recent first)
    client_analyses.sort(key=lambda x: x.get('latest_date', '0000-00-00'), reverse=True)
    
    # Display results
    print("\n" + "="*100)
    print("CLIENT ANALYSIS RESULTS")
    print("="*100)
    print(f"{'Client ID':<15} {'Transactions':<12} {'Date Range':<25} {'Latest Date':<12} {'Recent Activity':<15} {'Status'}")
    print("-"*100)
    
    for analysis in client_analyses:
        client_id = analysis['client_id']
        count = analysis['transaction_count']
        
        if analysis.get('error'):
            print(f"{client_id:<15} {'N/A':<12} {'N/A':<25} {'N/A':<12} {'N/A':<15} {analysis['error']}")
            continue
        
        earliest = analysis['earliest_date']
        latest = analysis['latest_date']
        recent = analysis['recent_activity']
        
        if earliest and latest:
            date_range = f"{earliest} to {latest}"
            
            # Determine status based on latest date
            if latest >= '2025-07-01':
                status = "🟢 Current (July 2025+)"
            elif latest >= '2025-06-01':
                status = "🟡 Recent (June 2025+)"
            elif latest >= '2025-01-01':
                status = "🟠 This Year (2025)"
            else:
                status = "🔴 Older Data"
                
        else:
            date_range = "No dates available"
            status = "❌ No data"
        
        print(f"{client_id:<15} {count:<12} {date_range:<25} {latest:<12} {recent:<15} {status}")
    
    # Recommendations
    print("\n" + "="*100)
    print("RECOMMENDATIONS")
    print("="*100)
    
    # Find client with most recent data
    current_clients = [c for c in client_analyses if c.get('latest_date', '0000-00-00') >= '2025-07-01']
    recent_clients = [c for c in client_analyses if c.get('latest_date', '0000-00-00') >= '2025-06-01']
    active_clients = [c for c in client_analyses if c.get('transaction_count', 0) > 100]
    
    if current_clients:
        best_client = current_clients[0]
        print(f"✅ BEST OPTION: '{best_client['client_id']}' has the most recent data")
        print(f"   - {best_client['transaction_count']} transactions")
        print(f"   - Latest transaction: {best_client['latest_date']}")
        print(f"   - {best_client['recent_activity']} transactions since June 2025")
    elif recent_clients:
        best_client = recent_clients[0]
        print(f"⭐ GOOD OPTION: '{best_client['client_id']}' has recent data")
        print(f"   - {best_client['transaction_count']} transactions")
        print(f"   - Latest transaction: {best_client['latest_date']}")
        print(f"   - {best_client['recent_activity']} transactions since June 2025")
    elif active_clients:
        best_client = active_clients[0]
        print(f"📊 ACTIVE OPTION: '{best_client['client_id']}' has most transaction data")
        print(f"   - {best_client['transaction_count']} transactions")
        print(f"   - Latest transaction: {best_client['latest_date']}")
    else:
        print("⚠️  No clients have substantial recent data")
    
    print(f"\n💡 To switch to a different client, you can use:")
    for analysis in client_analyses[:3]:  # Show top 3 options
        if analysis.get('transaction_count', 0) > 0:
            print(f"   python main.py --client {analysis['client_id']}")
    
    print(f"\n📊 Current working directory client context can be checked in:")
    print(f"   config/client_context.py")

if __name__ == "__main__":
    main()