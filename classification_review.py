import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
from supabase_client import supabase
from openai_client import openai_client

def run_classification_review():
    # 1. Fetch low confidence classifications
    vendors = supabase.table('vendors') \
        .select('display_name,forecast_frequency,forecast_confidence,forecast_amount') \
        .eq('client_id', 'spyguy') \
        .lt('forecast_confidence', 0.7) \
        .execute().data

    if not vendors:
        print("No low-confidence vendors found for review.")
        return

    print(f"Reviewing {len(vendors)} low-confidence vendors...")

    # 2. Ask OpenAI to review
    prompt = f"""Below are vendors with low confidence buckets.  
For each, review the `forecast_frequency` (monthly, weekly, irregular) and confidence score.
If any buckets should be changed, reply with a JSON array containing only the ones that need changes in this format: [{{"display_name":"…", "suggested_bucket":"…"}}].
If all buckets look correct, reply with an empty array [].

Data:
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
        if suggestion.get('suggested_bucket'):
            print(f"\nUpdating {suggestion['display_name']} → {suggestion['suggested_bucket']}")
            supabase.table('vendors') \
                .update({
                    'forecast_frequency': suggestion['suggested_bucket'],
                    'review_needed': True
                }) \
                .eq('display_name', suggestion['display_name']) \
                .eq('client_id', 'spyguy') \
                .execute()
            updated += 1

    print(f"\nApplied {updated} bucket corrections.")

if __name__ == '__main__':
    run_classification_review() 