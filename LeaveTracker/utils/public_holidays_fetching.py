import datetime
import requests
from LeaveTracker.models import PublicHoliday

def fetch_and_store_holidays(api_key, country_code, year):
    url = "https://calendarific.com/api/v2/holidays"
    params = {
        "api_key": api_key,
        "country": country_code,
        "year": year,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    if 'response' not in data or 'holidays' not in data['response']:
        raise ValueError("Invalid response from API")

    created_count = 0

    for holiday in data['response']['holidays']:
        name = holiday['name']
        date_str = holiday['date']['iso']
        try:
            date = datetime.datetime.fromisoformat(date_str).date()

            # Include country_code in the get_or_create
            _, created = PublicHoliday.objects.get_or_create(
                name=name,
                date=date,
                country_code=country_code
            )

            if created:
                created_count += 1
        except Exception:
            continue

    return created_count

