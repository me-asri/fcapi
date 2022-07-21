from pydantic import BaseModel, Field


class Result(BaseModel):
    code: str = Field(..., example='200')
    message: str = Field(..., example='Operation successful')
