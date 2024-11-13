from typing import Union
from pydantic import BaseModel


class AuthenticateDTO(BaseModel):
    domains: Union[str, list[str]]
