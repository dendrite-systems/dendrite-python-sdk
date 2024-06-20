from dendrite_python_sdk.request_handler import create_session, browser_ws_uri, send_request


async def remote_connect_uri(generate_session: bool = False) -> str:
    """
    Returns the WebSocket URI for connecting to a remote browser session.

    Args:
        generate_session (bool, optional): Whether to generate a new session ID. Defaults to False.

    Returns:
        str: The WebSocket URI for connecting to the remote browser session.
    """
    session_id = None

    if generate_session:
        session_id = await create_session()
    
    return await browser_ws_uri(session_id)

async def get_download(session_id:str):
    res = await send_request(f"browser/sessions/{session_id}/download", method="GET")
    return res  

