from datetime import timedelta, datetime



def total_days_for_queryset(queryset, public_holidays):
    return sum([
        count_non_weekend_and_non_holiday_days(hr.start_date, hr.end_date, public_holidays)
        for hr in queryset
    ])
    
def count_non_weekend_and_non_holiday_days(start_date, end_date, holidays):
    holidays = set(holidays)  # ensure fast lookup
    count = 0
    day = start_date
    while day <= end_date:
        if day.weekday() < 5 and day not in holidays:
            count += 1
        day += timedelta(days=1)
    return count

def get_month_range(year, month):
    start = datetime(year, month, 1).date()
    if month == 12:
        end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        end = datetime(year, month + 1, 1).date() - timedelta(days=1)
    return start, end
