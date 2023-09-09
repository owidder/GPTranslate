import os
import json
import openai
import collections
import argparse
from jproperties import Properties


properties = Properties()
openai.api_key = os.getenv("OPENAI_API_KEY")


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


def translate_properties_files(folder_path: str):
    for subdir, dirs, files in os.walk(folder_path):
        for file in sorted(files):
            if file.endswith("properties"):
                file_abs_path = subdir + os.path.sep + file
                print(f"translating: {file_abs_path}")
                with open(file_abs_path, "rb") as f:
                    properties.load(f)
                for item in properties.items():
                    translate_text(source_text=item[1].data, source_language="English", target_language="German")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', required=True, action='store', help='Path to the files to translate')
    args = parser.parse_args()

    translate_properties_files(folder_path=args.path)
