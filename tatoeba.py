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


def read_sentence_with_translations(sentence_number: int, source_language: str, target_language: str) -> (str, []):
    response = requests.get(f"https://tatoeba.org/en/api_v0/sentence/{sentence_number}")
    js = json.loads(response.text)
    translations = [j for i in js["translations"] for j in i]
    translations_list = list(filter(lambda l: l != None, [(translations[i]["lang_name"], translations[i]["text"]) if translations[i]["lang_name"] not in [source_language, target_language] else None for i in range(len(translations))]))
    return (js["text"], translations_list)


if __name__ == '__main__':
    ret = read_sentence_with_translations(689020, source_language="English", target_language="German")
    print(ret)
