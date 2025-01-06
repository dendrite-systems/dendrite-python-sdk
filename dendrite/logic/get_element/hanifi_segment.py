import copy
from collections import deque
from dataclasses import dataclass
from typing import List, Optional, Union

from bs4 import BeautifulSoup, Comment, Doctype, NavigableString, Tag

from ..dom.truncate import truncate_and_remove_whitespace, truncate_long_string_w_words


# Define a threshold (e.g., 30% of the total document size)
def calculate_size(element):
    as_str = str(element)
    return len(as_str)


def format_tag(node: Union[BeautifulSoup, Tag]):
    opening_tag = f"<{node.name}"

    # Add all attributes to the opening tag
    for attr, value in node.attrs.items():
        opening_tag += f' {attr}="{value}"'

    # Close the opening tag
    opening_tag += ">"
    return opening_tag


@dataclass
class SegmentGroup:
    node: List[Union[BeautifulSoup, Tag, str]]
    parents: List[Union[BeautifulSoup, Tag]]
    idx: int
    size: int
    order: int = 0


def hanifi_segment(
    node: Union[BeautifulSoup, Tag],
    threshold,
    num_parents: int,
) -> List[List[str]]:
    segment_groups = _new_segment_tree(
        node, threshold, num_parents, 0, deque(maxlen=num_parents)
    )
    return group_segments(segment_groups, threshold * 1.1)


def group_segments(segments: List[SegmentGroup], threshold: int) -> List[List[str]]:
    grouped_segments: List[List[str]] = []
    current_group: List[str] = []
    current_size = 0

    for segment in segments:
        # If adding the current segment doesn't exceed the threshold
        if current_size + segment.size <= threshold:
            current_group.append(reconstruct_html(segment))
            current_size += segment.size
        else:
            # Add the current group to the grouped_segments
            grouped_segments.append(current_group)
            # Start a new group with the current segment
            current_group = [reconstruct_html(segment)]
            current_size = segment.size

    # Add the last group if it's not empty
    if current_group:
        grouped_segments.append(current_group)

    return grouped_segments


def reconstruct_html(segment_group: SegmentGroup) -> str:
    # Initialize an empty list to build the HTML parts
    html_parts = []

    # If the index is not 0, add "..." before the first sibling node
    if segment_group.idx != 0:
        html_parts.append("...")

    # Add the string representation of each node in the segment group
    for node in segment_group.node:
        html_parts.append(str(node))

    # Combine the node HTML parts
    nodes_html = "\n".join(html_parts)

    # Build the HTML by wrapping the nodes_html within the parents
    for parent in reversed(segment_group.parents):
        # Get the opening tag with attributes
        attrs = "".join([f' {k}="{v}"' for k, v in parent.attrs.items()])
        opening_tag = f"<{parent.name}{attrs}>"
        closing_tag = f"</{parent.name}>"
        # Wrap the current nodes_html within this parent
        nodes_html = f"{opening_tag}\n{nodes_html}\n{closing_tag}"

    # Use BeautifulSoup to parse and prettify the final HTML
    soup = BeautifulSoup(nodes_html, "html.parser")
    return soup.prettify()


def _new_segment_tree(
    node: Union[BeautifulSoup, Tag],
    threshold: int,
    num_parents: int,
    index,
    queue: deque,
) -> List[SegmentGroup]:

    result_nodes = []
    idx = 0
    current_group: Optional[SegmentGroup] = None
    queue.append(node)
    for child in node.children:  # type: ignore

        if isinstance(child, (NavigableString, Tag)):
            size = 0
            if isinstance(child, NavigableString):
                child = str(child)
                size = len(child)
                if size > threshold:
                    truncated = truncate_long_string_w_words(
                        child, max_len_start=threshold // 4, max_len_end=threshold // 4
                    )
                    result_nodes.append(
                        SegmentGroup(
                            node=[truncated],
                            parents=list(queue.copy()),
                            idx=idx,
                            size=size,
                        )
                    )
                    idx += 1
                    continue

            elif isinstance(child, Tag):
                size = calculate_size(child)
                if size > threshold:
                    result_nodes.extend(
                        _new_segment_tree(
                            child, threshold, num_parents, idx, queue.copy()
                        )
                    )
                    idx += 1
                    continue

            if current_group is not None:
                if current_group.size + size < threshold:
                    current_group.node.append(child)
                    current_group.size += size
                else:
                    result_nodes.append(current_group)
                    # **Create a new current_group with the current child**
                    current_group = SegmentGroup(
                        node=[child], parents=list(queue.copy()), idx=idx, size=size
                    )
                idx += 1
                continue

            # **Initialize current_group if it's None**
            current_group = SegmentGroup(
                node=[child], parents=list(queue.copy()), idx=idx, size=size
            )
            idx += 1

    if current_group is not None:
        result_nodes.append(current_group)

    return result_nodes


@dataclass
class SelectedTag:
    d_id: str
    reason: str
    index: int  # index of the segment the tag belongs in


def expand_tags(soup: BeautifulSoup, tags: List[SelectedTag]) -> Optional[str]:

    target_d_ids = {tag.d_id for tag in tags}
    target_elements = soup.find_all(
        lambda tag: tag.has_attr("d-id") and tag["d-id"] in target_d_ids
    )

    if len(target_elements) == 0:
        return None

    parents_list = []
    for element in target_elements:
        parents = list(element.parents)
        parents_list.append(parents)

    all_parent_d_ids = frozenset(
        d_id
        for parents in parents_list
        for parent in parents
        if isinstance(parent, Tag) and parent.has_attr("d-id")
        for d_id in [parent.get("d-id")]
    )

    def traverse_and_simplify(element):
        if isinstance(element, Tag):
            d_id = element.get("d-id", "")
            if element in target_elements:
                # Add comments to mark the selected element
                element.insert_before(Comment(f"SELECTED ELEMENT START ({d_id})"))
                element.insert_after(Comment(f"SELECTED ELEMENT END ({d_id})"))

                # If element is too large, continue traversing since we don't want to display large elements
                if len(str(element)) > 40000:
                    for child in list(element.children):
                        if isinstance(child, Tag):
                            traverse_and_simplify(child)
                return
            elif d_id in all_parent_d_ids or element.name == "body":
                for child in list(element.children):
                    if isinstance(child, Tag):
                        traverse_and_simplify(child)
            elif isinstance(element, Tag) and element.name != "body":
                try:
                    truncated_text = truncate_and_remove_whitespace(
                        element.get_text(), max_len_start=200, max_len_end=200
                    )
                    element.replace_with(truncated_text)
                except ValueError:
                    element.replace_with("...")

    soup_copy = copy.copy(soup)
    traverse_and_simplify(soup_copy.body)
    simplified_html = soup_copy.prettify()

    return simplified_html
