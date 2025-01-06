def get_script_prompt(final_compressed_html: str, prompt: str, current_url: str):
    return f"""Compressed HTML:
{final_compressed_html}

Please look at the HTML DOM above and use execute_code to accomplish the user's task. 

Don't use the attributes 'is-compressed' and 'd-id' inside your script.

Prefer using soup.select() over soup.find_all().

If you are asked to fetch text from an article or similar it's generally a good idea to find the element(s) containing the article text and extracting the text from those. You'll also need to remove unwanted text from elements that isn't article text.

All elements with the attribute is-compressed="true" are collapsed and may contain hidden elements. If you need to use an element that is compressed you have to call expand_html_further, example:

expand_html_further({{"prompt": "I need to understand the structure of at least one product to create a script that fetches each product, since all the products are compressed I'll expand the first two ones. I'll also expand the pagenation controls since they are relevant for the task.", "d-ids_to_expand": "3uy9v2, 3uy9d2, -29ahd"}})

When scraping a list of items make sure at least one of the items is fully expanded to understand each items' structure before you code. You don't need to expand all items if you can see that there is a repeating structure.

You code must be a full implementation that solves the user's task.

Try to make your scripts as general as possible. They should work for different pages with a similar html structure if possible. No hard-coded values that'll only work for the page above.

Finally, the script must contain a variable called 'response_data'. This variable is sent back to the user and it must match the match the specification inside their prompt listed below.

Current URL: {current_url}
User's Prompt: 
{prompt}"""


def expand_futher_prompt(
    compressed_html: str,
    max_iterations: int,
    iterations: int,
    reasoning_prompt: str,
    question: str,
):
    return f"""{compressed_html}

Please look at the compressed HTML above and output a comma separated of elements that need to be de-compressed so that the task can be solved.

Task: '{question}'

Every element with the attribute is-compressed="true" can be de-compressed. Compressed elements may contain hidden elements such as anchor tags and buttons, so it's really important that relevant element to the task are expanded.

You'll get max {max_iterations} interations to explore the HTML DOM Tree.

You are currently on iteration {iterations}. Try to expand the DOM in relevant places at least three times.

{reasoning_prompt}

It's really important that you expand ALL the elements you believe could be useful for the task! However, in situations where you have repeating elements, such as products elements in a product list or sections of paragraphs in an article, you only need to expand a few of the repeating elements to be able to understand the others' structure.

Now you may output: 
- Ids to inspect further prefixed by some short reasoning (Don't expand irrelevant element and avoid outputting many IDs since that increases the token size of the HTML preview)
- "Done" once every relevant element is expanded.
- An error message if the task is too vauge or not possible to complete. A common use-case for the error message is when a page loads incorrectly and none of the task's data is available.

See the examples below to see each outputs format:

EXAMPLE OUTPUT
Reasoning: Most of the important elements are expanded, but I still need to understand the article's headings' HTML structure. To do this I'll expand the first section heading with the text 'hello kitty' and the d-id adh2ia. I'll also expand the related infobox with the id -s29as. By expanding these I'll be able to understand all the article's titles.
Ids: adh2ia, -s29as
END EXAMPLE OUTPUT

EXAMPLE OUTPUT
Reasoning: To understand the structure of the compressed product cards in the product list I'll expand the three first ones with the d-ids -7ap2j1, -7ap288 and -7ap2au. I'll also the pagenation controls at the bottom of the product list since pagenation can be useful for the task, this includes the page buttons for '1', '2' and '3' button with the d-ids j02ajd, j20had, j9dwh9 and the 'next page' button with the id j9dwss.
Ids: -7ap2j1, -7ap288, -7ap2au, j02ajd, j20had, j9dwh9, j9dwss
END EXAMPLE OUTPUT

EXAMPLE OUTPUT
Done
END EXAMPLE OUTPUT

EXAMPLE OUTPUT
Error: I don't understand what is mean with 'extract the page text', this page is completely empty.
END EXAMPLE OUTPUT"""


def generate_prompt_extract_compressed_html(
    combined_prompt: str,
    expanded_html: str,
    current_url: str,
):
    return f"""You are a web scraping agent that runs one action at a time by outputting a message with either elements to decompress, code to run or a status message. Never run several actions in the same message. 

Code a bs4 or regex script that can solve the task listed below for the webpage I'll specify below. First, inspect relevant areas of the DOM.

<TASK DESCRIPTION>
{combined_prompt}
</TASK DESCRIPTION>

Here is a compressed version of the webpage's HTML: 
<COMPRESSED HTML>
```html
{expanded_html}
```
</COMPRESSED HTML>

Important: Every element with the attribute `is-compressed="true"` is compressed – compressed elements may contain hidden elements such as anchor tags and buttons, so you need to decompress them to fully understand their structure before you write a script!

Below are your available functions and how to use them:

Start by outputting one or more d-ids of elements you'd like to decompress before you right a script. Focus on decompressing elements that look relevant to the task. If possible, expand one d-id at a time. Output in a format like this:

[Short reasoning first.]
```json
{{
    "d-ids": ["xxx", "yyy"]
}}
```

Once you have decompressed the DOM at least one time in separate messages and have a good enough understanding of the page's structure, write some python code to extract the required data using bs4 or regex. `from datetime import datetime` is available.

Your code will be ran inside exec() so don't use a return statement, just create variables. 

To scrape information from the current page use the predefined variable `html_string` (all the page's html as a string) or `soup` (current page's root's bs4 object). Don't use 'd-id' and 'is_compressed' in your script since these are temporary. Use selectors native to the site. 

The script must contain a variable called 'response_data' and it's structure must match the task listed above.

Don't return a response_data with hardcoded values that only work for the current page. The script must be general and work for similar pages with the same structure.

Unless specified, return an exception if a expected value cannot be extracted.

The current URL is: {current_url}

Here's how you can do it in a message:

[Do some reasoning first]
```python
# Simple bs4 code that fetches all the page's hrefs
response_data = [a.get('href') for a in soup.find_all('a')] # Uses the predefined soup variable
```

If the task isn't possible to complete (maybe because the task is too vauge, the page contains an error or the page failed to load) don't try and create a script with many assumptions. Instead, output an error like this:

```json
{{
    "error": "error message"
}}
```

Once you've created and ran a script and you are happy with response_data, output a short success message (max one paragraph) containing json like this, the response_data will automatically be returned to the user once you send this message, you don't need to output it:

```json
{{
    "success": "Write one-two sentences about how your the script works and how you ended up with the result you got."
}}
```

Don't include both the python code and json object in the same message.

Be sure that the the script has been execucted and you have seen the response_data in a previous message before you output the success message."""


LARGE_HTML_CHAR_TRUNCATE_LEN = 40000


def create_script_prompt_segmented_html(
    combined_prompt: str,
    expanded_html: str,
    current_url: str,
):
    if len(expanded_html) / 4 > LARGE_HTML_CHAR_TRUNCATE_LEN:
        html_prompt = f"""```html
    {expanded_html[:LARGE_HTML_CHAR_TRUNCATE_LEN]}
```
This HTML is truncated to {LARGE_HTML_CHAR_TRUNCATE_LEN} characters since it was too large. If you need to see more of the HTML, output a message like this:
```json
{{
    "request_more_html": true
}}
```
"""
    else:
        html_prompt = f"""```html
    {expanded_html}
```
"""

    return f"""You are a web scraping agent that analyzes HTML and writes Python scripts to extract data. Your task is to solve the following request for the webpage specified below.

<TASK DESCRIPTION>
{combined_prompt}
</TASK DESCRIPTION>

Current URL: {current_url}

Here is a truncated version of the HTML that focuses on relevant parts of the webpage (some elements are have been replaced with their text contents):
{html_prompt}

Instructions:
1. Analyze the provided HTML segments carefully.

2. Use bs4 or regex. `from datetime import datetime` is available.
- Your code will be ran inside exec() so don't use a return statement, just create variables. 
- To scrape information from the current page use the predefined variable `html_string` (all the page's html as a string) or `soup` (current page's root's bs4 object). Don't use 'd-id' and 'is_compressed' in your script since these are temporary. Use selectors native to the site. 
- The script must contain a variable called 'response_data' and it's structure must match the task listed above.
- Don't return a response_data with hardcoded values that only work for the current page. The script must be general and work for similar pages with the same structure.
- Unless specified, return an exception if a expected value cannot be extracted.

3. Output your Python script in this format:
[Do some reasoning first]
```python
# Simple bs4 code that fetches all the page's hrefs
response_data = [a.get('href') for a in soup.find_all('a')] # Uses the predefined soup variable
```

Don't output an explaination of the script after the code. Just do some short reasoning before.

4. If the task isn't possible to complete, output an error message like this:
```json
{{
    "error": "Detailed error message explaining why the task can't be completed"
}}
```

5. Once you've successfully created and ran a script, seen that the output is correct and you're happy with it, output a short success message:
```json
{{
    "success": "Brief explanation of how your script works and how you arrived at the result"
}}
```
Remember:
- Only output one action at a time (element index to expand, Python code, or status message).
- Don't include both Python code and JSON objects in the same message.
- Ensure the script has been executed and you've seen the `response_data` before sending the success message.
- Do short reasoning before you output an action, max one-two sentences.
- Never include a success message in the same output as your Python code. Always output the success message after you've seen the result of your code.

You may now begin by analyzing the HTML or requesting to expand specific elements if needed."""
