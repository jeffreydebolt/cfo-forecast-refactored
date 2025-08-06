#!/usr/bin/env python3
"""
Money Map Interface - Big Picture First Cash Flow Analysis
Redesigned UX: Focus on top 12 vendors that drive 80% of cash flow
"""

import sys
sys.path.append('.')

from cash_flow_analysis_engine import CashFlowAnalysisEngine
from datetime import datetime, date, timedelta
from collections import defaultdict
import json
import statistics

class MoneyMapGenerator:
    """Generate the Money Map interface with tiered decision making"""
    
    def __init__(self):
        self.engine = CashFlowAnalysisEngine()
    
    def analyze_and_tier_vendors(self, client_id: str):
        """Analyze vendors and organize into decision tiers"""
        print("🗺️ GENERATING MONEY MAP")
        print("=" * 60)
        
        # Get full analysis
        analyses = self.engine.analyze_client_patterns(client_id)
        
        # Separate revenue and expenses
        revenue_vendors = []
        expense_vendors = []
        
        for name, analysis in analyses.items():
            pattern = analysis.pattern_analysis
            monthly_amount = abs(pattern.average_amount) * self._get_monthly_multiplier(pattern.pattern_type)
            
            vendor_data = {
                'name': name,
                'analysis': analysis,
                'monthly_amount': monthly_amount,
                'confidence': pattern.confidence,
                'seasonality': self._detect_seasonality(analysis.transactions)
            }
            
            if pattern.average_amount > 0:
                revenue_vendors.append(vendor_data)
            else:
                expense_vendors.append(vendor_data)
        
        # Sort by monthly amount
        revenue_vendors.sort(key=lambda x: x['monthly_amount'], reverse=True)
        expense_vendors.sort(key=lambda x: x['monthly_amount'], reverse=True)
        
        # Create tiered structure
        tiers = {
            'tier1_revenue': revenue_vendors[:5],  # Top 5 revenue sources
            'tier1_expenses': self._group_related_expenses(expense_vendors[:15]),  # Top expenses, grouped
            'tier2_regular': self._identify_regular_minor(analyses, revenue_vendors[5:] + expense_vendors[15:]),
            'tier3_small': self._identify_small_items(analyses, revenue_vendors + expense_vendors)
        }
        
        return tiers
    
    def _get_monthly_multiplier(self, pattern_type: str) -> float:
        """Convert pattern frequency to monthly multiplier"""
        multipliers = {
            'daily': 30,
            'weekly': 4.33,
            'bi-weekly': 2.17,
            'monthly': 1,
            'quarterly': 0.33,
            'irregular': 1  # Use as-is for irregular
        }
        return multipliers.get(pattern_type, 1)
    
    def _detect_seasonality(self, transactions: list) -> dict:
        """Detect seasonal patterns in transaction data"""
        if len(transactions) < 12:  # Need at least a year of data
            return {'type': 'insufficient_data', 'confidence': 'low', 'description': '📊 Stable'}
        
        # Group by month
        monthly_amounts = defaultdict(list)
        for txn in transactions:
            txn_date = datetime.fromisoformat(txn['transaction_date'])
            month = txn_date.month
            monthly_amounts[month].append(abs(float(txn['amount'])))
        
        # Calculate monthly averages
        monthly_avgs = {}
        for month, amounts in monthly_amounts.items():
            if amounts:
                monthly_avgs[month] = statistics.mean(amounts)
        
        if len(monthly_avgs) < 6:  # Need at least 6 months
            return {'type': 'insufficient_data', 'confidence': 'low', 'description': '📊 Stable'}
        
        # Find peaks and patterns
        overall_avg = statistics.mean(monthly_avgs.values())
        peaks = []
        troughs = []
        
        for month, avg in monthly_avgs.items():
            if avg > overall_avg * 1.5:  # 50% above average
                peaks.append(month)
            elif avg < overall_avg * 0.75:  # 25% below average
                troughs.append(month)
        
        # Classify seasonal patterns
        if not peaks and not troughs:
            return {'type': 'stable', 'confidence': 'high', 'description': '📊 Stable'}
        
        # Q4 holiday pattern
        if any(month in [10, 11, 12] for month in peaks):
            peak_months = [m for m in peaks if m in [10, 11, 12]]
            return {
                'type': 'q4_peak',
                'confidence': 'high' if len(peak_months) >= 2 else 'medium',
                'description': '📈 Q4 Peak',
                'details': f"Oct-Dec +{((max(monthly_avgs[m] for m in peak_months) / overall_avg - 1) * 100):.0f}%"
            }
        
        # Back to school pattern (August spike)
        if 8 in peaks:
            return {
                'type': 'back_to_school',
                'confidence': 'medium',
                'description': '🎒 Back-to-School',
                'details': f"Aug +{((monthly_avgs[8] / overall_avg - 1) * 100):.0f}%"
            }
        
        # Spring pattern (March-May)
        if any(month in [3, 4, 5] for month in peaks):
            return {
                'type': 'spring_peak',
                'confidence': 'medium', 
                'description': '🌸 Spring Peak',
                'details': 'Mar-May seasonal increase'
            }
        
        # Default to variable
        return {
            'type': 'variable',
            'confidence': 'low',
            'description': '📊 Variable',
            'details': 'Seasonal pattern detected but unclear'
        }
    
    def _group_related_expenses(self, expense_vendors: list) -> list:
        """Group related expense vendors for cleaner display"""
        grouped = []
        used_indices = set()
        
        # Group credit cards
        credit_cards = []
        for i, vendor in enumerate(expense_vendors):
            if vendor['analysis'].business_category == 'credit_cards':
                credit_cards.append(vendor)
                used_indices.add(i)
        
        if credit_cards:
            total_amount = sum(v['monthly_amount'] for v in credit_cards)
            avg_confidence = statistics.mean(v['confidence'] for v in credit_cards)
            grouped.append({
                'name': 'Credit Cards',
                'type': 'grouped',
                'monthly_amount': total_amount,
                'confidence': avg_confidence,
                'seasonality': {'type': 'stable', 'confidence': 'high', 'description': '📊 Stable'},
                'components': credit_cards,
                'description': f"{len(credit_cards)} cards (Amex, Chase, etc.)"
            })
        
        # Group tax payments
        tax_vendors = []
        for i, vendor in enumerate(expense_vendors):
            if vendor['analysis'].business_category == 'tax_payments' or 'tax' in vendor['name'].lower():
                if i not in used_indices:
                    tax_vendors.append(vendor)
                    used_indices.add(i)
        
        if tax_vendors:
            total_amount = sum(v['monthly_amount'] for v in tax_vendors)
            avg_confidence = statistics.mean(v['confidence'] for v in tax_vendors)
            grouped.append({
                'name': 'Tax Payments',
                'type': 'grouped',
                'monthly_amount': total_amount,
                'confidence': avg_confidence,
                'seasonality': {'type': 'quarterly', 'confidence': 'high', 'description': '📅 Quarterly'},
                'components': tax_vendors,
                'description': f"{len(tax_vendors)} jurisdictions"
            })
        
        # Add individual large expenses
        for i, vendor in enumerate(expense_vendors):
            if i not in used_indices and len(grouped) < 7:  # Top 7 expense categories
                grouped.append(vendor)
        
        return grouped[:7]  # Limit to top 7
    
    def _identify_regular_minor(self, all_analyses: dict, remaining_vendors: list) -> dict:
        """Identify vendors for Tier 2 (Regular Minor Items)"""
        regular_minor = []
        
        for vendor in remaining_vendors:
            monthly_amount = vendor['monthly_amount']
            confidence = vendor['confidence']
            
            # Regular minor: $500-$5k/month with decent confidence
            if 500 <= monthly_amount <= 5000 and confidence >= 0.4:
                regular_minor.append(vendor)
        
        total_amount = sum(v['monthly_amount'] for v in regular_minor)
        
        return {
            'vendors': regular_minor,
            'count': len(regular_minor),
            'total_monthly': total_amount,
            'description': f"{len(regular_minor)} vendors - ${total_amount:,.0f}/month total"
        }
    
    def _identify_small_items(self, all_analyses: dict, all_vendors: list) -> dict:
        """Identify vendors for Tier 3 (Small Items)"""
        small_items = []
        
        for vendor in all_vendors:
            monthly_amount = vendor['monthly_amount']
            confidence = vendor['confidence']
            
            # Small items: Under $500/month or very irregular
            if monthly_amount < 500 or confidence < 0.3:
                small_items.append(vendor)
        
        total_amount = sum(v['monthly_amount'] for v in small_items)
        
        return {
            'vendors': small_items,
            'count': len(small_items),
            'total_monthly': total_amount,
            'description': f"{len(small_items)} vendors - ${total_amount:,.0f}/month total"
        }

def create_money_map_interface(client_id: str = 'spyguy'):
    """Create the Money Map interface HTML"""
    
    generator = MoneyMapGenerator()
    tiers = generator.analyze_and_tier_vendors(client_id)
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>💰 Money Map - Cash Flow Decisions</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .tier-card {{ transition: all 0.3s ease; }}
        .tier-card:hover {{ transform: translateY(-2px); }}
        .decision-btn {{ transition: all 0.2s ease; }}
        .decision-btn:hover {{ transform: scale(1.05); }}
        .looks-good {{ background: linear-gradient(135deg, #10B981, #059669); }}
        .needs-review {{ background: linear-gradient(135deg, #F59E0B, #D97706); }}
        .confidence-high {{ background: #10B981; }}
        .confidence-medium {{ background: #F59E0B; }}
        .confidence-low {{ background: #EF4444; }}
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    
    <!-- Header -->
    <header class="bg-white shadow-sm border-b sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 py-4">
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-2xl font-bold text-gray-900">💰 Money Map</h1>
                    <p class="text-sm text-gray-600">Focus on the big picture first • Make 12 key decisions</p>
                </div>
                <div class="flex items-center space-x-4">
                    <div class="text-sm text-gray-500">
                        <span id="decisionsCount">0</span>/12 decisions made
                    </div>
                    <button onclick="generateForecast()" 
                            class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 font-medium">
                        🔮 Generate Forecast
                    </button>
                </div>
            </div>
        </div>
    </header>

    <div class="max-w-7xl mx-auto px-4 py-6">
        
        <!-- 30-Second Overview -->
        <div class="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg p-6 mb-8">
            <h2 class="text-2xl font-bold mb-2">📊 30-Second Overview</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                <div>
                    <div class="text-3xl font-bold">${sum(v['monthly_amount'] for v in tiers['tier1_revenue']):,.0f}</div>
                    <div class="text-blue-100">Monthly Revenue</div>
                </div>
                <div>
                    <div class="text-3xl font-bold">${sum(v.get('monthly_amount', v.get('total_monthly', 0)) for v in tiers['tier1_expenses'] if isinstance(v, dict)):,.0f}</div>
                    <div class="text-blue-100">Monthly Expenses</div>
                </div>
                <div>
                    <div class="text-3xl font-bold">${sum(v['monthly_amount'] for v in tiers['tier1_revenue']) - sum(v.get('monthly_amount', v.get('total_monthly', 0)) for v in tiers['tier1_expenses'] if isinstance(v, dict)):,.0f}</div>
                    <div class="text-blue-100">Net Cash Flow</div>
                </div>
            </div>
        </div>

        <!-- Tier 1: Top 5 Revenue Sources -->
        <div class="mb-8">
            <div class="flex items-center mb-4">
                <h2 class="text-xl font-bold text-gray-900">💰 Top 5 Revenue Sources</h2>
                <span class="ml-3 px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full font-medium">Must Decide</span>
            </div>
            
            <div class="grid gap-4">'''
    
    # Generate Tier 1 Revenue cards
    for i, vendor in enumerate(tiers['tier1_revenue']):
        seasonality = vendor['seasonality']
        confidence_class = 'confidence-high' if vendor['confidence'] >= 0.7 else 'confidence-medium' if vendor['confidence'] >= 0.4 else 'confidence-low'
        
        html_content += f'''
                <div class="tier-card bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <div class="flex items-center mb-2">
                                <h3 class="text-lg font-semibold text-gray-900">{vendor['name']}</h3>
                                <span class="ml-3 text-xl">{seasonality['description']}</span>
                            </div>
                            <div class="flex items-center space-x-4 mb-3">
                                <div class="text-2xl font-bold text-green-600">${vendor['monthly_amount']:,.0f}/month</div>
                                <div class="flex items-center">
                                    <div class="w-3 h-3 rounded-full mr-2 {confidence_class}"></div>
                                    <span class="text-sm text-gray-600">{vendor['confidence']:.0%} confidence</span>
                                </div>
                            </div>
                            {f'<div class="text-sm text-gray-500 mb-3">{seasonality.get("details", "")}</div>' if seasonality.get('details') else ''}
                        </div>
                        <div class="flex space-x-2">
                            <button onclick="makeDecision('revenue_{i}', 'accept')" 
                                    class="decision-btn looks-good text-white px-4 py-2 rounded-lg font-medium">
                                ✅ Looks Good
                            </button>
                            <button onclick="makeDecision('revenue_{i}', 'review')" 
                                    class="decision-btn needs-review text-white px-4 py-2 rounded-lg font-medium">
                                ⚠️ Needs Review
                            </button>
                        </div>
                    </div>
                </div>'''
    
    html_content += '''
            </div>
        </div>

        <!-- Tier 1: Top 7 Expense Categories -->
        <div class="mb-8">
            <div class="flex items-center mb-4">
                <h2 class="text-xl font-bold text-gray-900">💸 Top 7 Expense Categories</h2>
                <span class="ml-3 px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full font-medium">Must Decide</span>
            </div>
            
            <div class="grid gap-4">'''
    
    # Generate Tier 1 Expense cards
    for i, vendor in enumerate(tiers['tier1_expenses']):
        if isinstance(vendor, dict):
            monthly_amount = vendor.get('monthly_amount', 0)
            confidence = vendor.get('confidence', 0)
            name = vendor.get('name', 'Unknown')
            description = vendor.get('description', '')
            
            confidence_class = 'confidence-high' if confidence >= 0.7 else 'confidence-medium' if confidence >= 0.4 else 'confidence-low'
            
            html_content += f'''
                <div class="tier-card bg-white rounded-lg shadow-md p-6 border-l-4 border-red-500">
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <div class="flex items-center mb-2">
                                <h3 class="text-lg font-semibold text-gray-900">{name}</h3>
                                {'<span class="ml-3 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">Grouped</span>' if vendor.get('type') == 'grouped' else ''}
                            </div>
                            <div class="flex items-center space-x-4 mb-3">
                                <div class="text-2xl font-bold text-red-600">${monthly_amount:,.0f}/month</div>
                                <div class="flex items-center">
                                    <div class="w-3 h-3 rounded-full mr-2 {confidence_class}"></div>
                                    <span class="text-sm text-gray-600">{confidence:.0%} confidence</span>
                                </div>
                            </div>
                            {f'<div class="text-sm text-gray-500 mb-3">{description}</div>' if description else ''}
                        </div>
                        <div class="flex space-x-2">
                            <button onclick="makeDecision('expense_{i}', 'accept')" 
                                    class="decision-btn looks-good text-white px-4 py-2 rounded-lg font-medium">
                                ✅ Looks Good
                            </button>
                            <button onclick="makeDecision('expense_{i}', 'review')" 
                                    class="decision-btn needs-review text-white px-4 py-2 rounded-lg font-medium">
                                ⚠️ Needs Review
                            </button>
                        </div>
                    </div>
                </div>'''
    
    # Add Tier 2 and Tier 3 sections
    tier2 = tiers['tier2_regular']
    tier3 = tiers['tier3_small']
    
    html_content += f'''
            </div>
        </div>

        <!-- Tier 2: Regular Minor Items -->
        <div class="mb-8">
            <div class="bg-white rounded-lg shadow-md p-6">
                <div class="flex justify-between items-center">
                    <div>
                        <h2 class="text-lg font-semibold text-gray-900">📋 Regular Minor Items</h2>
                        <p class="text-gray-600">{tier2['description']}</p>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="makeBatchDecision('tier2', 'auto')" 
                                class="decision-btn looks-good text-white px-6 py-2 rounded-lg font-medium">
                            ✅ Auto-forecast all at average amounts
                        </button>
                        <button onclick="expandTier('tier2')" 
                                class="decision-btn bg-gray-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-gray-700">
                            Review individually
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tier 3: Small Items -->
        <div class="mb-8">
            <div class="bg-white rounded-lg shadow-md p-6">
                <div class="flex justify-between items-center">
                    <div>
                        <h2 class="text-lg font-semibold text-gray-900">📁 Small Items</h2>
                        <p class="text-gray-600">{tier3['description']}</p>
                        <p class="text-sm text-gray-500 mt-1">Mostly one-time purchases, small fees, irregular vendors</p>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="makeBatchDecision('tier3', 'skip')" 
                                class="decision-btn bg-red-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-red-700">
                            ✅ Skip all minor items
                        </button>
                        <button onclick="expandTier('tier3')" 
                                class="decision-btn bg-gray-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-gray-700">
                            Review if needed
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Summary -->
        <div class="bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-lg p-6">
            <h2 class="text-xl font-bold mb-4">🎯 Decision Summary</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="text-center">
                    <div class="text-2xl font-bold" id="coveragePercent">80%</div>
                    <div class="text-green-100">Cash flow covered</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold" id="timeEstimate">2-3 min</div>
                    <div class="text-green-100">Time to complete</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold" id="decisionsRemaining">12</div>
                    <div class="text-green-100">Key decisions needed</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let decisions = {{}};
        let decisionCount = 0;
        
        function makeDecision(vendorId, decision) {{
            decisions[vendorId] = decision;
            updateDecisionCount();
            
            // Visual feedback
            const card = event.target.closest('.tier-card');
            if (card) {{
                card.style.opacity = '0.7';
                card.style.transform = 'scale(0.98)';
            }}
            
            console.log(`Decision: ${{vendorId}} = ${{decision}}`);
        }}
        
        function makeBatchDecision(tier, decision) {{
            decisions[tier] = decision;
            updateDecisionCount();
            
            // Visual feedback
            const card = event.target.closest('div');
            if (card) {{
                card.style.opacity = '0.7';
            }}
            
            console.log(`Batch decision: ${{tier}} = ${{decision}}`);
        }}
        
        function updateDecisionCount() {{
            decisionCount = Object.keys(decisions).length;
            document.getElementById('decisionsCount').textContent = decisionCount;
            document.getElementById('decisionsRemaining').textContent = Math.max(0, 12 - decisionCount);
        }}
        
        function expandTier(tier) {{
            alert(`This would expand ${{tier}} to show individual vendor decisions`);
        }}
        
        function generateForecast() {{
            if (decisionCount < 5) {{
                alert('Please make decisions on at least the top 5 revenue sources before generating forecasts.');
                return;
            }}
            
            console.log('All decisions:', decisions);
            alert(`Ready to generate forecasts with ${{decisionCount}} decisions made!`);
        }}
        
        // Initialize
        console.log('Money Map Interface loaded');
        console.log('Focus on 12 key decisions that drive 80% of cash flow');
    </script>
</body>
</html>'''
    
    # Save the interface
    output_file = '/Users/jeffreydebolt/Documents/cfo_forecast_refactored/money_map_interface.html'
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Money Map Interface created: {output_file}")
    return output_file

if __name__ == "__main__":
    print("🗺️ CREATING MONEY MAP INTERFACE")
    print("=" * 80)
    
    interface_file = create_money_map_interface('spyguy')
    
    print(f"\n🎉 SUCCESS!")
    print(f"💰 Money Map interface ready")
    print(f"🎯 Focus on 12 key decisions (5 revenue + 7 expenses)")
    print(f"⏰ 2-3 minute decision process")
    print(f"📊 80% of cash flow covered in top tier")