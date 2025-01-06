import re


def truncate_long_string(
    val: str,
    max_len_start: int = 150,
    max_len_end: int = 150,
    trucate_desc: str = "chars truncated for readability",
):
    return (
        val
        if len(val) < max_len_start + max_len_end
        else val[:max_len_start]
        + f"... [{len(val)-max_len_start-max_len_end} {trucate_desc}] ..."
        + val[-max_len_end:]
    )


def truncate_long_string_w_words(
    val: str,
    max_len_start: int = 150,
    max_len_end: int = 150,
    trucate_desc: str = "words truncated for readability",
    show_more_words_for_longer_val: bool = True,
):
    if len(val) < max_len_start + max_len_end:
        return val
    else:
        if show_more_words_for_longer_val:
            max_len_end += int(len(val) / 100)
            max_len_end += int(len(val) / 100)

        truncate_start_pos = max_len_start
        steps_taken_start = 0
        while (
            truncate_start_pos > 0
            and val[truncate_start_pos] not in [" ", "\n"]
            and steps_taken_start < 20
        ):
            truncate_start_pos -= 1
            steps_taken_start += 1

        truncate_end_pos = len(val) - max_len_end
        steps_taken_end = 0
        while (
            truncate_end_pos < len(val)
            and val[truncate_end_pos] not in [" ", "\n"]
            and steps_taken_end < 20
        ):
            truncate_end_pos += 1
            steps_taken_end += 1

        if steps_taken_start >= 20 or steps_taken_end >= 20:
            # Return simple truncation if we've looped further than 20 chars
            return truncate_long_string(val, max_len_start, max_len_end, trucate_desc)
        else:
            return (
                val[:truncate_start_pos]
                + f" [...{len(val[truncate_start_pos:truncate_end_pos].split())} {trucate_desc}...] "
                + val[truncate_end_pos:]
            )


def remove_excessive_whitespace(text: str, max_whitespaces=1):
    return re.sub(r"\s{2,}", " " * max_whitespaces, text)


def truncate_and_remove_whitespace(text, max_len_start=100, max_len_end=100):
    return truncate_long_string_w_words(
        remove_excessive_whitespace(text),
        max_len_start=max_len_start,
        max_len_end=max_len_end,
    )
