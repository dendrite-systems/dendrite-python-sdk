from typing import List
from dendrite_python_sdk.dto.GetSessionDTO import GetSessionDTO
from dendrite_python_sdk.request_handler import get_session_data, send_request


async def get_auth_session(user_id: str, domain: str) -> List[dict]:
    dto = GetSessionDTO(
        user_id=user_id,
        domain=domain
    )
    session = await get_session_data(dto)
    return session.session_data