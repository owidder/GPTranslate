import difflib
import csv


def create_td(diff: [str], plusminus: str) -> str:
    td = "<td>"
    for word in diff:
        if word[0] == plusminus:
            td += "<span style = 'color: red;'>{}</span>".format(word[1:])
        elif word[0] == "?" and len(word) > 1:
            pass
        elif word[0] != "+" and word[0] != "-":
            td += "<span style = 'color: black;'>{}</span>".format(word)
    td += "</td>"
    return td


def create_tr(s1, s2):
    diff = difflib.ndiff(s1.split(), s2.split())
    diff_list = list(diff)

    td_1 = create_td(diff_list, "-")
    td_2 = create_td(diff_list, "+")
    return f"<tr>{td_1}{td_2}</tr>"


if __name__ == "__main__":
    MIN_LENGTH = 300
    table = "<table>"
    with open(f"./eng_translations_detailed.{MIN_LENGTH}.tsv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter='\t', quotechar='|',
                                fieldnames=["sentence_no", "ne", "source_text", "with_translations", "without_translations", "translation1", "translation2", "translation3"])
        for index, row in enumerate(reader):
            table += create_tr(row["with_translations"], row["without_translations"])
    table += "</table>"

    with open(f"./eng_table_detailed.{MIN_LENGTH}.html", "w") as tf:
        tf.write(table)
