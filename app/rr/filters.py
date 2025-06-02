import django_filters
from django.db import models
from django_filters import rest_framework as filters
from django.utils import timezone
from .models import Checklist


class ChecklistFilter(filters.FilterSet):
    created_at = filters.DateFromToRangeFilter()
    score = filters.RangeFilter()
    completed = filters.BooleanFilter()
    today = filters.BooleanFilter(method='filter_today')
    
    class Meta:
        model = Checklist
        fields = ['created_at', 'score', 'completed', 'today']

    def filter_today(self, queryset, name, value):
        if value:
            today = timezone.now().date()

            # Try to get today's checklist
            today_checklist = queryset.filter(created_at__date=today)
            
            if not today_checklist.exists() and self.request:
                # Create a new checklist for today
                today_checklist = Checklist.objects.create(user=self.request.user)
                today_checklist = Checklist.objects.filter(pk=today_checklist.pk)
            
            return today_checklist
        return queryset
