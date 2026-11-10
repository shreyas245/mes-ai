"""Compliance ORM: electronic signatures (21 CFR Part 11, plan Phase 2)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from mes_core.shared.base_models import Entity


class ElectronicSignature(Entity):
    __tablename__ = "electronic_signature"

    entity_type: Mapped[str] = mapped_column(String(128), index=True)
    entity_id: Mapped[str] = mapped_column(String(64), index=True)
    signer: Mapped[str] = mapped_column(String(128))
    #: meaning of the signature, e.g. "performed_by", "verified_by".
    meaning: Mapped[str] = mapped_column(String(64))
    signed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
