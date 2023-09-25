import os
import re
import argparse
import openai


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

def read_translation_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.readlines()

    translations = {}
    for line in content:
        line = line.strip()
        if line and not line.startswith("#"):  # Ignoring comments and empty lines
            key, value = line.split("=", 1)
            translations[key.strip()] = value.strip()
    return translations


def collect_translations_from_directory(directory_path):
    all_translations = {}
    for filename in os.listdir(directory_path):
        if filename == "messages.properties":
            language = SOURCE_LANGUAGE
        else:
            match = re.match(r'messages_([a-z]{2})\.properties', filename)
            if match:
                language_code = match.group(1)
                language = LANGUAGES[language_code]
            else:
                continue

        filepath = os.path.join(directory_path, filename)
        file_translations = read_translation_file(filepath)

        for key, value in file_translations.items():
            if key not in all_translations:
                all_translations[key] = {}
            all_translations[key][language] = value

    return all_translations


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


def get_translation(source_text: str, source_language: str, target_language: str, translations: []):
    system = (
        f"You are an expert in pharmacy and computers. In the following you get an original {source_language} text from a Java properties file and several translations into other languages."
        f"Translate the original {source_language} text into {target_language}. Ensure that the translated text retains the original meaning, tone, and intent."
        f"Answer only with the translation. No quotes"
    )
    user_lines = [f"Original {source_language}: \"{source_text}\""]
    user_lines.extend([f"{language} Translation: \"{translation}\"" for language, translation in translations.items()])
    user = "\n".join(user_lines)
    answer = ask_chatgpt(system, user, model="gpt-3.5-turbo")
    return answer


def check_translation(source_text: str, source_language: str, back_translation: str) -> str:
    system = (
        f"You are an expert in pharmacy and computers. In the following you get two {source_language} texts from a Java properties file."
        f"Check whether both texts have the same meaning, tone and intent"
        f"Answer only with Yes or No"
    )
    user = (
        f"First text: {source_text}"
        f"Second text: {back_translation}"
    )
    answer = ask_chatgpt(system, user, model="gpt-3.5-turbo")
    return answer


def normalize(text: str) -> str:
    return text.replace('"', '').replace("'", "")


def translate_and_improve(source_text: str, source_language: str, target_language: str, translations: []):
    translations1 = translations.copy()
    del translations1[source_language]
    translations2 = translations.copy()

    translation = normalize(get_translation(source_text=source_text, translations=translations1, source_language=source_language, target_language=target_language))
    back_translation = normalize(get_translation(source_text=translation, translations=translations2, source_language=target_language, target_language=source_language))
    check = check_translation(source_text=source_text, back_translation=back_translation, source_language=source_language)
    print("------------------------------")
    print(f"sorce text: {source_text}")
    print(f"translation: {translation}")
    print(f"back translation: {back_translation}")
    print(f"check: {check}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=f"Translate {SOURCE_LANGUAGE} text using OpenAI based on translations from a directory.")
    parser.add_argument('--path', required=True, help='Path to the directory containing the resource bundles.')

    args = parser.parse_args()

    translations_data = collect_translations_from_directory(args.path)
    for english_text, translations in translations_data.items():
        if "English" in translations:
            source_text = translations[SOURCE_LANGUAGE]
            translate_and_improve(source_text=translations[SOURCE_LANGUAGE], source_language=SOURCE_LANGUAGE, target_language="German", translations=translations)
