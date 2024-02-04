
from dendrite_python_sdk.InteractionTypes import InteractionTypes


go_to_website = {
    "type": "function",
    "function": {
        "name": "go_to_website",
        "description": "Loads a website with selenium so it can be viewed and interacted with.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the website you wish to visit.",
                },
                "reasons_for_visit": {
                    "type": "string",
                    "description": "Specify why you are visiting the website. E.g 'I'm visiting the website to fetch the lastest news about the startup Dendrite.'",
                },
                "use_vision": {
                    "type": "boolean",
                    "description": "Strongly recommended and true by default. Can be turned of to decrease latency if the task specifies so.",
                },
            },
            "required": ["url", "reasons_for_visit"],
        },
    },
}
look_at_page = {
    "type": "function",
    "function": {
        "name": "look_at_page",
        "description": "This function looks at the current page and can give you advice on what to do next.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Specify what you'd like to understand from the page. E.g 'I am currently looking for a way to authenticate, are there any relevant elements?'",
                },
            },
            "required": ["prompt"],
        },
    },
}
inspect_element = {
    "type": "function",
    "function": {
        "name": "inspect_element",
        "description": "This function allows you to look at the HTML so you can interact with it or extract it's contents.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "If you know that a certain string exists in an element you can search for it by providing the string here.",
                },
                "dendrite_id": {
                    "type": "string",
                    "description": "If you know the dendrite id of an element, this is the best way to find it.",
                },
                "show_neighbors": {
                    "type": "boolean",
                    "description": "True by default. If you only need to see the element you've targeted, set this to false.",
                },
                "look_in_attributes": {
                    "type": "boolean",
                    "description": "If you want to search for strings inside element attributes. False by default since it can generate a huge amount of results.",
                },
                "reason": {
                    "type": "string",
                    "description": "Provide a short reason for the inspect.",
                },
            },
            "required": ["reason"],
        },
    },
}
scroll = {
    "type": "function",
    "function": {
        "name": "scroll",
        "description": "Useful tool for scrolling.",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Provide a short reason for the scroll.",
                },
                "amount_px": {
                    "type": "number",
                    "description": "Amount of pixels to scroll by. Default is 900. Negative numbers scroll upwards.",
                },
                "element_dendrite_id": {
                    "type": "string",
                    "description": "Scroll to the element with this dendrite id.",
                },
            },
            "required": ["reason"],
        },
    },
}
list_environment_vars = {
    "type": "function",
    "function": {
        "name": "list_environment_vars",
        "description": "List the names of all available environment variables. Environment variables can be used in forms and similar by typing ENV:[NAME_OF_ENV]. E.g ENV:LINKEDIN_PASSWORD.",
    },
}
interact_with_element = {
    "type": "function",
    "function": {
        "name": "interact_with_element",
        "description": "Allows you to interact with elements in the page. A dendrite id or xpath must be provided.",
        "parameters": {
            "type": "object",
            "properties": {
                "interaction_type": {
                    "type": "string",
                    "enum": InteractionTypes.get_valid_interaction_types(),
                    "description": "Type of interaction with the element",
                },
                "reason_for_interaction": {
                    "type": "string",
                    "description": "The reason for the interaction.",
                },
                "dendrite_id": {
                    "type": "string",
                    "description": "A unique dendrite id. This is the recommended way to locate elements.",
                },
                "xpath": {
                    "type": "string",
                    "description": "A xpath that is used with selenium to locate the element. E.g '//*[text()='Click Me']'",
                },
                "keys": {
                    "type": "string",
                    "description": "The keys to enter into the element. You can use environment variables by typing ENV:[NAME_OF_ENV]. E.g ENV:LINKEDIN_PASSWORD.",
                },
            },
            "required": ["interaction_type", "reason_for_interaction"],
        },
    },
}


public_tools = [
    go_to_website,
    look_at_page,
    inspect_element,
    scroll,
    list_environment_vars,
    interact_with_element
]
