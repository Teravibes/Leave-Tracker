from django.apps import AppConfig


class LeaveTrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'LeaveTracker'
    
    def ready(self):
        import LeaveTracker.signals
