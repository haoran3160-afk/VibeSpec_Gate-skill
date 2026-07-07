from pydantic import BaseModel

class Request(BaseModel):
    method: str
    params: dict

def handle(raw: dict):
    request = Request.model_validate(raw)
    return request.params
