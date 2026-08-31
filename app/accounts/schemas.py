from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AccountBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class AccountCreate(AccountBase):
    pass


class AccountUpdate(AccountBase):
    pass


class AccountResponse(AccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
