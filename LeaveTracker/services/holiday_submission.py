from datetime import date
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from LeaveTracker.models import (
    HolidayRequest,
    Employee,
    SpecialHolidayTypes,
    SpecialHolidayUsage,
    PublicHoliday,
)
from LeaveTracker.utils.date_utils import count_non_weekend_and_non_holiday_days

@transaction.atomic
def process_holiday_submission(user, data):
    start_date = date.fromisoformat(data["start_date"])
    end_date = date.fromisoformat(data["end_date"])

    if start_date > end_date:
        return {
            "status": "error",
            "message": "End date must be after start date."
        }

    is_special = data.get("is_special", False)
    special_type_id = data.get("special_type_id")
    group_names_str = ",".join(user.groups.values_list("name", flat=True))

    employee = Employee.objects.select_for_update().get(user=user)
    country_code = employee.country_code

    public_holidays = set(PublicHoliday.objects.filter(
        country_code=country_code
    ).values_list('date', flat=True))

    days_requested = count_non_weekend_and_non_holiday_days(
        start_date, end_date, public_holidays
    )

    if days_requested == 0:
        return {
            "status": "error",
            "message": "You have not selected any valid days to take off. Please select weekdays that are not holidays."
        }

    holiday_request = HolidayRequest(
        employee=employee,
        days_taken=days_requested,
        start_date=start_date,
        end_date=end_date,
        status="pending",
        user_group=group_names_str,
        is_special=is_special
    )

    if is_special and special_type_id:
        special_type = SpecialHolidayTypes.objects.get(id=special_type_id)
        holiday_request.special_type = special_type
        year = data.get("year", timezone.now().year)

        usage, created = SpecialHolidayUsage.objects.get_or_create(
            employee=employee,
            holiday_type=special_type,
            year=year,
            defaults={"days_used": 0}
        )

        if usage.days_used + days_requested > usage.holiday_type.max_days:
            return {
                "status": "error",
                "message": f"You've exceeded your allowed {usage.holiday_type.name} days."
            }

        usage.days_used += days_requested
        usage.save()

    else:
        if employee.available_holidays < days_requested:
            return {
                "status": "error",
                "message": "You don't have enough available holidays."
            }

    # Let model validation run
    try:
        holiday_request.clean()
    except ValidationError as e:
        return {"status": "error", "message": str(e)}

    # Save user and request
    if not is_special:
        employee.available_holidays -= days_requested
        employee.save()

    holiday_request.save()
    return {"status": "success"}