def compare_strings(s1, s2):
    import difflib

    diff = difflib.ndiff(s1.split(), s2.split())

    for word in diff:
        if word[0] == '-':
            print(f'\033[31m{word}\033[39m')  # Red color for deletions
        elif word[0] == '+':
            print(f'\033[32m{word}\033[39m')  # Green color for additions
        else:
            print(word)


s1 = "This is line one"
s2 = "That was line one"
compare_strings(s1, s2)
