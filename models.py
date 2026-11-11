import hashlib
from datetime import date, datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


def today_uae():
    return datetime.now(ZoneInfo("Asia/Dubai")).date()


class SearchQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    origin: str = Field(pattern=r"^[A-Z]{3}$")
    destination: str = Field(pattern=r"^[A-Z]{3}$")
    departure: date
    adults: int = Field(default=1, ge=1, le=6)
    direct: bool = False
    budget: int | None = Field(default=None, ge=1, le=100000)
    airline: str = Field(default="", pattern=r"^([A-Z0-9]{2})?$", max_length=2)
    cabin: Literal["economy", "premium", "business", "first"] = "economy"

    @field_validator("origin", "destination", "airline", mode="before")
    @classmethod
    def normalize_code(cls, code):
        return code.strip().upper() if isinstance(code, str) else code

    @model_validator(mode="after")
    def validate_trip(self):
        if self.origin == self.destination:
            raise ValueError("Choose different departure and arrival airports")
        if not today_uae() <= self.departure <= today_uae() + timedelta(days=330):
            raise ValueError("Departure must be today or within the next 330 days")
        return self

    def cache_key(self):
        return hashlib.sha256(self.model_dump_json().encode()).hexdigest()


class Credentials(BaseModel):
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, email):
        return email.lower()


class TokenInput(BaseModel):
    token: str = Field(min_length=20, max_length=128)


class EmailInput(BaseModel):
    email: EmailStr = Field(max_length=254)


class ResetInput(TokenInput):
    password: str = Field(min_length=12, max_length=128)


class AlertInput(BaseModel):
    query: SearchQuery
    target_price: int = Field(ge=1, le=100000)


class InterpretInput(BaseModel):
    text: str = Field(min_length=8, max_length=1000)


class TripExtraction(BaseModel):
    origin: str | None
    destination: str | None
    departure: str | None
    adults: int
    direct: bool
    budget: int | None
    airline: str
    cabin: Literal["economy", "premium", "business", "first"]
    clarification: str | None
