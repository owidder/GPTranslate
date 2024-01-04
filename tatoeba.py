import os
import re
import time
import argparse
import openai
import requests
import json
import csv
import zipfile
import pandas as pd
import sys


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


def read_sentence_with_translations(sentence_number: int, source_language: str, target_language: str) -> (str, [(str, str)], [str]):
    response = requests.get(f"https://tatoeba.org/en/api_v0/sentence/{sentence_number}")
    js = json.loads(response.text)
    translations = [j for i in js["translations"] for j in i]
    translations_list = [(t["lang_name"], t["text"]) for t in filter(lambda l: l["lang_name"] not in [source_language, target_language], translations)]
    target_text_list = [t["text"] for t in filter(lambda l: l["lang_name"] == target_language, translations)]
    return (js["text"], translations_list, target_text_list)


def ask_chatgpt(system: str, user: str, model: str) -> str:
    try:
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
    except openai.error.RateLimitError as e:
        print(e.json_body["error"]["message"])
        secnum_re = re.match(".*Please try again in ([0-9.]*)s\..*", e.json_body["error"]["message"])
        if secnum_re:
            secnum = float(secnum_re.groups()[0])
        else:
            secnum = 1
        print(f"wait for {secnum}")
        time.sleep(secnum)
        return ask_chatgpt(system, user, model)
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


def generate_html_table(headers, data):
    """
    Generates an HTML table.

    :param headers: A list of strings representing the column headers.
    :param data: A list of lists, where each inner list is a row of data.
    :return: A string containing the HTML representation of the table.
    """
    # Start the HTML table
    html = '<table border="1">\n'

    # Add the header row
    html += '  <tr>\n'
    for header in headers:
        html += f'    <th>{header}</th>\n'
    html += '  </tr>\n'

    # Add the data rows
    for row in data:
        html += '  <tr>\n'
        for cell in row:
            html += f'    <td>{cell}</td>\n'
        html += '  </tr>\n'

    # Close the HTML table
    html += '</table>'

    return html


def read_tsv_file(filename: str, max_number_of_sentences = sys.maxsize):
    """
    Reads a TSV file and returns the data as a list of dictionaries.

    :param filename: The name of the TSV file to read.
    :return: A list of dictionaries, where each dictionary represents a row of data.
    """
    data = []

    df = pd.read_csv(filename, compression='infer', sep='\t',
                     names=["sentence_no", "language", "text", "author", "ts1", "ts2"])
    current_number_of_sentences = 0
    for index, row in df.iterrows():
        data.append(row.to_dict())
        current_number_of_sentences += 1
        if current_number_of_sentences >= max_number_of_sentences:
            break

    return data


def normalize(str):
    return str.replace('"', '')


def read_translated_sentences(filename) -> [dict]:
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            sentences: [int] = []
            reader = csv.DictReader(file, delimiter='\t', fieldnames=["sentence_no", "ne", "source_text", "with_translations", "without_translations", "t1", "t2", "t3", "t4"])
            for row in reader:
                sentences.append(row)
        return sentences
    else:
        return []


if __name__ == '__main__':
    MIN_LENGTH = 900
    out_name = f"./eng_translations_detailed.{MIN_LENGTH}.tsv"
    translated_sentences = read_translated_sentences(filename=out_name)
    sentences = read_tsv_file(filename=f"./eng_sentences_detailed.{MIN_LENGTH}.tsv", max_number_of_sentences=100)
    sentence_nos = [t["sentence_no"] for t in translated_sentences]
    with open(out_name, 'a', encoding='utf-8') as et:
        for s in sentences:
            sentence_no: int = s["sentence_no"]
            if sentence_no not in sentence_nos:
                (source_text, translations, target_text_list) = read_sentence_with_translations(sentence_no, source_language="English", target_language="German")
                with_translations = normalize(get_translation(source_text=source_text, translations=translations, source_language="English", target_language="German"))
                without_translations = normalize(get_translation(source_text=source_text, translations=[], source_language="English", target_language="German"))
                target_text_csv = "\t".join(target_text_list)
                line = f"{sentence_no}\t{'e' if with_translations == without_translations else 'n'}\t{source_text}\t{with_translations}\t{without_translations}\t{target_text_csv}\n"
                et.write(line)
                et.flush()
