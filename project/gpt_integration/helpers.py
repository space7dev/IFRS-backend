import re

import tiktoken

from django.conf import settings

from .models import SystemPrompt


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613"):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model in {
        "gpt-35-turbo",  # Azure model
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
    }:
        tokens_per_message = 3
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_message = 4
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" in model:
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4" in model:
        return num_tokens_from_messages(messages, model="gpt-4-0613")
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
        )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def build_messages(chat, prompt):
    """For chat completion"""
    if settings.OPENAI_USE_AZURE:
        model = settings.OPENAI_AZURE_MODEL
    else:
        model = settings.OPENAI_DEFAULT_MODEL
    model_max_tokens = settings.GPT_MODEL_MAX_TOKENS
    max_tokens_per_response = settings.GPT_MAX_TOKENS_PER_RESPONSE

    try:
        system_prompt = SystemPrompt.objects.filter(
            is_active=True).first().prompt
    except:
        system_prompt = "You are a helpful assistant."

    base_messages = [{"role": "system", "content": system_prompt}]
    chat_messages = []

    user_prompt = {"role": "user", "content": str(prompt)}

    user_prompt_tokens = num_tokens_from_messages([user_prompt], model)
    system_prompt_tokens = num_tokens_from_messages(base_messages, model)

    tokens_limit = model_max_tokens - max_tokens_per_response - \
        user_prompt_tokens - system_prompt_tokens
    tokens_used = 0

    for message in chat.messages.all().order_by("-created_on"):
        old_prompt = {"role": "user", "content": message.prompt}
        old_bot_response = {"role": "assistant",
                            "content": message.bot_response}
        message_tokens = num_tokens_from_messages(
            [old_prompt, old_bot_response], model)

        if tokens_used + message_tokens > tokens_limit:
            break

        tokens_used += message_tokens
        chat_messages.extend([old_prompt, old_bot_response])

    messages = base_messages + chat_messages + [user_prompt]

    return messages
