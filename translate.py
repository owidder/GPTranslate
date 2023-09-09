import os
import json
import openai
import collections
import argparse
from jproperties import Properties


properties = Properties()
openai.api_key = os.getenv("OPENAI_API_KEY")
all_languages = {}


LANGUAGES = {
    "chi": "Chinese",
    "dut": "Dutch",
    "ind": "Indonesian",
    "ita": "Italian",
    "jpn": "Japanese",
    "kor": "Korean",
    "swe": "Swedish",
    "spa": "Spanish"
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


def init_validations_file(folder_path: str):
    with open(f"{folder_path}/validations.html") as f:
        f.write(f"<html>\n<head><style>{STYLES}</style></head>")



def translate_source_into_target(source_language: str, source_properties: dict, target_language: str, target_properties: dict, validations_file) -> dict:
    for source_key in source_properties.keys():
        if not source_key in target_properties.keys():
            translation = translate_text(source_text=source_properties[source_key], source_language=source_language, target_language=target_language)
            back_translation = translate_text(source_text=translation, source_language=target_language, target_language=source_language)


def translate_properties_files(folder_path: str):
    for subdir, dirs, files in os.walk(folder_path):
        for file in sorted(files):
            if file.endswith("properties"):
                file_abs_path = subdir + os.path.sep + file
                print(f"translating: {file_abs_path}")
                with open(file_abs_path, "rb") as f:
                    properties.load(f)
                name = file.split(".")[0]
                if name in all_languages.keys():
                    language = all_languages[name]
                else:
                    language = {}
                    all_languages[name] = language
                for item in properties.items():
                    translate_text(source_text=item[1].data, source_language="English", target_language="German")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', required=True, action='store', help='Path to the files to translate')
    args = parser.parse_args()

    translate_properties_files(folder_path=args.path)
