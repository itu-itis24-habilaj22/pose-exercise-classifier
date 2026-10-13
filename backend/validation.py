"""Small checks shared by the endpoints that read JSON from the website."""


def is_whole_number(value, low, high):
    """True for an int from low to high. bool is a subclass of int in Python, so True and
    False are rejected explicitly."""
    return isinstance(value, int) and not isinstance(value, bool) and low <= value <= high
