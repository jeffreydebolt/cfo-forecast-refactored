#!/usr/bin/env python3
"""
Simple Vendor Grouping Interface
User creates their own groups by dragging vendors together
"""

import sys
sys.path.append('.')

from supabase_client import supabase
from datetime import datetime, date, timedelta
from collections import defaultdict
import json

def create_simple_grouping_interface(client_id: str = 'spyguy'):
    """Create simple interface where users create their own groups"""
    
    # Get regular vendors with transaction info
    result = supabase.table('transactions').select('vendor_name, amount').eq('client_id', client_id).execute()
    transactions = result.data
    
    # Count transactions per vendor
    vendor_stats = defaultdict(lambda: {'count': 0, 'total': 0})
    for txn in transactions:
        vendor_name = txn['vendor_name']
        vendor_stats[vendor_name]['count'] += 1
        vendor_stats[vendor_name]['total'] += abs(float(txn['amount']))
    
    # Filter for regular vendors (2+ transactions)
    regular_vendors = []
    for vendor_name, stats in vendor_stats.items():
        if stats['count'] >= 2:
            regular_vendors.append({
                'name': vendor_name,
                'count': stats['count'],
                'total': stats['total'],
                'monthly_avg': stats['total'] / 12  # Rough estimate
            })
    
    # Sort by volume
    regular_vendors.sort(key=lambda x: x['total'], reverse=True)
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🗂️ Simple Vendor Grouping</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .vendor-item {{
            cursor: move;
            transition: all 0.2s ease;
        }}
        .vendor-item:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        .vendor-item.selected {{
            border-color: #3B82F6;
            background-color: #EFF6FF;
        }}
        .group-area {{
            min-height: 100px;
            border: 2px dashed #D1D5DB;
            transition: all 0.2s ease;
        }}
        .group-area.drag-over {{
            border-color: #3B82F6;
            background-color: #EFF6FF;
        }}
        .group-area.has-vendors {{
            border-style: solid;
            border-color: #10B981;
            background-color: #F0FDF4;
        }}
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    
    <header class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-4 py-4">
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-2xl font-bold text-gray-900">🗂️ Simple Vendor Grouping</h1>
                    <p class="text-sm text-gray-600">Click vendors to select, then group them together • {len(regular_vendors)} vendors</p>
                </div>
                <button onclick="saveGroups()" 
                        class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 font-medium">
                    💾 Save Groups & Continue
                </button>
            </div>
        </div>
    </header>

    <div class="max-w-7xl mx-auto px-4 py-6">
        
        <!-- Instructions -->
        <div class="bg-blue-50 rounded-lg p-4 mb-6">
            <h2 class="font-semibold text-blue-900 mb-2">How to Group Vendors:</h2>
            <ol class="text-blue-800 text-sm space-y-1">
                <li>1. Click vendors to select them (hold Ctrl/Cmd for multiple)</li>
                <li>2. Click "Group Selected" to create a new group</li>
                <li>3. Name your group (e.g., "Amex Payments", "State Taxes")</li>
                <li>4. Repeat as needed, then save</li>
            </ol>
        </div>

        <!-- Selection Controls -->
        <div class="bg-white rounded-lg p-4 mb-6 flex items-center justify-between">
            <div>
                <span id="selectedCount">0</span> vendors selected
            </div>
            <div class="space-x-2">
                <button onclick="selectAll()" 
                        class="bg-gray-100 text-gray-700 px-3 py-1 rounded hover:bg-gray-200 text-sm">
                    Select All
                </button>
                <button onclick="clearSelection()" 
                        class="bg-gray-100 text-gray-700 px-3 py-1 rounded hover:bg-gray-200 text-sm">
                    Clear Selection
                </button>
                <button onclick="groupSelected()" 
                        class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 font-medium"
                        id="groupButton" disabled>
                    🗂️ Group Selected
                </button>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Left: Available Vendors -->
            <div>
                <h2 class="text-lg font-semibold mb-4">📋 Available Vendors</h2>
                <div class="space-y-2" id="vendorList">'''
    
    # Generate vendor items
    for i, vendor in enumerate(regular_vendors):
        html_content += f'''
                    <div class="vendor-item bg-white rounded-lg p-3 border cursor-pointer" 
                         onclick="toggleVendor('{vendor['name']}')" 
                         id="vendor_{i}">
                        <div class="flex justify-between items-center">
                            <div>
                                <div class="font-medium text-gray-900">{vendor['name']}</div>
                                <div class="text-sm text-gray-500">{vendor['count']} transactions</div>
                            </div>
                            <div class="text-right">
                                <div class="font-medium text-gray-900">${vendor['total']:,.0f}</div>
                                <div class="text-sm text-gray-500">${vendor['monthly_avg']:,.0f}/mo</div>
                            </div>
                        </div>
                    </div>'''
    
    html_content += '''
                </div>
            </div>

            <!-- Right: Created Groups -->
            <div>
                <h2 class="text-lg font-semibold mb-4">🗂️ Your Groups</h2>
                <div id="groupsList">
                    <div class="text-gray-500 text-center py-8" id="emptyState">
                        No groups created yet.<br>
                        Select vendors and click "Group Selected" to start.
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let selectedVendors = new Set();
        let groups = {};
        let groupCounter = 0;
        
        function toggleVendor(vendorName) {
            const element = document.querySelector(`[onclick="toggleVendor('${vendorName.replace(/'/g, "\\'")}')"]`);
            
            if (selectedVendors.has(vendorName)) {
                selectedVendors.delete(vendorName);
                element.classList.remove('selected');
            } else {
                selectedVendors.add(vendorName);
                element.classList.add('selected');
            }
            
            updateSelectionUI();
        }
        
        function selectAll() {
            const vendors = document.querySelectorAll('.vendor-item');
            vendors.forEach(vendor => {
                const vendorName = vendor.querySelector('.font-medium').textContent;
                selectedVendors.add(vendorName);
                vendor.classList.add('selected');
            });
            updateSelectionUI();
        }
        
        function clearSelection() {
            selectedVendors.clear();
            document.querySelectorAll('.vendor-item').forEach(item => {
                item.classList.remove('selected');
            });
            updateSelectionUI();
        }
        
        function updateSelectionUI() {
            document.getElementById('selectedCount').textContent = selectedVendors.size;
            document.getElementById('groupButton').disabled = selectedVendors.size === 0;
        }
        
        function groupSelected() {
            if (selectedVendors.size === 0) return;
            
            const groupName = prompt(`Enter name for group with ${selectedVendors.size} vendors:`);
            if (!groupName) return;
            
            // Create group
            groupCounter++;
            const groupId = `group_${groupCounter}`;
            groups[groupId] = {
                name: groupName,
                vendors: Array.from(selectedVendors)
            };
            
            // Remove vendors from available list
            selectedVendors.forEach(vendorName => {
                const element = document.querySelector(`[onclick="toggleVendor('${vendorName.replace(/'/g, "\\'")}')"]`);
                if (element) element.remove();
            });
            
            // Add group to groups list
            addGroupToUI(groupId, groupName, Array.from(selectedVendors));
            
            // Clear selection
            selectedVendors.clear();
            updateSelectionUI();
            updateGroupsUI();
        }
        
        function addGroupToUI(groupId, groupName, vendors) {
            const groupsList = document.getElementById('groupsList');
            const emptyState = document.getElementById('emptyState');
            
            if (emptyState) emptyState.remove();
            
            const groupDiv = document.createElement('div');
            groupDiv.className = 'bg-green-50 rounded-lg p-4 mb-4 border border-green-200';
            groupDiv.id = groupId;
            
            let vendorsList = vendors.map(v => `<div class="text-sm text-gray-600">• ${v}</div>`).join('');
            
            groupDiv.innerHTML = `
                <div class="flex justify-between items-start mb-2">
                    <h3 class="font-medium text-green-900">${groupName}</h3>
                    <button onclick="deleteGroup('${groupId}')" 
                            class="text-red-600 hover:text-red-800 text-sm">
                        🗑️ Delete
                    </button>
                </div>
                <div class="text-sm text-green-700 mb-2">${vendors.length} vendors grouped</div>
                <div class="max-h-32 overflow-y-auto">
                    ${vendorsList}
                </div>
            `;
            
            groupsList.appendChild(groupDiv);
        }
        
        function deleteGroup(groupId) {
            if (!confirm('Delete this group? Vendors will return to available list.')) return;
            
            // Return vendors to available list
            const group = groups[groupId];
            group.vendors.forEach(vendorName => {
                // Find original vendor data and re-add to list
                // This is simplified - in production you'd maintain original data
                const vendorDiv = document.createElement('div');
                vendorDiv.className = 'vendor-item bg-white rounded-lg p-3 border cursor-pointer';
                vendorDiv.onclick = () => toggleVendor(vendorName);
                vendorDiv.innerHTML = `
                    <div class="flex justify-between items-center">
                        <div>
                            <div class="font-medium text-gray-900">${vendorName}</div>
                            <div class="text-sm text-gray-500">Restored</div>
                        </div>
                    </div>
                `;
                document.getElementById('vendorList').appendChild(vendorDiv);
            });
            
            // Remove group
            delete groups[groupId];
            document.getElementById(groupId).remove();
            
            updateGroupsUI();
        }
        
        function updateGroupsUI() {
            const groupsList = document.getElementById('groupsList');
            if (Object.keys(groups).length === 0 && !document.getElementById('emptyState')) {
                groupsList.innerHTML = `
                    <div class="text-gray-500 text-center py-8" id="emptyState">
                        No groups created yet.<br>
                        Select vendors and click "Group Selected" to start.
                    </div>
                `;
            }
        }
        
        function saveGroups() {
            console.log('Saving groups:', groups);
            
            // Convert to simple format
            const mappings = {};
            Object.values(groups).forEach(group => {
                mappings[group.name] = group.vendors;
            });
            
            console.log('Final mappings:', mappings);
            alert(`Saved ${Object.keys(groups).length} groups with ${Object.values(groups).reduce((sum, g) => sum + g.vendors.length, 0)} total vendors!`);
            
            // In production, this would save to database and continue to next phase
        }
        
        console.log('Simple grouping interface loaded');
    </script>
</body>
</html>'''
    
    output_file = '/Users/jeffreydebolt/Documents/cfo_forecast_refactored/simple_vendor_grouping.html'
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Simple Vendor Grouping Interface created: {output_file}")
    return output_file

def main():
    """Create simple grouping interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create vendor grouping interface')
    parser.add_argument('--client', required=True, help='Client ID')
    args = parser.parse_args()
    
    print("🗂️ CREATING SIMPLE VENDOR GROUPING INTERFACE")
    print("=" * 80)
    
    interface_file = create_simple_grouping_interface(args.client)
    
    print(f"\n🎉 SUCCESS!")
    print(f"📊 Simple click-to-group interface")
    print(f"🎯 User creates their own groups")
    print(f"💡 No suggestions - complete control")

if __name__ == "__main__":
    main()