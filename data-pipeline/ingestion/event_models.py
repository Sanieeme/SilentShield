"""Pydantic schemas for the three simulated banking event streams.

These are deliberately the ingestion-time "raw event" shape, distinct from
the backend's JPA entities: the pipeline treats every event as arriving from
an untrusted external source (an ATM, a device, a banking app) and validates
it before anything downstream trusts it.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EventBase(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    timestamp: datetime = Field(default_factory=_utcnow)

    @field_validator("timestamp")
    @classmethod
    def timestamp_not_in_future(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v > _utcnow():
            raise ValueError("event timestamp cannot be in the future")
        return v

    @field_validator("customer_id")
    @classmethod
    def customer_id_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("customer_id must not be blank")
        return v


class AtmEvent(EventBase):
    account_id: str
    atm_id: str
    amount: float = Field(gt=0)
    location: str
    device_id: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_reasonable(cls, v: float) -> float:
        if v > 1_000_000:
            raise ValueError("amount exceeds plausible ATM withdrawal limit")
        return v


class AuthMethod(str, Enum):
    REAL_PIN = "REAL_PIN"
    DURESS_PIN = "DURESS_PIN"
    UNKNOWN = "UNKNOWN"  # what an external observer of a failed attempt would see


class AuthEvent(EventBase):
    """Note: `method` is only ever REAL_PIN/DURESS_PIN in the *simulator*,
    which knows ground truth for evaluation purposes. Anything derived from
    real production auth events must use AuthMethod.UNKNOWN, since the
    backend intentionally never reveals which PIN type was used."""
    success: bool
    method: AuthMethod = AuthMethod.UNKNOWN
    device_id: str
    location: str


class TransactionChannel(str, Enum):
    ATM = "ATM"
    APP = "APP"
    CARD = "CARD"
    ONLINE = "ONLINE"


class TransactionEvent(EventBase):
    account_id: str
    transaction_type: str
    amount: float = Field(gt=0)
    channel: TransactionChannel
    device_id: Optional[str] = None
    location: str
