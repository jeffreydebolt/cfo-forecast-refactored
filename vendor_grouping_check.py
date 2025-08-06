import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
from supabase_client import supabase
from openai_client import openai_client

def run_vendor_grouping_check():
    # 1. Fetch new groups
    vendors = supabase.table('vendors') \
        .select('vendor_name,display_name,group_locked') \
        .eq('client_id', 'spyguy') \
        .eq('group_locked', False) \
        .execute().data

    if not vendors:
        print("No unlocked vendors found for review.")
        return

    print(f"Reviewing {len(vendors)} unlocked vendors...")

    # 2. Ask OpenAI to review
    prompt = f"""You're auditing vendor-name → display_name mappings. 
For each entry below, does the display_name look correct? 
If any are wrong, reply with a JSON array containing only the incorrect mappings in this format: [{{"vendor_name": "...", "suggested_display_name": "..."}}].
If all mappings look correct, reply with an empty array [].

Vendors:
{json.dumps(vendors, indent=2)}"""

    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    
    content = response.choices[0].message.content.strip()
    print("\nOpenAI Response:", content)
    
    try:
        suggestions = json.loads(content)
        if not isinstance(suggestions, list):
            print("Error: Expected JSON array response")
            return
    except json.JSONDecodeError:
        print("Error: Invalid JSON response from OpenAI")
        return
    
    # 3. Apply suggestions
    updated = 0
    for suggestion in suggestions:
        if suggestion.get('suggested_display_name'):
            print(f"\nUpdating {suggestion['vendor_name']} → {suggestion['suggested_display_name']}")
            supabase.table('vendors') \
                .update({
                    'display_name': suggestion['suggested_display_name'],
                    'review_needed': True
                }) \
                .eq('vendor_name', suggestion['vendor_name']) \
                .eq('client_id', 'spyguy') \
                .execute()
            updated += 1

    print(f"\nFlagged {updated} vendors for review.")

if __name__ == '__main__':
    run_vendor_grouping_check() 