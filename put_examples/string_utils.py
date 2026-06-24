def reverse(s):
    return s[::-1]


def is_palindrome(s):
    s = s.lower().replace(" ", "")
    return s == s[::-1]


def capitalize_words(s):
    return " ".join(word.capitalize() for word in s.split())
