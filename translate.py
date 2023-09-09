import os
import json
import openai
import collections
import argparse
from jproperties import Properties


openai.api_key = os.getenv("OPENAI_API_KEY")
all_languages = {}


SOURCE_LANGUAGE = ("en", "English")

TARGET_LANGUAGES = {
    "es": "Spanish",
    "id": "Indonesian",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "nl": "Dutch",
    "sv": "Swedish",
    "zh": "Chinese",
}

STYLES = '''
* {
    font-family: "Gill Sans", sans-serif;
}
td, th {
    background: lightgrey;
    padding: 0.5em;
}
.bold {
    font-weight: bolder;
    font-size: 1em;
}

.language {
    font-weight: bolder;
}
'''

TABLE_HEAD = '''
<table>
    <tr>
        <th>key</th>
        <th>source text</th>
        <th>back translation</th>
        <th>check</th>
        <th>translation</th>
    </tr>
'''


def start_validation_file(vf):
    vf.write(f"<html>\n<head><style>{STYLES}</style></head>")
    vf.write(f"{TABLE_HEAD}")


def end_validation_file(vf):
    vf.write("</table>")
    vf.write("</html>")


def add_translation_row(key: str, source_text: str, translation: str, back_translation: str, check: str, vf):
    background_color = "rgba(166, 236, 153, .5)" if check == "Yes" else "rgba(242, 169, 59, .5)"
    vf.write(
        f"<tr>"
        f"<td class='bold' style='background: {background_color}'>{key}</td>"
        f"<td style='background: {background_color}'>{format(source_text)}</td>"
        f"<td style='background: {background_color}'>{format(back_translation)}</td>"
        f"<td style='background: {background_color}'>{check}</td>"
        f"<td style='background: {background_color}'>{format(translation)}</td>"
        f"</tr>\n"
    )


def translate_text(source_text: str, source_language: str, target_language: str) -> str:
    print(f"-----> [{target_language}] translating: {source_text}")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": f"You are an expert in pharmacy. You will be provided with the value of a Java properties file from a pharmacy application in {source_language} language."
                           f"Please translate this text into {target_language}. Please do only translate. Never add your own text."
            },
            {
                "role": "user",
                "content": source_text
            }
        ],
        temperature=0,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    translation = response["choices"][0]["message"]["content"]
    return translation


def check_translation(source_text: str, back_translation: str, source_language: str) -> str:
    print(f"-----> checking: {source_text} <-> {back_translation}")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": f"You are an expert in pharmacy. You will be provided with two values of a Java properties file from a pharmacy application in {source_language} language."
                           f"Please decide whether they have the same meaning! Only answer with Yes or No!"
            },
            {
                "role": "user",
                "content": f"1. {source_text}"
                           f"2. {back_translation}"
            }
        ],
        temperature=0,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    answer = response["choices"][0]["message"]["content"]
    print(f"--------------------> {answer}")
    return "" if answer == "Yes" else back_translation


def translate_source_into_target(source_language: str, source_properties: Properties, target_language: str, target_properties: Properties, folder_path: str):
    with open(f"{folder_path}/validations_{target_language}.html", "w") as vf:
        start_validation_file(vf)
        for source_key in source_properties.keys():
            back_key = f"{source_key}_back"
            check_key = f"{source_key}_check"
            if not (source_key in target_properties.keys() and back_key in target_properties.keys() and check_key in target_properties.keys()):
                translation = translate_text(source_text=source_properties[source_key].data, source_language=source_language, target_language=target_language)
                back_translation = translate_text(source_text=translation, source_language=target_language, target_language=source_language)
                check = check_translation(source_text=source_properties[source_key], back_translation=back_translation, source_language=source_language)
                target_properties[source_key] = translation
                target_properties[back_key] = back_translation
                target_properties[check_key] = check

            add_translation_row(
                key=source_key,
                source_text=source_properties[source_key],
                translation=target_properties[source_key],
                back_translation=target_properties[back_key],
                check=target_properties[check_key],
                vf=vf
            )
        end_validation_file(vf)


def translate_properties_files(folder_path: str):
    for subdir, dirs, files in os.walk(folder_path):
        for source_filename in sorted(files):
            if source_filename.endswith(".properties") and not "_" in source_filename:
                source_properties_file_abs_path = subdir + os.path.sep + source_filename
                print(f"translating: {source_properties_file_abs_path}")
                source_properties = Properties()
                target_properties = Properties()
                with open(source_properties_file_abs_path, "rb") as sf:
                    source_properties.load(sf)
                source_name = source_filename.split(".")[0]
                for target_language_code in TARGET_LANGUAGES.keys():
                    target_filename = f"{source_name}_{target_language_code}.properties"
                    target_properties_file_abs_path = subdir + os.path.sep + target_filename
                    if os.path.exists(target_properties_file_abs_path):
                        with open(target_properties_file_abs_path, "rb") as tf:
                            target_properties.load(tf)
                    translate_source_into_target(
                        source_language=SOURCE_LANGUAGE[1],
                        target_language=TARGET_LANGUAGES[target_language_code],
                        source_properties=source_properties,
                        target_properties=target_properties,
                        folder_path=folder_path
                    )
                    with open(target_properties_file_abs_path, "wb") as tf:
                        target_properties.store(tf, encoding="utf-8")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', required=True, action='store', help='Path to the files to translate')
    args = parser.parse_args()

    translate_properties_files(folder_path=args.path)
