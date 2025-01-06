import asyncio
from typing import Any, Coroutine, List, Optional, Tuple, Union

from bs4 import BeautifulSoup, Tag

from dendrite.logic.config import Config
from dendrite.logic.dom.strip import strip_soup
from dendrite.logic.llm.config import LLMConfig

from .agents import segment_agent, select_agent
from .agents.segment_agent import (
    SegmentAgentFailureResponse,
    SegmentAgentReponseType,
    SegmentAgentSuccessResponse,
    extract_relevant_d_ids,
)
from .hanifi_segment import SelectedTag, expand_tags, hanifi_segment
from .models import Element


async def get_expanded_dom(
    soup: BeautifulSoup, prompt: str, llm_config: LLMConfig
) -> Optional[Tuple[str, List[SegmentAgentReponseType], List[SelectedTag]]]:

    new_nodes = hanifi_segment(soup, 6000, 3)
    tags = await get_relevant_tags(prompt, new_nodes, llm_config)

    succesful_d_ids = [
        (tag.d_id, tag.index, tag.reason)
        for tag in tags
        if isinstance(tag, SegmentAgentSuccessResponse)
    ]

    flat_list = [
        SelectedTag(
            d_id,
            reason=segment_d_ids[2],
            index=segment_d_ids[1],
        )
        for segment_d_ids in succesful_d_ids
        for d_id in segment_d_ids[0]
    ]
    dom = expand_tags(soup, flat_list)
    if dom is None:
        return None
    return dom, tags, flat_list


async def hanifi_search(
    soup: BeautifulSoup,
    prompt: str,
    config: Config,
    time_since_frame_navigated: Optional[float] = None,
    return_several: bool = False,
) -> List[Element]:

    stripped_soup = strip_soup(soup)
    expand_res = await get_expanded_dom(stripped_soup, prompt, config.llm_config)

    if expand_res is None:
        return [Element(status="failed", reason="No element found when expanding HTML")]

    expanded, tags, flat_list = expand_res

    failed_messages = []
    succesful_tags: List[SegmentAgentSuccessResponse] = []
    for tag in tags:
        if isinstance(tag, SegmentAgentFailureResponse):
            failed_messages.append(tag)
        else:
            succesful_tags.append(tag)

    if len(succesful_tags) == 0:
        return [Element(status="failed", reason="No relevant tags found in DOM")]

    (input_token, output_token, res) = await select_agent.select_best_tag(
        expanded,
        flat_list,
        prompt,
        time_since_frame_navigated,
        config.llm_config,
        return_several,
    )

    if not res:
        return [Element(status="failed", reason="Failed to get element")]

    if res.d_id:
        if return_several:
            return [
                Element(status=res.status, dendrite_id=d_id, reason=res.reason)
                for d_id in res.d_id
            ]
        else:
            return [
                Element(status=res.status, dendrite_id=res.d_id[0], reason=res.reason)
            ]

    return [Element(status=res.status, dendrite_id=None, reason=res.reason)]


async def get_relevant_tags(
    prompt: str,
    segments: List[List[str]],
    llm_config: LLMConfig,
) -> List[SegmentAgentReponseType]:

    tasks: List[Coroutine[Any, Any, SegmentAgentReponseType]] = []

    for index, segment in enumerate(segments):
        tasks.append(extract_relevant_d_ids(prompt, segment, index, llm_config))

    results: List[SegmentAgentReponseType] = await asyncio.gather(*tasks)
    if results is None:
        return []

    return results


def get_if_one_tag(
    lst: List[SegmentAgentSuccessResponse],
) -> Optional[SegmentAgentSuccessResponse]:
    curr_item = None
    for item in lst:
        if isinstance(item, SegmentAgentSuccessResponse):
            d_id_count = len(item.d_id)
            if d_id_count > 1:  # There are multiple d_ids
                return None

            if curr_item is None:
                curr_item = item  # There should always be atleast one d_id
            else:  # We have already found a d_id
                return None

    return curr_item


def process_segments(
    nodes: List[Union[Tag, BeautifulSoup]], threshold: int = 5000
) -> List[List[Union[Tag, BeautifulSoup]]]:
    processed_segments: List[List[Union[Tag, BeautifulSoup]]] = []
    grouped_segments: List[Union[Tag, BeautifulSoup]] = []
    current_len = 0
    for index, node in enumerate(nodes):
        node_len = len(str(node))

        if current_len + node_len > threshold:
            processed_segments.append(grouped_segments)
            grouped_segments = []
            current_len = 0

        grouped_segments.append(node)
        current_len += node_len

    if grouped_segments:
        processed_segments.append(grouped_segments)

    return processed_segments


def dump_processed_segments(processed_segments: List[List[Union[Tag, BeautifulSoup]]]):
    for index, processed_segement in enumerate(processed_segments):
        with open(f"processed_segments/segment_{index}.html", "w") as f:
            f.write("######\n\n".join(map(lambda x: x.prettify(), processed_segement)))


def dump_nodes(nodes: List[Union[Tag, BeautifulSoup]]):
    for index, node in enumerate(nodes):
        with open(f"nodes/node_{index}.html", "w") as f:
            f.write(node.prettify())
