from datetime import date
from json import dumps
from typing import Any
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.data import PersonEntity, async_session

app = FastAPI()


def get_error_status_code(errors: list[Any]):
    req_str_fields = ('apelido', 'nome', 'stack')
    for e in errors:
        if e['type'] == 'string_type' and isinstance(e['input'], int):
            if any(field in req_str_fields for field in e['loc']):
                return status.HTTP_400_BAD_REQUEST

        if e['type'] == 'value_error' and req_str_fields[0] in e['loc']:
            return status.HTTP_400_BAD_REQUEST

    return status.HTTP_422_UNPROCESSABLE_ENTITY


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    error_status_code = get_error_status_code(exc.errors())
    return JSONResponse(
        # TODO: Should test if use null return do something
        # Null for performance:
        # content=None,
        content=jsonable_encoder({'detail': exc.errors(), 'body': None}),
        status_code=error_status_code,
    )


class PersonResponse(BaseModel):
    id: UUID
    username: str
    name: str
    birth_date: date
    stack: list[str] | None = None


class PersonRequest(BaseModel):
    username: str = Field(max_length=32, alias='apelido')
    name: str = Field(max_length=100, alias='nome')
    birth_date: date = Field(alias='nascimento')
    stack: list[str] | None = None

    @field_validator('stack')
    def stack_size_validator(cls, stack: list[str]):
        if any(len(stack_item) > 32 for stack_item in stack):
            raise ValueError('Stack item should be less than 32 characters')
        return stack


async def get_session() -> async_sessionmaker[AsyncSession]:
    return async_session
    ...


@app.post('/pessoas', status_code=status.HTTP_201_CREATED)
async def person_create(
    res: Response,
    person: PersonRequest,
    session: async_sessionmaker[AsyncSession] = Depends(get_session),
):
    async with session() as s:
        async with s.begin():
            person_query = await s.scalars(
                select(PersonEntity).where(
                    PersonEntity.username == person.username
                )
            )

            if person_query.one_or_none():
                raise HTTPException(status_code=422)
            model_dump = person.model_dump()
            model_dump["stack"] = dumps(model_dump["stack"])
            new_person = PersonEntity(id=uuid4(), **model_dump)
            s.add(new_person)
            s.commit()
            res.headers.update({"Location": f"/pessoas/{new_person.id}"})


@app.get('/pessoas', response_model=list[PersonResponse])
async def people(t: str | None):
    ...


@app.get('/pessoas/{person_id}', response_model=PersonResponse)
async def person_by_id(person_id: int):
    ...


@app.get('contagem-pessoas/', response_model=int)
async def person_count() -> int:
    ...
