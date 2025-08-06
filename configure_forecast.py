from collections import Counter
from datetime import datetime, timedelta, UTC
import statistics

LOOKBACK_DAYS = 180
MONTHLY_MIN_MONTHS = 6      # keep your existing "6" threshold here
IRREGULAR_MIN_OCCURRENCES = 2

def parse_date(date_str):
    """Parse date string to UTC datetime."""
    dt = datetime.fromisoformat(date_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt

def analyze_display_history(txns):
    """
    txns: list of dicts with 'transaction_date' (ISO string) and 'amount'
    Returns dict with:
      - months_with_activity (set of YYYY-MM)
      - weeks_with_activity (set of YYYY-Www)
      - day_of_month_counts (Counter)
      - weekday_counts (Counter of ISO weekday 1–7)
      - amounts (list of float)
    """
    months = set()
    weeks = set()
    dom = Counter()
    dow = Counter()
    amounts = []

    for t in txns:
        dt = parse_date(t['transaction_date'])
        amounts.append(t['amount'])
        months.add(f"{dt.year}-{dt.month:02d}")
        iso_week = dt.isocalendar()[1]
        weeks.add(f"{dt.year}-W{iso_week:02d}")
        dom[dt.day] += 1
        dow[dt.isoweekday()] += 1

    return {
        'months': months,
        'weeks': weeks,
        'dom': dom,
        'dow': dow,
        'amounts': amounts
    }

def classify_and_configure(display_name, txns, supabase):
    stats = analyze_display_history(txns)
    num_months = len(stats['months'])
    num_weeks = len(stats['weeks'])

    # 1) Monthly vs Irregular
    if num_months >= MONTHLY_MIN_MONTHS:
        freq = 'monthly'
        # modal day-of-month
        forecast_day = stats['dom'].most_common(1)[0][0]
        confidence = num_months / MONTHLY_MIN_MONTHS
    # (we leave weekly cutoff as-is, e.g. total txns >= 4)
    elif len(txns) >= 4:
        freq = 'weekly'
        # modal ISO weekday (1=Mon … 7=Sun)
        forecast_day = stats['dow'].most_common(1)[0][0]
        # confidence = weeks covered / expected weeks
        expected_weeks = LOOKBACK_DAYS / 7
        confidence = num_weeks / expected_weeks
    else:
        freq = 'irregular'
        # if at least IRREGULAR_MIN_OCCURRENCES, capture a modal day
        if sum(stats['dom'].values()) >= IRREGULAR_MIN_OCCURRENCES:
            forecast_day = stats['dom'].most_common(1)[0][0]
            confidence = stats['dom'][forecast_day] / sum(stats['dom'].values())
        else:
            forecast_day = None
            confidence = 0

    # amount: trailing 90-day average
    trail = datetime.now(UTC) - timedelta(days=90)
    recent = [t['amount'] for t in txns if parse_date(t['transaction_date']) >= trail]
    forecast_amount = round(statistics.mean(recent), 2) if recent else 0

    print(f"  Frequency: {freq}, Day: {forecast_day}, Amount: {forecast_amount}")
    print(f"  Confidence: {confidence:.2f}, Months: {num_months}, Weeks: {num_weeks}")

    # persist to DB
    supabase.table('vendors').update({
        'forecast_frequency': freq,
        'forecast_day': forecast_day,
        'forecast_amount': forecast_amount,
        'forecast_confidence': round(confidence, 2)
    }).eq('display_name', display_name).eq('client_id', 'spyguy').execute() 