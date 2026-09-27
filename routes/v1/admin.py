from __future__ import annotations

import uuid
from uuid import UUID

from app.admin.audit_trail.repositories.audit_trail_repository import (
    AdminAuditTrailRepository,
)
from app.admin.audit_trail.schemas.audit_trail import AuditTrailResponse
from app.admin.audit_trail.services.audit_trail_service import AdminAuditTrailService
from app.admin.currency.repositories.currency_repository import AdminCurrencyRepository
from app.admin.currency.schemas.currency import (
    CurrencyCreate,
    CurrencyResponse,
    CurrencyUpdate,
)
from app.admin.currency.services.currency_service import AdminCurrencyService
from app.admin.plan.repositories.plan_repository import PlanRepository
from app.admin.plan.schemas.plan import PlanRequest, PlanResponse
from app.admin.plan.services.plan_service import PlanService
from app.admin.user.repositories.user_repository import AdminUserRepository
from app.admin.user.schemas.user import (
    AdminUserCreateRequest,
    AdminUserResponse,
    AdminUserUpdateRequest,
)
from app.admin.user.services.user_service import AdminUserService
from app.core.session import get_db
from app.repositories.subscription_event_repository import SubscriptionEventRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.schemas.base_schema import APIResponse, PaginatedResponse
from app.services.subscription_service import SubscriptionService
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_account
from app.core.helpers import success

router = APIRouter(prefix="/admin", tags=["Admin Endpoints"])

# ---------------------------------------------------------------------------
# Plan Endpoints
# ---------------------------------------------------------------------------
@router.get("/plans", response_model=APIResponse[list[PlanResponse]], tags=["Plans"])
async def get_plans(
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user=Depends(get_current_user),  # noqa: B008
    account=Depends(require_account("admin", permission="plans.read")),
     # noqa: B008
):
    service = PlanService(PlanRepository(db))
    plans = await service.get_all_plans()
    return success(True, "Plans fetched successfully", plans)

@router.post("/plans", response_model=APIResponse[PlanResponse], tags=["Plans"])
async def create_plan(
    payload: PlanRequest,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user=Depends(get_current_user),  # noqa: B008
    account=Depends(require_account("admin", permission="plans.create")),
     # noqa: B008
):
    service = PlanService(PlanRepository(db))
    plan = await service.create_plan(payload)
    await service.plan_repository.session.commit()
    return success(True, "Plan created successfully", plan)

@router.get("/plans/{plan_id}", response_model=APIResponse[PlanResponse], tags=["Plans"])
async def get_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user=Depends(get_current_user),  # noqa: B008
    account=Depends(require_account("admin", permission="plans.read")),
     # noqa: B008
):
    service = PlanService(PlanRepository(db))
    plan = await service.get_plan(plan_id)
    return success(True, "Plan fetched successfully", plan)

@router.patch("/plans/{plan_id}", response_model=APIResponse[PlanResponse], tags=["Plans"])
async def update_plan(
    plan_id: uuid.UUID,
    payload: PlanRequest,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user=Depends(get_current_user),  # noqa: B008
    account=Depends(require_account("admin", permission="plans.update")),
     # noqa: B008
):
    service = PlanService(PlanRepository(db))
    plan = await service.update_plan(plan_id, payload)
    await service.plan_repository.session.commit()
    return success(True, "Plan updated successfully", plan)

@router.delete("/plans/{plan_id}", response_model=APIResponse[None], tags=["Plans"])
async def delete_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user=Depends(get_current_user),  # noqa: B008
    account=Depends(require_account("admin", permission="plans.delete")),
     # noqa: B008
):
    service = PlanService(PlanRepository(db))
    await service.delete_plan(plan_id)
    await service.plan_repository.session.commit()
    return success(True, "Plan deleted successfully", None)

# ---------------------------------------------------------------------------
# User Endpoints
# ---------------------------------------------------------------------------
@router.get(
    "/users",
    response_model=APIResponse[PaginatedResponse[AdminUserResponse]],
    tags=["Users"],
)
async def get_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user=Depends(get_current_user),  # noqa: B008
    account=Depends(require_account("admin", permission="user.read")),  # noqa: B008
):
    service = AdminUserService(AdminUserRepository(db))
    users, total = await service.get_users(page=page, size=size)
    
    users = PaginatedResponse(
        items=users,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )

    return success(True, "Users fetched successfully", users)

@router.get(
    "/users/{user_id}",
    response_model=APIResponse[AdminUserResponse],
    tags=["Users"],
)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user=Depends(get_current_user),  # noqa: B008
    account=Depends(require_account("admin", permission="user.read")),  # noqa: B008
):
    service = AdminUserService(AdminUserRepository(db))
    fetched_user = await service.get_user(user_id)
    return success(True, "User fetched successfully", fetched_user)

@router.post(
    "/users",
    response_model=APIResponse[AdminUserResponse],
    tags=["Users"],
)
async def create_user(
    payload: AdminUserCreateRequest,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user=Depends(get_current_user),  # noqa: B008
    account=Depends(require_account("admin", permission="user.create")),  # noqa: B008
):
    service = AdminUserService(AdminUserRepository(db))
    created_user = await service.create_user(payload)
    await service.repository.session.commit()
    return success(True, "User created successfully", created_user)

@router.patch(
    "/users/{user_id}",
    response_model=APIResponse[AdminUserResponse],
    tags=["Users"],
)
async def update_user(
    user_id: uuid.UUID,
    payload: AdminUserUpdateRequest,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user=Depends(get_current_user),  # noqa: B008
    account=Depends(require_account("admin", permission="user.update")),  # noqa: B008
):
    service = AdminUserService(AdminUserRepository(db))
    updated_user = await service.update_user(user_id, payload)
    await service.repository.session.commit()
    return success(True, "User updated successfully", updated_user)

@router.delete(
    "/users/{user_id}",
    response_model=APIResponse[None],
    tags=["Users"],
)
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user=Depends(get_current_user),  # noqa: B008
    account=Depends(require_account("admin", permission="user.delete")),  # noqa: B008
):
    service = AdminUserService(AdminUserRepository(db))
    await service.delete_user(user_id)
    await service.repository.session.commit()
    return success(True, "User deleted successfully", None)

@router.get(
    "/users/type/{user_type}",
    response_model=APIResponse[PaginatedResponse[AdminUserResponse]],
    tags=["Users"],
)
async def get_users_by_type(
    user_type: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user=Depends(get_current_user),  # noqa: B008
    account=Depends(require_account("admin", permission="user.read")),  # noqa: B008
):
    service = AdminUserService(AdminUserRepository(db))
    users, total = await service.get_users_by_type(user_type=user_type, page=page, size=size)
    
    users = PaginatedResponse(
        items=users,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )
    return success(True, "Users fetched successfully", users)

# ---------------------------------------------------------------------------
# Currency Endpoints
# ---------------------------------------------------------------------------
@router.get(
    "/currencies",
    response_model=APIResponse[PaginatedResponse[CurrencyResponse]],
    tags=["Currencies"],
)
async def get_currencies(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user=Depends(get_current_user),  # noqa: B008
    account=Depends(require_account("admin", permission="currency.read")),  # noqa: B008
):
    service = AdminCurrencyService(AdminCurrencyRepository(db))
    currencies, total = await service.get_currencies(page=page, size=size)
    
    currencies_resp = PaginatedResponse(
        items=currencies,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )

    return success(True, "Currencies fetched successfully", currencies_resp)

@router.get(
    "/currencies/{currency_id}",
    response_model=APIResponse[CurrencyResponse],
    tags=["Currencies"],
)
async def get_currency(
    currency_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user=Depends(get_current_user),  # noqa: B008
    account=Depends(require_account("admin", permission="currency.read")),  # noqa: B008
):
    service = AdminCurrencyService(AdminCurrencyRepository(db))
    currency = await service.get_currency(currency_id)
    return success(True, "Currency fetched successfully", currency)

@router.post(
    "/currencies",
    response_model=APIResponse[CurrencyResponse],
    tags=["Currencies"],
)
async def create_currency(
    payload: CurrencyCreate,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user=Depends(get_current_user),  # noqa: B008
    account=Depends(require_account("admin", permission="currency.create")),  # noqa: B008
):
    service = AdminCurrencyService(AdminCurrencyRepository(db))
    currency = await service.create_currency(payload)
    await service.repository.session.commit()
    return success(True, "Currency created successfully", currency)

@router.patch(
    "/currencies/{currency_id}",
    response_model=APIResponse[CurrencyResponse],
    tags=["Currencies"],
)
async def update_currency(
    currency_id: uuid.UUID,
    payload: CurrencyUpdate,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user=Depends(get_current_user),  # noqa: B008
    account=Depends(require_account("admin", permission="currency.update")),  # noqa: B008
):
    service = AdminCurrencyService(AdminCurrencyRepository(db))
    currency = await service.update_currency(currency_id, payload)
    await service.repository.session.commit()
    return success(True, "Currency updated successfully", currency)

@router.delete(
    "/currencies/{currency_id}",
    response_model=APIResponse[None],
    tags=["Currencies"],
)
async def delete_currency(
    currency_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user=Depends(get_current_user),  # noqa: B008
    account=Depends(require_account("admin", permission="currency.delete")),  # noqa: B008
):
    service = AdminCurrencyService(AdminCurrencyRepository(db))
    await service.delete_currency(currency_id)
    await service.repository.session.commit()
    return success(True, "Currency deleted successfully", None)

# ---------------------------------------------------------------------------
# Audit Trail Endpoints
# ---------------------------------------------------------------------------
@router.get(
    "/audit-trails/admin",
    response_model=APIResponse[PaginatedResponse[AuditTrailResponse]],
    tags=["Audit Trails"],
)
async def get_admin_audit_trails(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    organization_id: uuid.UUID = Query(None),
    organization_name: str = Query(None),
    organization_code: str = Query(None),
    username: str = Query(None),
    user_name: str = Query(None),
    user_email: str = Query(None),
    date: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user=Depends(get_current_user),  # noqa: B008
    account=Depends(require_account("admin", permission="audit_trails.read")),  # noqa: B008
):
    service = AdminAuditTrailService(AdminAuditTrailRepository(db))
    audit_trails, total = await service.get_admin_audit_trails(
        page=page,
        size=size,
        organization_id=organization_id,
        organization_name=organization_name,
        organization_code=organization_code,
        username=username,
        user_name=user_name,
        user_email=user_email,
        date=date,
        start_date=start_date,
        end_date=end_date,
    )
    
    audit_trails_resp = PaginatedResponse(
        items=audit_trails,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )

    return success(True, "Admin audit trails fetched successfully", audit_trails_resp)



# app/api/admin/videos.py
import uuid

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import require_admin
from app.db.base import get_db
from app.schemas.video import VideoUploadResponse
from app.services.video_service import UnsupportedSourceFormatError, VideoService
from app.workers.tasks import process_video

router = APIRouter(prefix="/admin/videos", tags=["admin-videos"])


@router.post("", status_code=202, response_model=VideoUploadResponse)
async def upload_video(
    title: str = Form(...),
    description: str | None = Form(None),
    price: float = Form(...),
    extension_price: float = Form(...),
    rental_days: int = Form(settings.DEFAULT_RENTAL_DAYS),
    extension_days: int = Form(settings.DEFAULT_EXTENSION_DAYS),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    tmp_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
    with open(tmp_path, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            out.write(chunk)

    service = VideoService(db)
    try:
        video = await service.create_from_upload(
            title=title, description=description, price=price, extension_price=extension_price,
            rental_days=rental_days, extension_days=extension_days,
            content_type=file.content_type, local_source_path=tmp_path, original_filename=file.filename,
        )
    except UnsupportedSourceFormatError:
        raise HTTPException(400, "Unsupported source format, upload mp4, mov, or mkv")

    await db.commit()
    process_video.delay(str(video.id))

    return VideoUploadResponse(id=video.id, status=video.status.value)