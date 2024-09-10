from typing import List, Optional

from pydantic import BaseModel


class GetElementResponse(BaseModel):
    selectors: Optional[List[str]] = None
    message: str = ""
