from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from ingestion.event_models import AtmEvent, AuthEvent, TransactionChannel, TransactionEvent


def test_atm_event_valid():
    evt = AtmEvent(customer_id="CUST-1", account_id="ACC-1", atm_id="ATM-1",
                   amount=500.0, location="Sandton")
    assert evt.amount == 500.0


def test_atm_event_rejects_non_positive_amount():
    with pytest.raises(ValidationError):
        AtmEvent(customer_id="CUST-1", account_id="ACC-1", atm_id="ATM-1",
                 amount=0, location="Sandton")


def test_atm_event_rejects_implausible_amount():
    with pytest.raises(ValidationError):
        AtmEvent(customer_id="CUST-1", account_id="ACC-1", atm_id="ATM-1",
                 amount=2_000_000, location="Sandton")


def test_event_rejects_future_timestamp():
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    with pytest.raises(ValidationError):
        AtmEvent(customer_id="CUST-1", account_id="ACC-1", atm_id="ATM-1",
                 amount=100.0, location="Sandton", timestamp=future)


def test_event_rejects_blank_customer_id():
    with pytest.raises(ValidationError):
        AtmEvent(customer_id="  ", account_id="ACC-1", atm_id="ATM-1",
                 amount=100.0, location="Sandton")


def test_transaction_event_valid():
    evt = TransactionEvent(customer_id="CUST-1", account_id="ACC-1", transaction_type="WITHDRAWAL",
                           amount=250.0, channel=TransactionChannel.APP, location="Rosebank")
    assert evt.channel == TransactionChannel.APP


def test_auth_event_defaults_to_unknown_method():
    evt = AuthEvent(customer_id="CUST-1", success=False, device_id="DEV-1", location="Rosebank")
    assert evt.method.value == "UNKNOWN"
