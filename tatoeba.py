import os
import re
import time
import argparse
import openai
import requests
import json

openai.api_key = os.getenv("OPENAI_API_KEY")

LANGUAGES = {
    "de": "German",
    "es": "Spanish",
    "fr": "French",
    "id": "Indonesian",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "nl": "Dutch",
    "sv": "Swedish",
    "zh": "Chinese",
}


SOURCE_LANGUAGE = "English"
TARGET_LANGUAGE = "German"


def retrieve_sentence(sentence_number: int):
    response = requests.get(f"https://tatoeba.org/en/api_v0/sentence/{sentence_number}")
    js = json.loads(response.text)
    translations = [j for i in js["translations"] for j in i]
    print(translations)


def read_sentence_with_translations(sentence_number: int, source_language: str, target_language: str) -> (str, [(str, str)]):
    response = requests.get(f"https://tatoeba.org/en/api_v0/sentence/{sentence_number}")
    js = json.loads(response.text)
    translations = [j for i in js["translations"] for j in i]
    translations_list = [(t["lang_name"], t["text"]) for t in filter(lambda l: l["lang_name"] not in [source_language, target_language], translations)]
    return (js["text"], translations_list)


def ask_chatgpt(system: str, user: str, model: str) -> str:
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system
            },
            {
                "role": "user",
                "content": user
            }
        ],
        temperature=0,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    answer = response["choices"][0]["message"]["content"]
    return answer


def get_translation(source_text: str, source_language: str, target_language: str, translations: [(str, str)]):
    system = (
        f"You are an expert in all languages. In the following you get an original {source_language} text {'and several translations into other languages' if len(translations) > 0 else ''}."
        f"Translate the original {source_language} text into {target_language}. Ensure that the translated text retains the original meaning, tone, and intent."
        f"The answer has to contain ONLY the translation itself. No explaining text. Otherwise the answer is NOT CORRECT"
    )
    user_lines = [f"Original {source_language}: \"{source_text}\""]
    if len(translations) > 0:
        user_lines.extend([f"{language} Translation: \"{translation}\"" for language, translation in translations])
    user = "\n".join(user_lines)
    print(f"get_translation for '{source_text}'")
    answer = ask_chatgpt(system, user, model="gpt-4")
    print(f"get_translation: answer={answer}")
    return answer


if __name__ == '__main__':
    (source_text, translations) = read_sentence_with_translations(689020, source_language="English", target_language="German")
    get_translation(source_text=source_text, translations=translations, source_language="English", target_language="German")
