from openai import AzureOpenAI, OpenAI
from django.conf import settings


class WhisperIntegration(object):
    def __init__(self):
        if settings.OPENAI_USE_AZURE:
            self.openai = AzureOpenAI(
                api_key=settings.OPENAI_AZURE_API_KEY,
                api_version=settings.OPENAI_AZURE_API_VERSION,
                azure_endpoint=settings.OPENAI_AZURE_ENDPOINT,
            )
            self.model = settings.OPENAI_AZURE_WHISPER_DEPLOYMENT_NAME
        else:
            self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_WHISPER_MODEL
    
    def get_transcription(self, audio_file):
        transcription = self.openai.audio.transcriptions.create(
            model=self.model, 
            file=audio_file
        )
        return transcription.text
