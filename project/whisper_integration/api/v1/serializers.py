from rest_framework import serializers


class GetTranscriptionSerializer(serializers.Serializer):
    file = serializers.FileField(
        max_length=None, allow_empty_file=False, use_url=True
    )
