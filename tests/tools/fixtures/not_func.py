def make(client, params):
    def word_count(text: str) -> int:
        return len(text.split())

    return word_count
