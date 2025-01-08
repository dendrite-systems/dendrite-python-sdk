import re
import time
from collections import Counter
from typing import List, Optional, Tuple, TypedDict, Union

from bs4 import BeautifulSoup, NavigableString, PageElement, Tag
from bs4.element import Tag

from dendrite.logic.dom.truncate import (
    truncate_and_remove_whitespace,
    truncate_long_string_w_words,
)
from dendrite.logic.llm.token_count import token_count

MAX_REPEATING_ELEMENT_AMOUNT = 6


class FollowableListInfo(TypedDict):
    expanded_elements: List[Tag]
    amount: int
    parent_element_d_id: str
    first_element_d_id: str


class CompressHTML:
    def __init__(
        self,
        root_soup: Union[BeautifulSoup, Tag],
        ids_to_expand: List[str] = [],
        compression_multiplier: float = 1,
        exclude_dendrite_ids=False,
        max_token_size: int = 80000,
        max_size_per_element: int = 6000,
        focus_on_text=False,
    ) -> None:
        if exclude_dendrite_ids == True:
            for tag in root_soup.find_all():
                if "d-id" in tag.attrs:
                    del tag["d-id"]

        self.orginal_size = len(str(root_soup))
        self.root = BeautifulSoup(str(root_soup), "html.parser")
        self.original_root = BeautifulSoup(str(root_soup), "html.parser")
        self.ids_to_expand = ids_to_expand
        self.expand_crawlable_list = False
        self.compression_multiplier = compression_multiplier
        self.lists_with_followable_urls: List[FollowableListInfo] = []
        self.max_token_size = max_token_size
        self.max_size_per_element = max_size_per_element
        self.focus_on_text = focus_on_text
        self.search_terms = []

    def get_lists_with_followable_urls(self):
        return self.lists_with_followable_urls

    def _remove_consecutive_newlines(self, text: str, max_newlines=1):
        cleaned_text = re.sub(r"\n{2,}", "\n" * max_newlines, text)
        return cleaned_text

    def _parent_is_explicitly_expanded(self, tag: Tag) -> bool:
        for tag in tag.parents:
            if tag.get("d-id", None) in self.ids_to_expand:
                return True
        return False

    def _should_expand_anyways(self, tag: Tag) -> bool:
        curr_id = tag.get("d-id", None)

        if curr_id in self.ids_to_expand:
            return True

        tag_descendants = [
            descendant for descendant in tag.descendants if isinstance(descendant, Tag)
        ]
        for tag in tag_descendants:
            id = tag.get("d-id", None)
            if id in self.ids_to_expand:
                return True

        for parent in tag.parents:
            id = parent.get("d-id", None)
            if id in self.ids_to_expand:
                return True
            # Expand the children of expanded elements if the expanded element isn't too big
            if len(str(parent)) > 4000:
                return False

        return False

    def clear_attrs(self, element: Tag, unique_class_names: List[str]):
        attrs = {}
        class_attr = element.get("class", [])
        salient_attributes = [
            "type" "alt",
            "aria-describedby",
            "aria-label",
            "aria-role",
            "input-checked",
            "label",
            "name",
            "option_selected",
            "placeholder",
            "readonly",
            "text-value",
            "title",
            "value",
            "href",
        ]

        attrs = {
            attr: (str(value)[:100] if len(str(value)) > 100 else str(value))
            for attr, value in element.attrs.items()
            if attr in salient_attributes
        }

        if class_attr:
            if isinstance(class_attr, str):
                class_attr = class_attr.split(" ")

            class_name_len = 0
            class_max_len = 200
            classes_to_show = []
            for class_name in class_attr:
                if class_name_len + len(class_name) < class_max_len:
                    classes_to_show.append(class_name)
                    class_name_len += len(class_name)

            if len(classes_to_show) > 0:
                attrs = {**attrs, "class": " ".join(classes_to_show)}

        id = element.get("id")
        d_id = element.get("d-id")

        if isinstance(id, str):
            attrs = {**attrs, "id": id}

        if d_id:
            attrs = {**attrs, "d-id": d_id}

        element.attrs = attrs

    def extract_crawlable_list(
        self, repeating_element_sequence_ids: List[str], amount_repeating_left: int
    ):
        items: List[Tag] = []
        parent_element_d_id: str = ""
        first_element_d_id = repeating_element_sequence_ids[0]

        for d_id in repeating_element_sequence_ids:

            el = self.original_root.find(attrs={"d-id": str(d_id)})
            if (
                parent_element_d_id == ""
                and isinstance(el, Tag)
                and isinstance(el.parent, Tag)
            ):
                parent_element_d_id = str(el.parent.get("d-id", ""))

            original = BeautifulSoup(str(el), "html.parser")
            link = original.find("a")
            if link and isinstance(original, Tag):
                items.append(original)

        if (
            len(items) == len(repeating_element_sequence_ids)
            and len(items) >= MAX_REPEATING_ELEMENT_AMOUNT
            and parent_element_d_id != ""
        ):
            self.lists_with_followable_urls.append(
                {
                    "amount": len(items) + amount_repeating_left,
                    "expanded_elements": items,
                    "parent_element_d_id": parent_element_d_id,
                    "first_element_d_id": first_element_d_id,
                }
            )

    def get_html_display(self) -> str:
        def collapse(element: PageElement) -> str:
            chars_to_keep = 2000 if self.focus_on_text else 100

            if isinstance(element, Tag):
                if element.get("d-id", "") == "-1":
                    return ""

                text = element.get_text()
                if text:
                    element.attrs["is-compressed"] = "true"
                    element.attrs["d-id"] = str(element.get("d-id", ""))
                    element.clear()
                    element.append(
                        truncate_and_remove_whitespace(
                            text, max_len_start=chars_to_keep, max_len_end=chars_to_keep
                        )
                    )
                    return str(element)
                else:
                    return ""
            elif isinstance(element, NavigableString):
                return truncate_and_remove_whitespace(
                    element, max_len_start=chars_to_keep, max_len_end=chars_to_keep
                )
            else:
                return ""

        start_time = time.time()
        class_names = [
            name for tag in self.root.find_all() for name in tag.get("class", [])
        ]

        counts = Counter(class_names)
        unique_class_names = [name for name, count in counts.items() if count == 1]

        def get_repeating_element_info(el: Tag) -> Tuple[str, List[str]]:
            return (
                el.name,
                [el.name for el in el.children if isinstance(el, Tag)],
            )

        def is_repeating_element(
            previous_element_info: Optional[Tuple[str, List[str]]], element: Tag
        ) -> bool:
            if previous_element_info:
                repeat_element_info = get_repeating_element_info(element)
                return (
                    previous_element_info == repeat_element_info
                    and element.name != "div"
                )

            return False

        # children_size += token_count(str(child))
        #     if children_size > 400:
        #         children_left = {}
        #         for c in child.next_siblings:
        #             if isinstance(c, Tag):
        #                 if c.name in children_left:
        #                     children_left[c.name] += 1
        #                 else:
        #                     children_left[c.name] = 0
        #         desc = ""
        #         for c_name in children_left.keys():
        #             desc = f"{children_left[c_name]} {c_name} tag(s) truncated for readability"
        #         child.replace_with(f"[...{desc}...]")
        #         break

        def traverse(tag: Union[BeautifulSoup, Tag]):
            previous_element_info: Optional[Tuple[str, List[str]]] = None
            repeating_element_sequence_ids = []
            has_placed_truncation = False
            same_element_repeat_amount: int = 0

            tag_children = (child for child in tag.children if isinstance(child, Tag))

            total_token_size = 0
            for index, child in enumerate(tag_children):

                total_token_size += len(str(child))
                # if total_token_size > self.max_size_per_element * 4 and index > 60:
                #     names = {}
                #     for next_sibling in child.next_siblings:
                #         if isinstance(next_sibling, Tag):
                #             if next_sibling.name in names:
                #                 names[next_sibling.name] += 1
                #             else:
                #                 names[next_sibling.name] = 1

                #     removable = [sib for sib in child.next_siblings]
                #     for sib in removable:
                #         try:
                #             sib.replace_with("")
                #         except:
                #             print("failed to replace sib: ", str(sib))

                #     truncation_message = []
                #     for element_name, amount_hidden in names.items():
                #         truncation_message.append(
                #             f"{amount_hidden} `{element_name}` element(s)"
                #         )

                #     child.replace_with(
                #         f"[...{','.join(truncation_message)} hidden for readablity ...]"
                #     )
                #     break

                repeating_element_sequence_ids.append(child.get("d-id", "None"))

                if is_repeating_element(previous_element_info, child):
                    same_element_repeat_amount += 1

                    if (
                        same_element_repeat_amount > MAX_REPEATING_ELEMENT_AMOUNT
                        and self._parent_is_explicitly_expanded(child) == False
                    ):
                        amount_repeating = 0
                        if isinstance(child, Tag):
                            for sibling in child.next_siblings:
                                if isinstance(sibling, Tag) and is_repeating_element(
                                    previous_element_info, sibling
                                ):
                                    amount_repeating += 1

                        if has_placed_truncation == False and amount_repeating >= 1:
                            child.replace_with(
                                f"[...{amount_repeating} repeating `{child.name}` elements collapsed for readability...]"
                            )
                            has_placed_truncation = True

                            self.extract_crawlable_list(
                                repeating_element_sequence_ids, amount_repeating
                            )

                            if self.expand_crawlable_list == True:
                                for d_id in repeating_element_sequence_ids:
                                    sequence_element = self.root.find(
                                        attrs={"d-id": str(d_id)}
                                    )

                                    if isinstance(sequence_element, Tag):
                                        original = BeautifulSoup(
                                            str(
                                                self.original_root.find(
                                                    attrs={"d-id": str(d_id)}
                                                )
                                            ),
                                            "html.parser",
                                        )
                                        links = original.find_all("a")
                                        for link in links:

                                            self.ids_to_expand.append(
                                                str(link.get("d-id", "None"))
                                            )
                                        sequence_element.replace_with(original)
                                        traverse(sequence_element)

                            repeating_element_sequence_ids = []
                        else:
                            child.replace_with("")
                        continue

                else:
                    has_placed_truncation = False
                    previous_element_info = get_repeating_element_info(child)
                    same_element_repeat_amount = 0

                # If a parent is expanded, allow larger element until collapsing
                compression_mod = self.compression_multiplier
                if self._parent_is_explicitly_expanded(child):
                    compression_mod = 0.5

                if len(str(child)) < self.orginal_size // 300 * compression_mod:
                    if self._should_expand_anyways(child):
                        traverse(child)
                    else:
                        chars_to_keep = 2000 if self.focus_on_text else 80
                        truncated_text = truncate_long_string_w_words(
                            child.get_text().replace("\n", ""),
                            max_len_start=chars_to_keep,
                            max_len_end=chars_to_keep,
                        )
                        if truncated_text.strip():
                            child.attrs = {
                                "is-compressed": "true",
                                "d-id": str(child.get("d-id", "")),
                            }
                            child.string = truncated_text
                        else:
                            child.replace_with("")
                elif len(str(child)) > self.orginal_size // 10 * compression_mod:
                    traverse(child)
                else:
                    if self._should_expand_anyways(child):
                        traverse(child)
                    else:
                        replacement = collapse(child)
                        child.replace_with(BeautifulSoup(replacement, "html.parser"))

                # total_token_size += len(str(child))
                # print("total_token_size: ", total_token_size)

                # if total_token_size > 2000:
                #     next_element_tags = [
                #         sibling.name for sibling in child.next_siblings if isinstance(sibling, Tag)]
                #     child.replace_with(
                #         f"[...{', '.join(next_element_tags)} tags collapsed for readability...]")

        def remove_double_nested(
            soup: Union[BeautifulSoup, Tag]
        ) -> Union[BeautifulSoup, Tag]:
            for tag in soup.find_all():
                # If a tag only contains a single child of the same type
                children = tag.find_all(recursive=False)
                if (
                    len(children) == 1
                    and tag.contents
                    and isinstance(tag.contents[0], Tag)
                ):
                    child_tag = tag.contents[0]
                    # move the contents of the child tag up to the parent
                    tag.clear()
                    tag.extend(child_tag.contents)
                    if (
                        len(tag.find_all(recursive=False)) == 1
                        and tag.contents
                        and isinstance(tag.contents[0], Tag)
                    ):
                        remove_double_nested(tag)

            return soup

        def is_effectively_empty(element):
            if element.name and not element.attrs:
                if not element.contents or all(
                    isinstance(child, NavigableString) and len(child.strip()) < 3
                    for child in element.contents
                ):
                    return True
            return False

        start_time = time.time()
        for i in range(10):
            for element in self.root.find_all(is_effectively_empty):
                element.decompose()

        for tag in self.root.find_all():
            self.clear_attrs(tag, unique_class_names)

        if len(str(self.root)) < 1500:
            return self.root.prettify()

        # print("time: ", end_time - start_time)

        # remove_double_nested(self.root)
        # clean_attributes(root, keep_dendrite_id=False)
        traverse(self.root)
        # print("traverse time: ", end_time - start_time)

        return self.root.prettify()

    def get_compression_level(self) -> Tuple[str, int]:
        if self.orginal_size > 100000:
            return "4/4 (Extremely compressed)", 4
        elif self.orginal_size > 40000:
            return "3/4 (Very compressed)", 3
        elif self.orginal_size > 4000:
            return "2/4 (Slightly compressed)", 2
        elif self.orginal_size > 400:
            return "1/4 (Very mild compression)", 1
        else:
            return "0/4 (no compression)", 0

    async def compress(self, search_terms: List[str] = []) -> str:
        iterations = 0
        pretty = ""
        self.search_terms = search_terms

        while token_count(pretty) > self.max_token_size or pretty == "":
            iterations += 1
            if iterations > 5:
                break
            compression_level_desc, _ = self.get_compression_level()
            # Show elements with relevant search terms more
            if len(self.search_terms) > 0:

                def contains_text(element):
                    if element:
                        # Check only direct text content, not including nested elements
                        direct_text = "".join(
                            child
                            for child in element.children
                            if isinstance(child, NavigableString)
                        ).lower()
                        return any(
                            term.lower() in direct_text for term in self.search_terms
                        )
                    return False

                matching_elements = self.original_root.find_all(contains_text)
                for element in matching_elements:
                    print(f"Element contains search word: {str(element)[:400]}")
                    d_id = element.get("d-id")
                    if d_id:
                        self.ids_to_expand.append(d_id)

            # print("old: ", self.orginal_size)
            md = self.get_html_display()
            md = self._remove_consecutive_newlines(md)
            pretty = BeautifulSoup(md, "html.parser").prettify()
            end = time.time()
            # print("pretty: ", pretty)
            # print("new: ", token_count(pretty))
            # print("took: ", end - start)
            # print("compression_level: ", compression_level_desc)
            self.compression_multiplier *= 2

        return pretty
