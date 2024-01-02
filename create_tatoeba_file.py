import csv
import sys


def filter_tatoeba_file(source_filename: str, min_text_length=800, max_sentences=sys.maxsize):

    sentence_count = 0

    with open(source_filename, 'r', encoding='utf-8') as file:
        line_count = len(file.readlines())

    with open(source_filename, 'r', encoding='utf-8') as source, open(f"{source_filename}.{min_text_length}", 'w', encoding='utf-8') as target:
        reader = csv.DictReader(source, delimiter='\t', quotechar='|',
                                fieldnames=["sentence_no", "language", "text", "author", "ts1", "ts2"])

        # Iterate over the rows in the file
        for index, row in enumerate(reader):
            l = len(row["text"])
            if l > min_text_length:
                target.write("\t".join(list(row.values()))+"\n")
                sentence_count += 1
                print(f"{l}: {index} / {row['sentence_no']} / {sentence_count} / {line_count}")
                if sentence_count >= max_sentences:
                    break


if __name__ == '__main__':
    for min_length in range(100, 1000, 100):
        filter_tatoeba_file("./eng_sentences_detailed.tsv", min_text_length=min_length)
