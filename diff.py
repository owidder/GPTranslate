import difflib
from colorama import Fore, Back, Style

def compare_strings(a, b):
    d = difflib.Differ()
    diff = list(d.compare(a, b))

    output = ""

    for i in diff:
        if i[0] == " ":
            output += i
        elif i[0] == "-":
            output += Fore.RED + i + Style.RESET_ALL
        elif i[0] == "+":
            output += Fore.GREEN + i + Style.RESET_ALL

    return output

string1 = "Hello, World!"
string2 = "Hollo, World!"

print(compare_strings(string1, string2))