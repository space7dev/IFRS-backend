from django.urls import include, path

from .views import GetTranscriptionAPIView


api_patterns = [
    path("get-transcription/",
         GetTranscriptionAPIView.as_view(), name="get_transcription"),

]