import os
import re
import time
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
TARGET_LANGUAGE = "German"

def read_translation_file(filepath: str):
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.readlines()

    translations = {}
    for line in content:
        line = line.strip()
        if line and not line.startswith("#"):  # Ignoring comments and empty lines
            key, value = line.split("=", 1)
            translations[key.strip()] = value.strip()
    return translations


def collect_translations_from_directory(directory_path: str):
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


def collect_failed_messages_keys(directory_path: str, target_language_code: str) -> [str]:
    with open(os.path.join(directory_path, f"_failed_messages_{target_language_code}.properties"), "r") as tm:
        lines = tm.readlines()
    keys = [line.split('=')[0] for line in lines]
    return keys


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
        f"You are an expert in pharmacy and computers. In the following you get an original {source_language} text from a Java properties file {'and several translations into other languages' if len(translations) > 0 else ''}."
        f"Translate the original {source_language} text into {target_language}. Ensure that the translated text retains the original meaning, tone, and intent."
        f"The answer has to contain ONLY the translation itself. No explaining text. Otherwise the answer is NOT CORRECT"
    )
    user_lines = [f"Original {source_language}: \"{source_text}\""]
    if len(translations) > 0:
        user_lines.extend([f"{language} Translation: \"{translation}\"" for language, translation in translations.items()])
    user = "\n".join(user_lines)
    print(f"get_translation for '{source_text}'")
    answer = ask_chatgpt(system, user, model="gpt-4")
    print(f"get_translation: answer={answer}")
    return answer


def check_translation(source_text: str, source_language: str, back_translation: str) -> str:
    system = (
        f"You are an expert in pharmacy and computers. In the following you get two {source_language} texts from a Java properties file."
        f"Check whether both texts have a similar meaning."
        f"Answer only with Yes or No"
    )
    user = (
        f"First text: {source_text}"
        f"Second text: {back_translation}"
    )
    print(f"check_translation {source_text} <-> {back_translation}")
    answer = ask_chatgpt(system, user, model="gpt-3.5-turbo")
    print(f"check_translation: answer={answer}")
    return answer


def check_translation_2(source_text: str, source_language: str, translation: str, target_language: str) -> str:
    system = (
        f"You are an expert in pharmacy and computers. In the following you get two texts from a Java properties file."
        f"The first text in {source_language} the second text is in {target_language}"
        f"Check whether there is a possible translation from the second text to the first text."
        f"Answer only with Yes or No"
    )
    user = (
        f"First text: {source_text}"
        f"Second text: {translation}"
    )
    print(f"check_translation {source_text} <-> {translation}")
    answer = ask_chatgpt(system, user, model="gpt-3.5-turbo")
    print(f"check_translation: answer={answer}")
    return answer



def normalize(text: str) -> str:
    return text.replace('"', '').replace("'", "")


def translate_and_improve(source_text: str, source_language: str, target_language: str, translations: [], test_translation="") -> (str, str, str, str):
    translations1 = translations.copy()
    if source_language in translations1:
        del translations1[source_language]
    translations2 = translations.copy()

    translation = normalize(get_translation(source_text=source_text, translations=translations1, source_language=source_language, target_language=target_language))
    check_2 = ""

    if translation.lower() == test_translation.lower():
        return test_translation, None, None, None
    else:
        back_translation = normalize(get_translation(source_text=translation, translations=translations2, source_language=target_language, target_language=source_language))
        check = check_translation(source_text=source_text, back_translation=back_translation, source_language=source_language)
        if check.lower() != 'yes':
            check_2 = check_translation_2(source_text=source_text, source_language=source_language, translation=translation, target_language=target_language)
        print("------------------------------")
        print(f"source text: {source_text}")
        print(f"translation: {translation}")
        print(f"back translation: {back_translation}")
        print(f"check: {check}")
        print(f"check_2: {check_2}")
        return translation, back_translation, check, check_2


def get_language_code(language: str) -> str:
    for lc in LANGUAGES:
        if LANGUAGES[lc] == language:
            return lc

    return ""


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=f"Translate {SOURCE_LANGUAGE} text using OpenAI based on translations from a directory.")
    parser.add_argument('--path', required=True, help='Path to the directory containing the resource bundles.')

    args = parser.parse_args()

    target_language_code = get_language_code(TARGET_LANGUAGE)

    translations_data = collect_translations_from_directory(args.path)
    failed_messages_keys = collect_failed_messages_keys(args.path, target_language_code)

    with (open(f"{args.path}/messages_{target_language_code}.properties", "a") as f,
          open(f"{args.path}/_failed_messages_{target_language_code}.properties", "w") as failed_f,
          open(f"{args.path}/test_messages_{target_language_code}.properties", "a") as tf):
        for key, translations in translations_data.items():
            if SOURCE_LANGUAGE in translations and not TARGET_LANGUAGE in translations and not key in failed_messages_keys:
                print(f"######################## {key} ###################################")
                source_text = translations[SOURCE_LANGUAGE]
                translation, back_translation, check, check_2 = translate_and_improve(
                    source_text=translations[SOURCE_LANGUAGE],
                    source_language=SOURCE_LANGUAGE,
                    target_language=TARGET_LANGUAGE,
                    translations=translations
                )
                print("++++++++++++++++++++++++++++++++++++++++++++++++")
                test_translation, test_back_translation, test_check, test_check_2 = translate_and_improve(
                    source_text=translations[SOURCE_LANGUAGE],
                    source_language=SOURCE_LANGUAGE,
                    target_language=TARGET_LANGUAGE,
                    translations=[],
                    test_translation=translation
                )

                if check.lower() == 'yes' or check_2.lower() == 'yes' or source_text.lower() == back_translation.lower():
                    f.write(f"{key}={translation}\n")
                else:
                    failed_f.write(f"{key}={translation}\n")
                    failed_f.write(f"{key}.back={back_translation}\n")
                    failed_f.write(f"{key}.source={source_text}\n")

                tf.write(f"{key}={test_translation}\n")
                tf.write(f"{key}.source={source_text}\n")
                tf.write(f"{key}.counter={translation}\n")
                tf.write(f"{key}.back={back_translation}\n")
                tf.write(f"{key}.test_back={test_back_translation}\n")
                tf.write(f"{key}.check={check}\n")
                tf.write(f"{key}.check_2={check_2}\n")
                tf.write(f"{key}.test_check={test_check}\n")
                tf.write(f"{key}.test_check_2={test_check_2}\n")

                f.flush()
                failed_f.flush()
                tf.flush()

                time.sleep(3)