from datetime import date
from typing import Any
from uuid import UUID
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator


app = FastAPI()


def get_error_status_code(errors: list[Any]):
    req_str_fields = ("apelido", "nome", "stack")
    for e in errors:
        if e["type"] == "string_type" and isinstance(e["input"], int):
            if any(field in req_str_fields for field in e["loc"]):
                return status.HTTP_400_BAD_REQUEST

        if e["type"] == "value_error" and req_str_fields[0] in e["loc"]:
            return status.HTTP_400_BAD_REQUEST

    return status.HTTP_422_UNPROCESSABLE_ENTITY

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    error_status_code = get_error_status_code(exc.errors())
    return JSONResponse(
        # TODO: Should test if use null return do something
        # Null for performance: 
        # content=None,

        content=jsonable_encoder({"detail": exc.errors(), "body": None}),
        status_code=error_status_code
    )


class PersonResponse(BaseModel):
    id: UUID
    username: str
    name: str
    birth_date: date
    stack: list[str] | None = None

class PersonRequest(BaseModel):
    username: str = Field(max_length=32, alias="apelido")
    name: str = Field(max_length=100, alias="nome")
    birth_date: date = Field(alias="nascimento")
    stack: list[str] | None = None

    @field_validator("stack")
    def stack_size_validator(cls, stack: list[str]):
        if any(len(stack_item) > 32 for stack_item in stack):
            raise ValueError("Stack item should be less than 32 characters")
        return stack

    @field_validator("username")
    def unique_username(cls, username: str):
        usernames = ["Danilo"]

        if username in usernames:
            raise ValueError("This username is in use")
        return username

@app.post('/pessoas', response_model=PersonRequest)
async def person_create(person: PersonRequest):
    return person
    ...


@app.get('/pessoas', response_model=list[PersonResponse])
async def people(t: str | None):
    ...


@app.get('/pessoas/{person_id}', response_model=PersonResponse)
async def person_by_id(person_id: int):
    ...


@app.get('contagem-pessoas/', response_model=int)
async def person_count() -> int:
    ...
