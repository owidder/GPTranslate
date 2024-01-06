import difflib
import nltk

def compare_strings(a, b):
    a_words = nltk.word_tokenize(a)
    b_words = nltk.word_tokenize(b)
    d = difflib.Differ()
    diff = d.compare(a_words, b_words)
    return ' '.join(diff)

string1 = "Hello, dear World!"
string2 = "Hello, amazing World!"

print(compare_strings(string1, string2))