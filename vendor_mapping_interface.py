#!/usr/bin/env python3
"""
Vendor Mapping Interface
Phase 1: Interactive interface for reviewing and approving vendor grouping suggestions
"""

import sys
sys.path.append('.')

from smart_vendor_grouping import SmartVendorGrouping
from datetime import datetime
import json

def create_vendor_mapping_interface(client_id: str = 'spyguy'):
    """Create interactive interface for vendor mapping decisions"""
    
    # Get grouping suggestions
    grouping = SmartVendorGrouping()
    suggestions = grouping.analyze_and_suggest_groupings(client_id)
    
    # Calculate totals for overview
    total_vendors = sum(len(suggestion.vendors) for groups in suggestions.values() for suggestion in groups)
    total_monthly = sum(suggestion.total_monthly_amount for groups in suggestions.values() for suggestion in groups)
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🗺️ Vendor Mapping - Phase 1 Setup</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .suggestion-card {{ transition: all 0.3s ease; }}
        .suggestion-card:hover {{ transform: translateY(-2px); }}
        .vendor-item {{ transition: all 0.2s ease; }}
        .vendor-item:hover {{ background-color: #f9fafb; }}
        .confidence-high {{ border-left: 4px solid #10B981; }}
        .confidence-medium {{ border-left: 4px solid #F59E0B; }}
        .confidence-low {{ border-left: 4px solid #EF4444; }}
        .accepted {{ background: #F0FDF4; border-color: #10B981; }}
        .rejected {{ background: #FEF2F2; border-color: #EF4444; }}
        .custom {{ background: #FEF3E2; border-color: #F59E0B; }}
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    
    <!-- Header -->
    <header class="bg-white shadow-sm border-b sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 py-4">
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-2xl font-bold text-gray-900">🗺️ Vendor Mapping - Phase 1</h1>
                    <p class="text-sm text-gray-600">Review grouping suggestions • Create meaningful business entities</p>
                </div>
                <div class="flex items-center space-x-4">
                    <div class="text-sm text-gray-500">
                        <span id="decisionsCount">0</span>/{len(suggestions['high_confidence']) + len(suggestions['medium_confidence'])} decisions made
                    </div>
                    <button onclick="proceedToPhase2()" 
                            class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 font-medium"
                            id="phase2Button" disabled>
                        🚀 Proceed to Phase 2
                    </button>
                </div>
            </div>
        </div>
    </header>

    <div class="max-w-7xl mx-auto px-4 py-6">
        
        <!-- Overview -->
        <div class="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg p-6 mb-8">
            <h2 class="text-2xl font-bold mb-2">📊 Grouping Analysis Complete</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                <div>
                    <div class="text-3xl font-bold">42</div>
                    <div class="text-blue-100">Individual Vendors</div>
                </div>
                <div>
                    <div class="text-3xl font-bold">{len(suggestions['high_confidence']) + len(suggestions['medium_confidence'])}</div>
                    <div class="text-blue-100">Suggested Groups</div>
                </div>
                <div>
                    <div class="text-3xl font-bold">${total_monthly:,.0f}</div>
                    <div class="text-blue-100">Monthly Volume</div>
                </div>
            </div>
        </div>

        <!-- High Confidence Suggestions -->
        <div class="mb-8">
            <div class="flex items-center mb-6">
                <h2 class="text-xl font-bold text-gray-900">✅ High Confidence Suggestions</h2>
                <button onclick="acceptAllHigh()" 
                        class="ml-4 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm font-medium">
                    Accept All
                </button>
                <span class="ml-2 text-sm text-gray-600">| Review Individually</span>
            </div>
            
            <div class="space-y-6">'''
    
    # Generate High Confidence Cards
    for i, suggestion in enumerate(suggestions['high_confidence']):
        html_content += f'''
                <div class="suggestion-card confidence-high bg-white rounded-lg shadow-md p-6" id="high_{i}">
                    <div class="flex justify-between items-start mb-4">
                        <div class="flex-1">
                            <div class="flex items-center mb-2">
                                <h3 class="text-lg font-semibold text-gray-900">{suggestion.display_name}</h3>
                                <span class="ml-3 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full font-medium">
                                    {len(suggestion.vendors)} vendors → 1 group
                                </span>
                            </div>
                            <p class="text-sm text-gray-600 mb-3">{suggestion.reasoning}</p>
                            <div class="text-lg font-bold text-green-600 mb-3">${suggestion.total_monthly_amount:,.0f}/month combined</div>
                        </div>
                    </div>
                    
                    <!-- Vendor Details -->
                    <div class="bg-gray-50 rounded-lg p-4 mb-4">
                        <h4 class="font-medium text-gray-700 mb-3">Vendors to be grouped:</h4>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-2">'''
        
        for vendor in suggestion.vendors:
            html_content += f'''
                            <div class="vendor-item flex justify-between items-center py-2 px-3 bg-white rounded border">
                                <span class="text-sm font-medium text-gray-900">{vendor['vendor_name']}</span>
                                <div class="text-right">
                                    <div class="text-sm font-medium text-gray-900">${vendor['monthly_amount']:,.0f}/month</div>
                                    <div class="text-xs text-gray-500">{vendor['transaction_count']} transactions</div>
                                </div>
                            </div>'''
        
        html_content += f'''
                        </div>
                    </div>
                    
                    <!-- Decision Buttons -->
                    <div class="flex justify-between items-center">
                        <div class="text-sm text-gray-600">
                            Business Category: <span class="font-medium">{suggestion.business_category}</span>
                        </div>
                        <div class="flex space-x-2">
                            <button onclick="makeDecision('high_{i}', 'accept', '{suggestion.display_name}')" 
                                    class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 font-medium">
                                ✅ Accept Grouping
                            </button>
                            <button onclick="showCustomNaming('high_{i}')" 
                                    class="bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 font-medium">
                                ✏️ Custom Name
                            </button>
                            <button onclick="makeDecision('high_{i}', 'reject', '')" 
                                    class="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 font-medium">
                                ❌ Keep Separate
                            </button>
                        </div>
                    </div>
                    
                    <!-- Custom Naming (Hidden) -->
                    <div id="custom_high_{i}" class="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg hidden">
                        <label class="block text-sm font-medium text-gray-700 mb-2">Custom Group Name:</label>
                        <div class="flex space-x-2">
                            <input type="text" class="flex-1 border rounded px-3 py-2" 
                                   placeholder="{suggestion.display_name}" 
                                   id="customName_high_{i}">
                            <button onclick="acceptCustomName('high_{i}')" 
                                    class="bg-yellow-600 text-white px-4 py-2 rounded hover:bg-yellow-700">
                                Save
                            </button>
                        </div>
                    </div>
                </div>'''
    
    html_content += '''
            </div>
        </div>

        <!-- Medium Confidence Suggestions -->
        <div class="mb-8">
            <div class="flex items-center mb-6">
                <h2 class="text-xl font-bold text-gray-900">⚠️ Medium Confidence Suggestions</h2>
                <span class="ml-3 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full font-medium">Review Required</span>
            </div>
            
            <div class="space-y-6">'''
    
    # Generate Medium Confidence Cards
    for i, suggestion in enumerate(suggestions['medium_confidence']):
        html_content += f'''
                <div class="suggestion-card confidence-medium bg-white rounded-lg shadow-md p-6" id="medium_{i}">
                    <div class="flex justify-between items-start mb-4">
                        <div class="flex-1">
                            <div class="flex items-center mb-2">
                                <h3 class="text-lg font-semibold text-gray-900">{suggestion.display_name}</h3>
                                <span class="ml-3 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full font-medium">
                                    {len(suggestion.vendors)} vendors → review needed
                                </span>
                            </div>
                            <p class="text-sm text-gray-600 mb-3">{suggestion.reasoning}</p>
                            <div class="text-lg font-bold text-yellow-600 mb-3">${suggestion.total_monthly_amount:,.0f}/month combined</div>
                        </div>
                    </div>
                    
                    <!-- Vendor Details -->
                    <div class="bg-gray-50 rounded-lg p-4 mb-4">
                        <h4 class="font-medium text-gray-700 mb-3">Vendors to be grouped:</h4>
                        <div class="space-y-2">'''
        
        for vendor in suggestion.vendors:
            html_content += f'''
                            <div class="vendor-item flex justify-between items-center py-2 px-3 bg-white rounded border">
                                <span class="text-sm font-medium text-gray-900">{vendor['vendor_name']}</span>
                                <div class="text-right">
                                    <div class="text-sm font-medium text-gray-900">${vendor['monthly_amount']:,.0f}/month</div>
                                    <div class="text-xs text-gray-500">{vendor['transaction_count']} transactions</div>
                                </div>
                            </div>'''
        
        html_content += f'''
                        </div>
                        <div class="mt-3 p-3 bg-yellow-50 rounded border border-yellow-200">
                            <p class="text-sm text-yellow-800">
                                <strong>Consider:</strong> Do you need to track these separately for business reasons, 
                                or is grouping as "{suggestion.display_name}" appropriate?
                            </p>
                        </div>
                    </div>
                    
                    <!-- Decision Buttons -->
                    <div class="flex justify-between items-center">
                        <div class="text-sm text-gray-600">
                            Business Category: <span class="font-medium">{suggestion.business_category}</span>
                        </div>
                        <div class="flex space-x-2">
                            <button onclick="makeDecision('medium_{i}', 'accept', '{suggestion.display_name}')" 
                                    class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 font-medium">
                                ✅ Group as "{suggestion.display_name}"
                            </button>
                            <button onclick="showCustomNaming('medium_{i}')" 
                                    class="bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 font-medium">
                                ✏️ Custom Name
                            </button>
                            <button onclick="makeDecision('medium_{i}', 'reject', '')" 
                                    class="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 font-medium">
                                ❌ Keep Separate
                            </button>
                        </div>
                    </div>
                    
                    <!-- Custom Naming (Hidden) -->
                    <div id="custom_medium_{i}" class="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg hidden">
                        <label class="block text-sm font-medium text-gray-700 mb-2">Custom Group Name:</label>
                        <div class="flex space-x-2">
                            <input type="text" class="flex-1 border rounded px-3 py-2" 
                                   placeholder="{suggestion.display_name}" 
                                   id="customName_medium_{i}">
                            <button onclick="acceptCustomName('medium_{i}')" 
                                    class="bg-yellow-600 text-white px-4 py-2 rounded hover:bg-yellow-700">
                                Save
                            </button>
                        </div>
                    </div>
                </div>'''
    
    html_content += '''
            </div>
        </div>

        <!-- Summary & Next Steps -->
        <div class="bg-white rounded-lg shadow-sm p-6">
            <h3 class="text-lg font-semibold mb-4">🎯 Mapping Summary</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div class="text-center p-4 bg-green-50 rounded-lg">
                    <div class="text-2xl font-bold text-green-600" id="acceptedCount">0</div>
                    <div class="text-sm text-gray-600">Accepted Groups</div>
                </div>
                <div class="text-center p-4 bg-yellow-50 rounded-lg">
                    <div class="text-2xl font-bold text-yellow-600" id="customCount">0</div>
                    <div class="text-sm text-gray-600">Custom Names</div>
                </div>
                <div class="text-center p-4 bg-red-50 rounded-lg">
                    <div class="text-2xl font-bold text-red-600" id="rejectedCount">0</div>
                    <div class="text-sm text-gray-600">Kept Separate</div>
                </div>
            </div>
            
            <div class="border-t pt-4">
                <h4 class="font-medium text-gray-700 mb-2">Next Steps:</h4>
                <ol class="list-decimal list-inside text-sm text-gray-600 space-y-1">
                    <li>Review and approve grouping suggestions above</li>
                    <li>Create custom names for business-specific groups</li>
                    <li>Save mappings to create meaningful business entities</li>
                    <li>Proceed to Phase 2: Business Entity Analysis</li>
                </ol>
            </div>
        </div>
    </div>

    <script>
        let decisions = {{}};
        let decisionCount = 0;
        
        function makeDecision(cardId, decision, groupName) {{
            const card = document.getElementById(cardId);
            
            // Remove existing decision classes
            card.classList.remove('accepted', 'rejected', 'custom');
            
            // Add new decision class
            if (decision === 'accept') {{
                card.classList.add('accepted');
                decisions[cardId] = {{decision: 'accept', groupName: groupName}};
            }} else if (decision === 'reject') {{
                card.classList.add('rejected');
                decisions[cardId] = {{decision: 'reject', groupName: ''}};
            }}
            
            updateCounts();
            console.log(`Decision: ${{cardId}} = ${{decision}} (${{groupName}})`);
        }}
        
        function showCustomNaming(cardId) {{
            const customDiv = document.getElementById(`custom_${{cardId}}`);
            customDiv.classList.remove('hidden');
        }}
        
        function acceptCustomName(cardId) {{
            const customNameInput = document.getElementById(`customName_${{cardId}}`);
            const customName = customNameInput.value.trim();
            
            if (!customName) {{
                alert('Please enter a custom group name');
                return;
            }}
            
            const card = document.getElementById(cardId);
            card.classList.remove('accepted', 'rejected');
            card.classList.add('custom');
            
            decisions[cardId] = {{decision: 'custom', groupName: customName}};
            
            // Hide custom naming div
            const customDiv = document.getElementById(`custom_${{cardId}}`);
            customDiv.classList.add('hidden');
            
            updateCounts();
            console.log(`Custom decision: ${{cardId}} = ${{customName}}`);
        }}
        
        function acceptAllHigh() {{
            const highCards = document.querySelectorAll('[id^="high_"]');
            highCards.forEach(card => {{
                if (!decisions[card.id]) {{
                    const groupName = card.querySelector('h3').textContent;
                    makeDecision(card.id, 'accept', groupName);
                }}
            }});
        }}
        
        function updateCounts() {{
            decisionCount = Object.keys(decisions).length;
            document.getElementById('decisionsCount').textContent = decisionCount;
            
            let accepted = 0, custom = 0, rejected = 0;
            Object.values(decisions).forEach(d => {{
                if (d.decision === 'accept') accepted++;
                else if (d.decision === 'custom') custom++;
                else if (d.decision === 'reject') rejected++;
            }});
            
            document.getElementById('acceptedCount').textContent = accepted;
            document.getElementById('customCount').textContent = custom;
            document.getElementById('rejectedCount').textContent = rejected;
            
            // Enable Phase 2 button if decisions made
            const phase2Button = document.getElementById('phase2Button');
            if (decisionCount >= {len(suggestions['high_confidence'])}) {{
                phase2Button.disabled = false;
                phase2Button.classList.remove('opacity-50');
            }}
        }}
        
        function proceedToPhase2() {{
            if (Object.keys(decisions).length < {len(suggestions['high_confidence'])}) {{
                alert('Please make decisions on high confidence suggestions before proceeding');
                return;
            }}
            
            console.log('All mapping decisions:', decisions);
            alert(`Phase 1 Complete! Ready to save ${{Object.keys(decisions).length}} mapping decisions and proceed to Phase 2: Business Entity Analysis`);
            
            // In production, this would save to database and redirect
        }}
        
        // Initialize
        console.log('Vendor Mapping Interface loaded');
        console.log('Make grouping decisions to create meaningful business entities');
    </script>
</body>
</html>'''
    
    # Save interface
    output_file = '/Users/jeffreydebolt/Documents/cfo_forecast_refactored/vendor_mapping_interface.html'
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Vendor Mapping Interface created: {output_file}")
    return output_file

if __name__ == "__main__":
    print("🗺️ CREATING VENDOR MAPPING INTERFACE")
    print("=" * 80)
    
    interface_file = create_vendor_mapping_interface('spyguy')
    
    print(f"\n🎉 SUCCESS!")
    print(f"📊 Phase 1 mapping interface ready")
    print(f"🎯 Review grouping suggestions and create business entities")
    print(f"⏭️ Then proceed to Phase 2: Business Entity Analysis")