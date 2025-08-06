#!/usr/bin/env python3
"""
Pattern Review Interface
Interactive HTML interface for reviewing and deciding on forecasting patterns
"""

import sys
sys.path.append('.')

from cash_flow_analysis_engine import CashFlowAnalysisEngine
from datetime import datetime, date
import json

def create_pattern_review_interface(client_id: str = 'bestself'):
    """Create interactive HTML interface for pattern review"""
    
    # Run analysis
    engine = CashFlowAnalysisEngine()
    analyses = engine.analyze_client_patterns(client_id)
    
    # Create HTML interface
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cash Flow Pattern Review - {client_id.title()}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .pattern-card {{ transition: all 0.3s ease; }}
        .pattern-card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.1); }}
        .accept {{ border-left: 4px solid #10B981; }}
        .modify {{ border-left: 4px solid #F59E0B; }}
        .manual {{ border-left: 4px solid #8B5CF6; }}
        .skip {{ border-left: 4px solid #EF4444; }}
        .confidence-bar {{ height: 8px; border-radius: 4px; transition: width 0.5s ease; }}
        .high-confidence {{ background: linear-gradient(90deg, #10B981, #059669); }}
        .medium-confidence {{ background: linear-gradient(90deg, #F59E0B, #D97706); }}
        .low-confidence {{ background: linear-gradient(90deg, #EF4444, #DC2626); }}
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-4 py-6">
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-3xl font-bold text-gray-900">💰 Cash Flow Pattern Review</h1>
                    <p class="text-gray-600 mt-1">Client: {client_id.title()} • Review analysis results and make forecasting decisions</p>
                </div>
                <div class="text-right">
                    <div class="text-sm text-gray-500">Analysis Date</div>
                    <div class="font-medium">{datetime.now().strftime('%B %d, %Y')}</div>
                </div>
            </div>
        </div>
    </header>

    <!-- Summary Stats -->
    <div class="max-w-7xl mx-auto px-4 py-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">'''
    
    # Calculate summary stats
    total_vendors = len(analyses)
    recommendations = {}
    categories = {}
    
    for analysis in analyses.values():
        rec = analysis.recommendation
        recommendations[rec] = recommendations.get(rec, 0) + 1
        
        cat = analysis.business_category
        categories[cat] = categories.get(cat, 0) + 1
    
    # Summary cards
    summary_cards = [
        ('Total Vendors', total_vendors, 'text-blue-600', '🏢'),
        ('Accept', recommendations.get('accept', 0), 'text-green-600', '✅'),
        ('Need Review', recommendations.get('modify', 0) + recommendations.get('manual', 0), 'text-yellow-600', '⚠️'),
        ('Skip', recommendations.get('skip', 0), 'text-red-600', '❌')
    ]
    
    for title, value, color, icon in summary_cards:
        html_content += f'''
            <div class="bg-white rounded-lg shadow p-6 text-center">
                <div class="text-2xl mb-2">{icon}</div>
                <div class="text-3xl font-bold {color}">{value}</div>
                <div class="text-sm text-gray-600">{title}</div>
            </div>'''
    
    html_content += '''
        </div>

        <!-- Filter Controls -->
        <div class="bg-white rounded-lg shadow p-4 mb-6">
            <div class="flex flex-wrap gap-4 items-center">
                <span class="font-medium text-gray-700">Filter by:</span>
                <select id="categoryFilter" class="border rounded px-3 py-1">
                    <option value="all">All Categories</option>'''
    
    for category in sorted(categories.keys()):
        html_content += f'<option value="{category}">{category.replace("_", " ").title()}</option>'
    
    html_content += '''
                </select>
                <select id="recommendationFilter" class="border rounded px-3 py-1">
                    <option value="all">All Recommendations</option>
                    <option value="accept">Accept</option>
                    <option value="modify">Modify</option>
                    <option value="manual">Manual</option>
                    <option value="skip">Skip</option>
                </select>
                <button onclick="exportDecisions()" class="bg-blue-600 text-white px-4 py-1 rounded hover:bg-blue-700">
                    📄 Export Decisions
                </button>
            </div>
        </div>

        <!-- Pattern Cards -->
        <div class="space-y-6" id="patternContainer">'''
    
    # Generate pattern cards
    for display_name, analysis in sorted(analyses.items()):
        pattern = analysis.pattern_analysis
        
        # Confidence styling
        confidence_class = 'high-confidence' if pattern.confidence >= 0.7 else 'medium-confidence' if pattern.confidence >= 0.4 else 'low-confidence'
        
        # Amount info
        if pattern.average_amount > 0:
            amount_class = 'text-green-600'
            amount_icon = '💰'
            amount_type = 'Revenue'
        else:
            amount_class = 'text-red-600'
            amount_icon = '💸'
            amount_type = 'Expense'
        
        # Business category icon
        category_icons = {
            'revenue_channels': '💰',
            'credit_cards': '💳',
            'people': '👥',
            'tax_payments': '📊',
            'inventory': '📦',
            'financial_services': '🏦',
            'other': '❓'
        }
        category_icon = category_icons.get(analysis.business_category, '❓')
        
        html_content += f'''
            <div class="pattern-card bg-white rounded-lg shadow p-6 {analysis.recommendation}" 
                 data-category="{analysis.business_category}" 
                 data-recommendation="{analysis.recommendation}">
                
                <!-- Header -->
                <div class="flex justify-between items-start mb-4">
                    <div class="flex items-center">
                        <span class="text-2xl mr-3">{category_icon}</span>
                        <div>
                            <h3 class="text-xl font-semibold text-gray-900">{display_name}</h3>
                            <p class="text-sm text-gray-600">{analysis.business_category.replace('_', ' ').title()}</p>
                        </div>
                    </div>
                    <div class="text-right">
                        <div class="text-2xl">{amount_icon}</div>
                        <div class="text-sm text-gray-600">{amount_type}</div>
                    </div>
                </div>
                
                <!-- Pattern Analysis -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div class="bg-gray-50 rounded-lg p-4">
                        <h4 class="font-medium text-gray-700 mb-2">Pattern Detected</h4>
                        <div class="text-lg font-semibold text-gray-900">{pattern.pattern_type.replace('_', ' ').title()}</div>
                        <div class="text-sm text-gray-600">{pattern.transaction_count} transactions</div>
                        <div class="mt-2">
                            <div class="text-xs text-gray-500 mb-1">Confidence: {pattern.confidence:.0%}</div>
                            <div class="w-full bg-gray-200 rounded-full h-2">
                                <div class="confidence-bar {confidence_class}" style="width: {pattern.confidence:.0%}"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="bg-gray-50 rounded-lg p-4">
                        <h4 class="font-medium text-gray-700 mb-2">Amount Analysis</h4>
                        <div class="text-lg font-semibold {amount_class}">${abs(pattern.average_amount):,.2f}</div>
                        <div class="text-sm text-gray-600">Average amount</div>
                        <div class="text-xs text-gray-500 mt-1">
                            Pattern: {pattern.amount_pattern.replace('_', ' ').title()}
                        </div>
                        <div class="text-xs text-gray-500">
                            Volatility: {pattern.amount_volatility:.1%}
                        </div>
                    </div>
                    
                    <div class="bg-gray-50 rounded-lg p-4">
                        <h4 class="font-medium text-gray-700 mb-2">Time Range</h4>
                        <div class="text-sm text-gray-600">
                            From: {pattern.date_range[0]}
                        </div>
                        <div class="text-sm text-gray-600">
                            To: {pattern.date_range[1]}
                        </div>
                        {f'<div class="text-xs text-gray-500 mt-1">Every {pattern.frequency_days} days</div>' if pattern.frequency_days else ''}
                    </div>
                </div>
                
                <!-- Recommendation -->
                <div class="bg-blue-50 rounded-lg p-4 mb-4">
                    <div class="flex items-start">
                        <span class="text-2xl mr-3">
                            {'✅' if analysis.recommendation == 'accept' else 
                             '⚠️' if analysis.recommendation == 'modify' else 
                             '🔧' if analysis.recommendation == 'manual' else '❌'}
                        </span>
                        <div>
                            <h4 class="font-medium text-gray-900 capitalize">{analysis.recommendation}</h4>
                            <p class="text-sm text-gray-600 mt-1">{analysis.reasoning}</p>
                        </div>
                    </div>
                </div>
                
                <!-- Decision Controls -->
                <div class="border-t pt-4">
                    <h4 class="font-medium text-gray-700 mb-3">Your Decision:</h4>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
                        <button onclick="setDecision('{display_name}', 'accept')" 
                                class="decision-btn px-3 py-2 rounded border text-sm hover:bg-green-50 hover:border-green-500">
                            ✅ Accept
                        </button>
                        <button onclick="setDecision('{display_name}', 'modify')" 
                                class="decision-btn px-3 py-2 rounded border text-sm hover:bg-yellow-50 hover:border-yellow-500">
                            ⚠️ Modify
                        </button>
                        <button onclick="setDecision('{display_name}', 'manual')" 
                                class="decision-btn px-3 py-2 rounded border text-sm hover:bg-purple-50 hover:border-purple-500">
                            🔧 Manual
                        </button>
                        <button onclick="setDecision('{display_name}', 'skip')" 
                                class="decision-btn px-3 py-2 rounded border text-sm hover:bg-red-50 hover:border-red-500">
                            ❌ Skip
                        </button>
                    </div>
                    
                    <!-- Manual Override Controls -->
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div>
                            <label class="block text-gray-600 mb-1">Override Pattern:</label>
                            <select class="w-full border rounded px-2 py-1" id="pattern_{display_name.replace(' ', '_')}">
                                <option value="">Keep detected</option>
                                <option value="weekly">Weekly</option>
                                <option value="bi-weekly">Bi-weekly</option>
                                <option value="monthly">Monthly</option>
                                <option value="quarterly">Quarterly</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-gray-600 mb-1">Override Amount ($):</label>
                            <input type="number" class="w-full border rounded px-2 py-1" 
                                   placeholder="${abs(pattern.average_amount):,.0f}"
                                   id="amount_{display_name.replace(' ', '_')}">
                        </div>
                        <div>
                            <label class="block text-gray-600 mb-1">Notes:</label>
                            <input type="text" class="w-full border rounded px-2 py-1" 
                                   placeholder="Optional notes..."
                                   id="notes_{display_name.replace(' ', '_')}">
                        </div>
                    </div>
                </div>
            </div>'''
    
    html_content += '''
        </div>
        
        <!-- Summary Actions -->
        <div class="mt-8 bg-white rounded-lg shadow p-6">
            <h3 class="text-lg font-semibold mb-4">Next Steps</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button onclick="generateForecasts()" 
                        class="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 font-medium">
                    🔮 Generate Forecasts
                </button>
                <button onclick="saveDecisions()" 
                        class="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 font-medium">
                    💾 Save Decisions
                </button>
                <button onclick="viewDashboard()" 
                        class="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 font-medium">
                    📊 View Dashboard
                </button>
            </div>
        </div>
    </div>

    <script>
        // Store user decisions
        let userDecisions = {};
        
        // Filter functions
        function filterPatterns() {
            const category = document.getElementById('categoryFilter').value;
            const recommendation = document.getElementById('recommendationFilter').value;
            const cards = document.querySelectorAll('.pattern-card');
            
            cards.forEach(card => {
                const cardCategory = card.getAttribute('data-category');
                const cardRecommendation = card.getAttribute('data-recommendation');
                
                const showCategory = category === 'all' || cardCategory === category;
                const showRecommendation = recommendation === 'all' || cardRecommendation === recommendation;
                
                if (showCategory && showRecommendation) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }
        
        // Set user decision
        function setDecision(vendorName, decision) {
            userDecisions[vendorName] = {
                decision: decision,
                timestamp: new Date().toISOString()
            };
            
            // Visual feedback
            const card = document.querySelector(`[data-category]`);
            const buttons = card?.parentElement.querySelectorAll('.decision-btn') || document.querySelectorAll('.decision-btn');
            
            // Reset all buttons in this card
            buttons.forEach(btn => {
                btn.classList.remove('bg-green-500', 'bg-yellow-500', 'bg-purple-500', 'bg-red-500', 'text-white');
            });
            
            // Highlight selected button
            event.target.classList.add(
                decision === 'accept' ? 'bg-green-500' : 
                decision === 'modify' ? 'bg-yellow-500' : 
                decision === 'manual' ? 'bg-purple-500' : 'bg-red-500',
                'text-white'
            );
            
            console.log(`Decision for ${vendorName}: ${decision}`);
        }
        
        // Export decisions
        function exportDecisions() {
            const decisions = Object.keys(userDecisions).length > 0 ? userDecisions : 'No decisions made yet';
            console.log('User Decisions:', decisions);
            alert('Decisions logged to console. In production, this would save to database.');
        }
        
        // Generate forecasts
        function generateForecasts() {
            const decidedVendors = Object.keys(userDecisions).length;
            if (decidedVendors === 0) {
                alert('Please make decisions on at least some vendors before generating forecasts.');
                return;
            }
            
            alert(`Ready to generate forecasts for ${decidedVendors} vendors with decisions. This would integrate with the forecasting engine.`);
        }
        
        // Save decisions
        function saveDecisions() {
            if (Object.keys(userDecisions).length === 0) {
                alert('No decisions to save yet.');
                return;
            }
            
            console.log('Saving decisions:', userDecisions);
            alert('Decisions saved! In production, this would update the database.');
        }
        
        // View dashboard
        function viewDashboard() {
            alert('This would redirect to the main forecasting dashboard with your decisions applied.');
        }
        
        // Add event listeners
        document.getElementById('categoryFilter').addEventListener('change', filterPatterns);
        document.getElementById('recommendationFilter').addEventListener('change', filterPatterns);
        
        // Initialize
        console.log('Pattern Review Interface loaded with {len(analyses)} vendors');
    </script>
</body>
</html>'''
    
    # Save HTML file
    output_file = '/Users/jeffreydebolt/Documents/cfo_forecast_refactored/pattern_review_interface.html'
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Pattern Review Interface created: {output_file}")
    return output_file

if __name__ == "__main__":
    print("🎨 CREATING PATTERN REVIEW INTERFACE")
    print("=" * 80)
    
    interface_file = create_pattern_review_interface('bestself')
    
    print(f"\n🎉 SUCCESS!")
    print(f"📊 Interactive review interface ready")
    print(f"🌐 Open {interface_file} in your browser")
    print(f"💡 Review patterns and make forecasting decisions")