from __future__ import annotations

import uuid

from models.base_models import BaseModel
from models.plan_feature import PlanFeature
from sqlalchemy import Boolean, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Plan(BaseModel):
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tier_level: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    monthly_price: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    yearly_price: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    discount_percent: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=0.0
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    features: Mapped[list[PlanFeature]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )

    def module_codes(self) -> set[str]:
        """Reads the plan_features row with feature_key='modules' as the
        set of enabled ModuleCode values. Requires features to be eager
        loaded (selectinload), otherwise this triggers a lazy load."""
        for feature in self.features:
            if feature.feature_key == "modules":
                return set(feature.value)
        return set()
