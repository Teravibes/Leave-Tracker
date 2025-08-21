from django.db import models
from django.contrib.auth.models import User, Group, Permission
from datetime import date
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

def current_year():
    return date.today().year


class Event(models.Model):
    title = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    
    class Meta:
        default_permissions = ()
        db_table = 'Event'


class SpecialHolidayTypes(models.Model):
    name = models.CharField(max_length=100)
    max_days = models.IntegerField()

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = ()
        verbose_name_plural = "Special holiday types"
        db_table = 'SpecialHolidayTypes'


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    country_code = models.CharField(max_length=2, default='NL')
    annual_holidays = models.IntegerField(default=25)
    available_holidays = models.IntegerField(default=25)
    last_holiday_update = models.DateField(null=True, blank=True)
    last_holiday_year_update = models.IntegerField(default=0)
    manager = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL)
    position = models.CharField(max_length=255, null=True, blank=True)
    special_holidays = models.ManyToManyField(
        SpecialHolidayTypes, through='SpecialHolidayUsage')

    def remaining_holidays(self):
        current_year_holidays = self.annual_holidays
        previous_years_unused = 0

        for request in self.holidayrequest_set.filter(status='approved'):
            if request.end_date.year < current_year():
                days_in_previous_year = (
                    request.end_date - request.start_date).days + 1
                previous_years_unused += days_in_previous_year

        for request in self.holidayrequest_set.filter(status='pending'):
            if request.start_date.year == current_year():
                days_in_current_year = (
                    request.end_date - request.start_date).days + 1
                current_year_holidays -= days_in_current_year

        total_holidays = current_year_holidays + previous_years_unused
        return total_holidays

    def __str__(self):
        return self.user.username
    
    class Meta:
        default_permissions = ()
        db_table = 'Employee'


class SpecialHolidayUsage(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    year = models.IntegerField(default=current_year)
    holiday_type = models.ForeignKey(
        SpecialHolidayTypes, on_delete=models.CASCADE)
    days_used = models.IntegerField(default=0)

    def can_use_more_days(self, days):
        """
        Check if adding more days to current usage will exceed the max limit.

        :param days: The number of days to add to current usage.
        :return: True if it does not exceed the limit, False otherwise.
        """
        new_usage = self.days_used + days
        return new_usage <= self.holiday_type.max_days

    def __str__(self):
        return f"{self.employee.user.username}'s {self.holiday_type.name} in {self.year}"

    class Meta:
        default_permissions = ()
        unique_together = ['employee', 'holiday_type', 'year']
        db_table = 'SpecialHolidayUsage'


class HolidayRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    days_taken = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='pending')
    user_group = models.CharField(max_length=255, blank=True)
    reset = models.BooleanField(default=False)
    deleted = models.DateTimeField(null=True)
    deleted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='holiday_requests_deleted')
    is_special = models.BooleanField(default=False)
    special_type = models.ForeignKey(
        SpecialHolidayTypes, on_delete=models.SET_NULL, null=True)

    # Additional logging fields
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='holiday_requests_approved')
    rejected_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='holiday_requests_rejected')
    approved_at = models.DateTimeField(null=True)
    rejected_at = models.DateTimeField(null=True)

    def __str__(self):
        return f"{self.employee.user.username} - {self.start_date} to {self.end_date}"

    class Meta:
        default_permissions = ()
        permissions = [
            # permission to be able to view things needs to be given to ppl with elevated access
            ("is_manager", "Can manage other users"),
            # permissions for review_requests
            ("review_holiday_requests_all",
             "Can review holiday requests for all employees"),
            ("review_holiday_requests_managed",
             "Can review holiday requests for managed employees"),
            # permissions for approve_request
            ("approve_holiday_request", "Can approve holiday requests"),
            # permissions for reject_request
            ("reject_holiday_request", "Can reject holiday request"),
            # for manage_holidays page permissions
            ("view_all_employees", "Can view all employee holidays (managed page)"),
            ("view_managed_employees", "Can view managed employees (managed page)"),
            # permissions for total_normal_holidays
            ("view_total_normal_holidays_all",
             "Can view total normal holidays for all employees"),
            ("view_total_normal_holidays_managed",
             "Can view total normal holidays for managed employees"),
            # permissions for remaining_normal_holidays
            ("view_remaining_normal_holidays_all",
             "Can view remaining normal holidays for all employees"),
            ("view_remaining_normal_holidays_managed",
             "Can view remaining normal holidays for managed employees"),
            # permissions for filter_holidays
            ("filter_holidays_all", "Can filter holidays for all employees"),
            ("filter_holidays_managed", "Can filter holidays for managed employees"),
            # permissions for delete_holiday // view holidays not delete
            ("delete_holiday", "Can delete holidays"),
            ("view_holiday", "Can view holidays but not delete"),
            # permissions for special_holiday_usage
            ("view_special_holiday_usage_all",
             "Can view special holiday usage for all employees"),
            ("view_special_holiday_usage_managed",
             "Can view special holiday usage for managed employees"),
        ]
        db_table = 'HolidayRequest'
    def clean(self):
        super().clean()

        # Check date logic
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("End date must be after start date.")

        # Optional: Prevent overlapping holiday requests for the same employee
        if self.employee_id:
            overlapping = HolidayRequest.objects.filter(
                employee=self.employee,
                deleted__isnull=True,
                status__in=['pending', 'approved'],
                start_date__lte=self.end_date,
                end_date__gte=self.start_date
            ).exclude(id=self.id)

            if overlapping.exists():
                raise ValidationError("You already have a holiday request that overlaps with this date range.")


@receiver(pre_save, sender=HolidayRequest)
def validate_before_save(sender, instance, **kwargs):
    """
    Run clean method before saving a HolidayRequest instance.
    """
    instance.clean()


class PublicHoliday(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateField()
    country_code = models.CharField(max_length=2)
    db_table = 'PublicHoliday'

    def __str__(self):
        return self.name
    
    class Meta:
        default_permissions = ()
        db_table = 'PublicHoliday'
        unique_together = ('name', 'date', 'country_code')
        

class PublicHolidayFetchConfig(models.Model):
    api_key = models.CharField(max_length=255)
    country_code = models.CharField(max_length=10, default='NL')
    year = models.IntegerField(default=2025)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.country_code} - {self.year}"
    
    class Meta:
        default_permissions = ()
        db_table = 'PublicHolidayConfig'