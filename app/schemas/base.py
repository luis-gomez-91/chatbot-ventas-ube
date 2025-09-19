from pydantic import BaseModel


class Response(BaseModel):
    status: str

class Error(Response):
    message: str