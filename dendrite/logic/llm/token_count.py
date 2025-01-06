import tiktoken


def token_count(string: str, encoding_name: str = "gpt-4o") -> int:
    encoding = tiktoken.encoding_for_model(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens
