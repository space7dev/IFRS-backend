from django_filters import rest_framework as filters

from gpt_integration.models import Chat


class ChatFilter(filters.FilterSet):
    date = filters.DateFromToRangeFilter(field_name="modified_on")

    class Meta:
        model = Chat
        fields = ['modified_on']
