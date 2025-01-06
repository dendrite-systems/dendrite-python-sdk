from typing import Dict, List, Optional, Union

from pydantic import BaseModel

from dendrite.models.status import Status


class GetElementResponse(BaseModel):
    status: Status
    d_id: Optional[str] = None
    selectors: Optional[List[str]] = None
    message: str = ""
