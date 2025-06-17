import os, tempfile
from rest_framework import permissions, status
from rest_framework.generics import CreateAPIView
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from whisper_integration.integration import WhisperIntegration
from .serializers import GetTranscriptionSerializer


class GetTranscriptionAPIView(CreateAPIView):
    """ Uploads an audio file and get its transcription """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GetTranscriptionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        transcription = self._get_transcription(serializer)
        response = {
            "transcription": transcription
        }
        return Response(response)

    def _get_transcription(self, serializer):
        file = serializer.validated_data["file"]

        # create temporary path and save file
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, file.name)
        with open(temp_file_path, "wb") as local_file:
            for chunk in file.chunks():
                local_file.write(chunk)
        
        # open temporary file and get transcription
        audio_file = open(temp_file_path, "rb")
        whisper = WhisperIntegration()
        transcription = whisper.get_transcription(audio_file)

        # remove file and directory
        os.remove(temp_file_path)
        os.rmdir(temp_dir)
        return transcription
