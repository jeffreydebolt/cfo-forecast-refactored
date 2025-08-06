"""
Weekly Cash Flow Table Generator
Creates a week-by-week cash flow projection table.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from collections import defaultdict
import pandas as pd

from supabase_client import supabase
from config.client_context import get_current_client

logger = logging.getLogger(__name__)


class WeeklyCashFlow:
    """Generates weekly cash flow projections."""
    
    def __init__(self, client_id: str = None, weeks_ahead: int = 13):
        """
        Initialize the weekly cash flow generator.
        
        Args:
            client_id: Client ID (uses current if None)
            weeks_ahead: Number of weeks to project (default 13)
        """
        self.client_id = client_id or get_current_client()
        self.weeks_ahead = weeks_ahead
        self.start_date = self._get_week_start()
        
    def _get_week_start(self) -> datetime:
        """Get the start of the current week (Monday)."""
        today = datetime.now()
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        return monday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def _get_current_balance(self) -> float:
        """Get the current bank balance."""
        # TODO: This should come from a balance tracking table
        # For now, calculate from transactions
        try:
            result = supabase.table('transactions') \
                .select('amount') \
                .eq('client_id', self.client_id) \
                .execute()
            
            if result.data:
                return sum(float(t['amount']) for t in result.data)
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting current balance: {e}")
            return 0.0
    
    def _get_forecasted_transactions(self) -> List[Dict[str, Any]]:
        """Get forecasted transactions for the projection period."""
        try:
            # Get vendor configurations with forecast settings
            vendors = supabase.table('vendors') \
                .select('*') \
                .eq('client_id', self.client_id) \
                .not_.is_('forecast_method', 'null') \
                .execute()
            
            # Group vendors by display_name to avoid duplicates
            vendors_by_name = {}
            for vendor in vendors.data:
                display_name = vendor.get('display_name')
                if display_name and vendor.get('forecast_amount') is not None:
                    # Only keep the first entry for each display name
                    if display_name not in vendors_by_name:
                        vendors_by_name[display_name] = vendor
            
            forecasted_txns = []
            end_date = self.start_date + timedelta(weeks=self.weeks_ahead)
            
            for vendor in vendors_by_name.values():
                if vendor.get('forecast_method') in ['regular', 'trailing_avg']:
                    # Generate transactions based on frequency
                    txns = self._generate_regular_transactions(
                        vendor,
                        self.start_date,
                        end_date
                    )
                    forecasted_txns.extend(txns)
                elif vendor.get('forecast_method') == 'irregular':
                    # Use average amount with lower confidence
                    txns = self._generate_irregular_transactions(
                        vendor,
                        self.start_date,
                        end_date
                    )
                    forecasted_txns.extend(txns)
            
            return forecasted_txns
            
        except Exception as e:
            logger.error(f"Error getting forecasted transactions: {e}")
            return []
    
    def _generate_regular_transactions(
        self,
        vendor: Dict[str, Any],
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Generate regular transactions based on frequency."""
        transactions = []
        
        frequency = vendor.get('forecast_frequency', 'monthly')
        amount = float(vendor.get('forecast_amount', 0))
        
        if amount == 0:
            return transactions
        
        current_date = start_date
        
        if frequency == 'weekly':
            while current_date < end_date:
                transactions.append({
                    'date': current_date,
                    'vendor_name': vendor['display_name'],
                    'amount': amount,
                    'confidence': 0.9,
                    'type': 'forecast'
                })
                current_date += timedelta(weeks=1)
                
        elif frequency == 'bi-weekly':
            while current_date < end_date:
                transactions.append({
                    'date': current_date,
                    'vendor_name': vendor['display_name'],
                    'amount': amount,
                    'confidence': 0.85,
                    'type': 'forecast'
                })
                current_date += timedelta(weeks=2)
                
        elif frequency == 'monthly':
            # Approximate monthly as every 4 weeks
            while current_date < end_date:
                transactions.append({
                    'date': current_date,
                    'vendor_name': vendor['display_name'],
                    'amount': amount,
                    'confidence': 0.8,
                    'type': 'forecast'
                })
                current_date += timedelta(weeks=4)
        
        return transactions
    
    def _generate_irregular_transactions(
        self,
        vendor: Dict[str, Any],
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Generate irregular transactions using averages."""
        # For irregular vendors, we might spread the average across the period
        # This is a simplified approach - could be enhanced
        return []
    
    def _get_week_number(self, date: datetime) -> int:
        """Get the week number relative to start date."""
        delta = date - self.start_date
        return delta.days // 7
    
    def generate_weekly_projection(self) -> Dict[str, Any]:
        """
        Generate the weekly cash flow projection.
        
        Returns:
            Dictionary containing weekly projection data
        """
        # Initialize weekly buckets
        weeks = []
        for week_num in range(self.weeks_ahead):
            week_start = self.start_date + timedelta(weeks=week_num)
            week_end = week_start + timedelta(days=6)
            
            weeks.append({
                'week_num': week_num + 1,
                'start_date': week_start,
                'end_date': week_end,
                'deposits': 0.0,
                'withdrawals': 0.0,
                'transactions': []
            })
        
        # Get starting balance
        starting_balance = self._get_current_balance()
        
        # Get forecasted transactions
        forecasted_txns = self._get_forecasted_transactions()
        
        # Bucket transactions into weeks
        for txn in forecasted_txns:
            week_num = self._get_week_number(txn['date'])
            if 0 <= week_num < self.weeks_ahead:
                if txn['amount'] > 0:
                    weeks[week_num]['deposits'] += txn['amount']
                else:
                    weeks[week_num]['withdrawals'] += txn['amount']
                weeks[week_num]['transactions'].append(txn)
        
        # Calculate running balances
        current_balance = starting_balance
        for week in weeks:
            week['starting_balance'] = current_balance
            week['net_movement'] = week['deposits'] + week['withdrawals']
            current_balance += week['net_movement']
            week['ending_balance'] = current_balance
        
        return {
            'starting_balance': starting_balance,
            'weeks': weeks,
            'final_balance': current_balance,
            'generated_at': datetime.now(),
            'client_id': self.client_id
        }
    
    def format_as_table(self, projection: Dict[str, Any]) -> str:
        """
        Format the projection as a text table.
        
        Args:
            projection: The projection data from generate_weekly_projection
            
        Returns:
            Formatted table string
        """
        lines = []
        lines.append("\n" + "=" * 100)
        lines.append(f"WEEKLY CASH FLOW PROJECTION - {self.client_id}")
        lines.append(f"Generated: {projection['generated_at'].strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 100)
        
        # Header
        header = f"{'Week':>6} | {'Dates':^20} | {'Starting':>12} | {'Deposits':>12} | {'Withdrawals':>12} | {'Net':>12} | {'Ending':>12}"
        lines.append(header)
        lines.append("-" * 100)
        
        # Data rows
        for week in projection['weeks']:
            date_range = f"{week['start_date'].strftime('%m/%d')} - {week['end_date'].strftime('%m/%d')}"
            
            row = f"{week['week_num']:>6} | {date_range:^20} | "
            row += f"${week['starting_balance']:>11,.2f} | "
            row += f"${week['deposits']:>11,.2f} | "
            row += f"${abs(week['withdrawals']):>11,.2f} | "
            
            net = week['net_movement']
            if net >= 0:
                row += f"+${net:>10,.2f} | "
            else:
                row += f"-${abs(net):>10,.2f} | "
            
            # Highlight low balances
            if week['ending_balance'] < 10000:
                row += f"${week['ending_balance']:>11,.2f} ⚠️"
            else:
                row += f"${week['ending_balance']:>11,.2f}"
            
            lines.append(row)
        
        lines.append("=" * 100)
        lines.append(f"Starting Balance: ${projection['starting_balance']:,.2f}")
        lines.append(f"Final Balance: ${projection['final_balance']:,.2f}")
        lines.append(f"Total Change: ${projection['final_balance'] - projection['starting_balance']:,.2f}")
        
        return "\n".join(lines)
    
    def export_to_html(self, projection: Dict[str, Any]) -> str:
        """
        Export the projection as an HTML table.
        
        Args:
            projection: The projection data
            
        Returns:
            HTML string
        """
        html = f"""
        <html>
        <head>
            <title>Weekly Cash Flow - {self.client_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
                th {{ background-color: #4CAF50; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .negative {{ color: red; }}
                .positive {{ color: green; }}
                .warning {{ background-color: #ffeb3b; }}
                .critical {{ background-color: #ff9800; color: white; }}
            </style>
        </head>
        <body>
            <h1>Weekly Cash Flow Projection</h1>
            <p>Client: {self.client_id}</p>
            <p>Generated: {projection['generated_at'].strftime('%Y-%m-%d %H:%M')}</p>
            
            <table>
                <tr>
                    <th>Week</th>
                    <th>Period</th>
                    <th>Starting Balance</th>
                    <th>Deposits</th>
                    <th>Withdrawals</th>
                    <th>Net Movement</th>
                    <th>Ending Balance</th>
                </tr>
        """
        
        for week in projection['weeks']:
            date_range = f"{week['start_date'].strftime('%m/%d')} - {week['end_date'].strftime('%m/%d')}"
            
            # Determine row class based on ending balance
            row_class = ""
            if week['ending_balance'] < 5000:
                row_class = "critical"
            elif week['ending_balance'] < 10000:
                row_class = "warning"
            
            html += f"""
                <tr class="{row_class}">
                    <td>{week['week_num']}</td>
                    <td>{date_range}</td>
                    <td>${week['starting_balance']:,.2f}</td>
                    <td class="positive">${week['deposits']:,.2f}</td>
                    <td class="negative">${abs(week['withdrawals']):,.2f}</td>
                    <td class="{'positive' if week['net_movement'] >= 0 else 'negative'}">
                        ${week['net_movement']:,.2f}
                    </td>
                    <td>${week['ending_balance']:,.2f}</td>
                </tr>
            """
        
        html += f"""
            </table>
            
            <h3>Summary</h3>
            <p>Starting Balance: ${projection['starting_balance']:,.2f}</p>
            <p>Final Balance: ${projection['final_balance']:,.2f}</p>
            <p>Total Change: ${projection['final_balance'] - projection['starting_balance']:,.2f}</p>
        </body>
        </html>
        """
        
        return html


def generate_weekly_cash_flow(client_id: str = None, weeks: int = 13) -> Dict[str, Any]:
    """Convenience function to generate weekly cash flow."""
    generator = WeeklyCashFlow(client_id, weeks)
    return generator.generate_weekly_projection()


def display_weekly_cash_flow(client_id: str = None, weeks: int = 13):
    """Generate and display weekly cash flow table."""
    generator = WeeklyCashFlow(client_id, weeks)
    projection = generator.generate_weekly_projection()
    print(generator.format_as_table(projection))
    
    # Also save HTML version
    html_file = f"weekly_cash_flow_{client_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(html_file, 'w') as f:
        f.write(generator.export_to_html(projection))
    print(f"\nHTML version saved to: {html_file}")


if __name__ == "__main__":
    # Test the weekly cash flow generator
    logging.basicConfig(level=logging.INFO)
    
    display_weekly_cash_flow()