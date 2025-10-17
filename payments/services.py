from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from django.utils import timezone
from typing import Literal


@dataclass
class PaymentResult:
    status: Literal['success', 'failure']
    reference: str
    processed_at: datetime


def process_mock_payment(amount: float) -> PaymentResult:
    """Pretend to charge a card and return a receipt-like object."""
    now = timezone.now()
    reference = f"MOCK-{int(now.timestamp())}"
    return PaymentResult(status='success', reference=reference, processed_at=now)
