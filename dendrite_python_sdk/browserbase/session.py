from dendrite_python_sdk.request_handler import create_session, browser_ws_uri


async def connect_uri(generate_session: bool =False) -> str:
    session_id = None

    if generate_session:
        session_id = await create_session()
    
    return await browser_ws_uri(session_id)
