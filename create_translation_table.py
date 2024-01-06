import os
import csv
import nltk
import difflib


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


def create_diff(text1: str, text2: str) -> str:
    text1_words = nltk.word_tokenize(text1)
    text2_words = nltk.word_tokenize(text2)
    d = difflib.Differ()
    diff = d.compare(text1_words, text2_words)
    return ' '.join(diff)


if __name__ == '__main__':
    MIN_LENGTH = 300
    filename = f"eng_translations_detailed.{MIN_LENGTH}.tsv"
    sentences = read_translated_sentences(filename)
    with_translations = sentences[0]['with_translations']
    without_translations = sentences[0]['without_translations']
    print(create_diff(with_translations, without_translations))
    print(sentences)