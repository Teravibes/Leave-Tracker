import pytest
from datetime import date
from django.urls import reverse
from django.contrib.auth.models import User
from LeaveTracker.models import Employee, HolidayRequest, PublicHoliday

@pytest.mark.django_db
def test_submit_normal_holiday_request(client):
    # Create user and log in
    user = User.objects.create_user(username="user1", password="testpass", email="user1@example.com")
    client.login(username="user1", password="testpass")

    # Create Employee with available holidays
    employee = Employee.objects.create(user=user, available_holidays=10)

    # Add a public holiday to test exclusion
    PublicHoliday.objects.create(country_code="NL", date=date(2025, 7, 21))  # Monday

    # Prepare JSON payload (Sunday to Wednesday)
    payload = {
        "start_date": "2025-07-20",  # Sunday
        "end_date": "2025-07-23",    # Wednesday
        "is_special": False
    }

    # Submit request via POST
    url = reverse("submit_holiday_request")
    response = client.post(url, payload, content_type="application/json")

    # Assert response success
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    # Validate created HolidayRequest
    holiday = HolidayRequest.objects.get(employee=employee)
    assert holiday.days_taken == 2  # Excludes Sunday and public holiday on Monday
    assert holiday.start_date.isoformat() == "2025-07-20"
    assert holiday.end_date.isoformat() == "2025-07-23"

    # Employee's holiday balance reduced
    employee.refresh_from_db()
    assert employee.available_holidays == 8

@pytest.mark.django_db
def test_submit_request_with_insufficient_holidays(client):
    user = User.objects.create_user(username="user2", password="testpass", email="user2@example.com")
    client.login(username="user2", password="testpass")
    employee = Employee.objects.create(user=user, available_holidays=1)  # not enough for 3 days

    payload = {
        "start_date": "2025-07-22",  # Tue
        "end_date": "2025-07-24",    # Thu → 3 working days
        "is_special": False
    }

    url = reverse("submit_holiday_request")
    response = client.post(url, payload, content_type="application/json")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "enough available holidays" in data["message"]
    
from LeaveTracker.models import SpecialHolidayTypes, SpecialHolidayUsage

@pytest.mark.django_db
def test_submit_special_holiday_creates_usage_record(client):
    user = User.objects.create_user(username="user3", password="testpass", email="user3@example.com")
    client.login(username="user3", password="testpass")
    employee = Employee.objects.create(user=user, available_holidays=5)

    special_type = SpecialHolidayTypes.objects.create(
        name="Marriage Leave",
        max_days=5  # Or any valid positive integer
    )

    payload = {
        "start_date": "2025-07-22",
        "end_date": "2025-07-23",  # 2 days
        "is_special": True,
        "special_type_id": special_type.id,
        "year": 2025
    }

    url = reverse("submit_holiday_request")
    response = client.post(url, payload, content_type="application/json")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    # SpecialHolidayUsage should be created
    usage = SpecialHolidayUsage.objects.get(employee=employee, holiday_type=special_type, year=2025)
    assert usage.days_used == 2

    # Regular holiday balance should remain unchanged
    employee.refresh_from_db()
    assert employee.available_holidays == 5
    
    
@pytest.mark.django_db
def test_submit_invalid_date_range(client):
    user = User.objects.create_user(username="user4", password="testpass", email="user4@example.com")
    client.login(username="user4", password="testpass")
    Employee.objects.create(user=user, available_holidays=5)

    payload = {
        "start_date": "2025-07-25",
        "end_date": "2025-07-22",  # Invalid: end before start
        "is_special": False
    }

    url = reverse("submit_holiday_request")
    response = client.post(url, payload, content_type="application/json")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "error"
    assert "Invalid date range" in data["message"] or "after start date" in data["message"]


