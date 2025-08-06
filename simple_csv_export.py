#!/usr/bin/env python3
"""
Simple CSV export of the 13-week forecast data.
"""

import csv
from datetime import datetime
import subprocess
import re

def export_forecast_to_csv():
    """Export the forecast output to CSV format."""
    
    print("🔄 Generating forecast data...")
    
    # Run the forecast and capture output
    result = subprocess.run(
        ['python3', 'run_calendar_forecast.py', '--client', 'bestself', '--weeks', '13', '--show-events'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Error running forecast: {result.stderr}")
        return
    
    output = result.stdout
    
    # Parse the output to extract forecast data
    lines = output.split('\n')
    
    # Find the forecast table
    table_start = None
    table_data = []
    
    for i, line in enumerate(lines):
        if 'Week   Period' in line and 'Deposits' in line:
            table_start = i + 2  # Skip header and separator line
            break
    
    if table_start:
        for i in range(table_start, len(lines)):
            line = lines[i]
            if line.startswith('W') and '$' in line:
                # Parse week data
                parts = line.split()
                if len(parts) >= 7:
                    week = parts[0]
                    period = f"{parts[1]} {parts[2]} {parts[3]}"
                    deposits = parts[4].replace('$', '').replace(',', '')
                    withdrawals = parts[5].replace('$', '').replace(',', '')
                    net = parts[6].replace('$', '').replace(',', '')
                    events = parts[7] if len(parts) > 7 else '0'
                    balance = parts[8].replace('$', '').replace(',', '') if len(parts) > 8 else '0'
                    
                    table_data.append([week, period, deposits, withdrawals, net, events, balance])
            elif line.startswith('TOTAL'):
                break
    
    # Create CSV filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    csv_filename = f'bestself_13week_forecast_{timestamp}.csv'
    
    # Write to CSV
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Header
        writer.writerow(['Week', 'Period', 'Deposits', 'Withdrawals', 'Net', 'Events', 'Balance'])
        
        # Data
        for row in table_data:
            writer.writerow(row)
    
    print(f"✅ Forecast exported to: {csv_filename}")
    print(f"📊 Exported {len(table_data)} weeks of data")
    
    # Also extract vendor breakdown if available
    vendor_data = []
    in_vendor_section = False
    current_week = None
    
    for line in lines:
        if 'Vendor Breakdown' in line:
            in_vendor_section = True
            continue
        
        if in_vendor_section:
            if line.startswith('Week'):
                current_week = line.split('(')[0].strip()
            elif '$' in line and '  ' in line:
                # Parse vendor line
                vendor_line = line.strip()
                if vendor_line:
                    parts = vendor_line.rsplit('$', 1)
                    if len(parts) == 2:
                        vendor = parts[0].strip()
                        amount = parts[1].strip().replace(',', '')
                        vendor_data.append([current_week, vendor, amount])
    
    if vendor_data:
        vendor_filename = f'bestself_vendor_breakdown_{timestamp}.csv'
        with open(vendor_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Week', 'Vendor', 'Amount'])
            for row in vendor_data:
                writer.writerow(row)
        
        print(f"✅ Vendor breakdown exported to: {vendor_filename}")
    
    return csv_filename

if __name__ == "__main__":
    export_forecast_to_csv()