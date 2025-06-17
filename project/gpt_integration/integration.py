import json

from openai import AzureOpenAI, OpenAI

from django.conf import settings

from gpt_integration.models import ChatMessage


class GptIntegration(object):
    def __init__(self):
        if settings.OPENAI_USE_AZURE:
            self.openai = AzureOpenAI(
                api_key=settings.OPENAI_AZURE_API_KEY,
                api_version=settings.OPENAI_AZURE_API_VERSION,
                azure_endpoint=settings.OPENAI_AZURE_ENDPOINT,
            )
            self.model = settings.OPENAI_AZURE_DEPLOYMENT_NAME
        else:
            self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_DEFAULT_MODEL
        self.max_tokens = settings.GPT_MAX_TOKENS_PER_RESPONSE
        self.temperature = settings.GPT_TEMPERATURE

    def get_chat_completion(self, messages=""):
        """
        prompt format:
            [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Who won the world series in 2020?"},
                {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
                {"role": "user", "content": "Where was it played?"}
            ]
        """
        chat_completion = self.openai.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=messages,
        )
        response = chat_completion.choices[0].message.content
        return response

    def get_chat_completion_stream(self, chat, prompt, messages=""):
        full_response = ""
        for chunk in self.openai.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=messages,
            stream=True,
        ):
            chatcompletion_delta = chunk["choices"][0].get("delta", {})
            chatcompletion_finish_reason = chunk["choices"][0].get(
                "finish_reason", {})
            if chatcompletion_finish_reason == "stop":
                # Have to create ChatMessage here, no access to data later on
                ChatMessage.objects.create(
                    chat=chat,
                    prompt=prompt,
                    bot_response=full_response
                )
            else:
                full_response += chatcompletion_delta.get("content")

            data = json.dumps(dict(chatcompletion_delta))
            yield f'data: {data}\n\n'
