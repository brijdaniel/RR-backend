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
            return queryset.filter(created_at__date=timezone.now().date())
        return queryset
