from django.contrib import admin,messages
from django.urls import path
from django.shortcuts import redirect
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group, Permission
from .models import Employee, HolidayRequest,SpecialHolidayTypes,SpecialHolidayUsage, PublicHolidayFetchConfig
from LeaveTracker.utils.public_holidays_fetching import fetch_and_store_holidays
from django.contrib.auth.admin import GroupAdmin
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple



class EmployeeInline(admin.StackedInline):
    model = Employee
    can_delete = False
    verbose_name_plural = 'employee'


class UserAdmin(BaseUserAdmin):
    inlines = (EmployeeInline,)

class PermissionMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name 

EXCLUDED_APPS = ['admin', 'sessions', 'contenttypes']
EXCLUDED_CODENAMES = [
    'add_user', 'change_user', 'delete_user', 'view_user',
    'add_group', 'change_group', 'delete_group', 'view_group',
    'add_permission', 'change_permission', 'delete_permission', 'view_permission',
]

class CustomUserAdmin(UserAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'user_permissions' in form.base_fields:
            form.base_fields['user_permissions'] = PermissionMultipleChoiceField(
                queryset=Permission.objects.exclude(
                    content_type__app_label__in=EXCLUDED_APPS
                ).exclude(
                    codename__in=EXCLUDED_CODENAMES
                ),
                widget=FilteredSelectMultiple("permissions", is_stacked=False),
                required=False
            )
        return form

class CustomGroupAdmin(GroupAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'permissions' in form.base_fields:
            form.base_fields['permissions'] = PermissionMultipleChoiceField(
                queryset=Permission.objects.exclude(
                    content_type__app_label__in=EXCLUDED_APPS
                ).exclude(
                    codename__in=EXCLUDED_CODENAMES
                ),
                widget=FilteredSelectMultiple("permissions", is_stacked=False),
                required=False
            )
        return form

@admin.register(PublicHolidayFetchConfig)
class PublicHolidayFetchConfigAdmin(admin.ModelAdmin):
    list_display = ('country_code', 'year', 'created_at')
    change_form_template = "admin/holiday_config_change_form.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/run/',
                self.admin_site.admin_view(self.run_fetch),
                name='holidayfetchconfig-run',
            ),
        ]
        return custom_urls + urls

    def run_fetch(self, request, object_id):
        config = self.get_object(request, object_id)
        if not config:
            self.message_user(request, "Configuration not found.", level=messages.ERROR)
            return redirect("..")

        try:
            count = fetch_and_store_holidays(config.api_key, config.country_code, config.year)
            self.message_user(
                request,
                f"Successfully imported {count} holidays for {config.country_code} - {config.year}",
                level=messages.SUCCESS,
            )
        except Exception as e:
            self.message_user(request, f"Error during fetch: {e}", level=messages.ERROR)

        return redirect(f"../")

def response_add(self, request, obj, post_url_continue=None):

    return redirect(f'../{obj.pk}/change/')

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)
admin.site.register(HolidayRequest)
admin.site.register(Employee)
admin.site.register(SpecialHolidayTypes)
admin.site.register(SpecialHolidayUsage)
