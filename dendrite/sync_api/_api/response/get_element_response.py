from typing import Dict, List, Optional, Union
from pydantic import BaseModel
from dendrite.sync_api._common.status import Status


class GetElementResponse(BaseModel):
    status: Status
    selectors: Optional[Union[List[str], Dict[str, List[str]]]] = None
    message: str = ""
    used_cache: bool = False
