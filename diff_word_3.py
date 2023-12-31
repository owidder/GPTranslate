import difflib
import csv


def create_td(diff: [str], plusminus: str) -> str:
    td = "<td style='border-bottom:3px solid white;border-right:3px solid white;'>"
    for word in diff:
        if word[0] == plusminus:
            td += "<span style = 'color: red; font-weight: bold;'>{}</span>".format(word[1:])
        elif word[0] == "?" and len(word) > 1:
            pass
        elif word[0] != "+" and word[0] != "-":
            td += "<span style = 'color: black;'>{}</span>".format(word)
    td += "</td>"
    return td


def create_tr(with_tranlations, without_translations, source_text: str, official_translation: str, ne: str):
    with_without_diff_list = list(difflib.ndiff(with_tranlations.split(), without_translations.split()))
    with_official_diff_list = list(difflib.ndiff(with_tranlations.split(), official_translation.split()))
    without_official_diff_list = list(difflib.ndiff(without_translations.split(), official_translation.split()))

    td_1 = create_td(with_without_diff_list, "-")
    td_2 = create_td(with_without_diff_list, "+")
    td_3 = create_td(with_official_diff_list, "+")
    td_4 = create_td(without_official_diff_list, "+")
    color = 'lightblue' if ne == "n" else 'lightgrey'
    return f"<tr style='background-color: {color};'><td style='border-bottom:3px solid white;border-right:3px solid white;'>{source_text}</td>{td_1}{td_2}{td_3}{td_4}</tr>"


if __name__ == "__main__":
    MIN_LENGTH = 100
    table = '<table style="font-family:verdana; font-size:12px; border: 1px solid white;">'
    table += '<tr><th>source text</th><th>with translations</th><th>without translations</th><th>official vs. with translations</th><th>official vs. without translations</th></tr>'
    with open(f"./eng_translations_detailed.{MIN_LENGTH}.tsv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter='\t', quotechar='|',
                                fieldnames=["sentence_no", "ne", "source_text", "with_translations", "without_translations", "translation1", "translation2", "translation3"])
        for index, row in enumerate(reader):
            table += create_tr(
                with_tranlations=row["with_translations"],
                without_translations=row["without_translations"],
                source_text=row["source_text"],
                official_translation=row["translation1"],
                ne=row["ne"]
            )
    table += "</table>"

    with open(f"./eng_table_detailed.{MIN_LENGTH}.html", "w") as tf:
        tf.write(table)
