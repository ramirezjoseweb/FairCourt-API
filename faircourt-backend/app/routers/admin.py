from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.db import get_db
from app.deps import require_platform_admin
from app.models import (
    AuditLog,
    AuditVisibility,
    AuthOTP,
    Community,
    Facility,
    Household,
    User,
    UserRole,
    normalize_household_code,
)
from app.schemas import (
    AdminBasicPolicyUpdateIn,
    AdminFacilityOut,
    AdminFacilityWriteIn,
    AdminHouseholdCreateIn,
    AdminHouseholdOut,
    AdminHouseholdUpdateIn,
    AdminMeOut,
    AdminRequestOTPIn,
    AdminVerifyOTPIn,
    AuditLogOut,
    CommunityPolicyOut,
    CommunitySummaryOut,
    MessageOut,
    TokenOut,
)
from app.security import (
    create_access_token,
    gen_otp,
    hash_secret,
    utcnow,
    verify_secret,
)
from app.services.audit import log_admin_event
from app.services.policies import get_community_policy


router = APIRouter(prefix="/admin", tags=["admin"])
ADMIN_OTP_PURPOSE = "PLATFORM_ADMIN"


def _community_summary(db: Session, community: Community) -> dict:
    return {
        "id": community.id,
        "slug": community.slug,
        "name": community.name,
        "timezone": community.timezone,
        "is_active": community.is_active,
        "household_count": (
            db.query(Household)
            .filter(Household.community_id == community.id)
            .count()
        ),
        "facility_count": (
            db.query(Facility)
            .filter(Facility.community_id == community.id)
            .count()
        ),
    }


def _community_or_404(db: Session, community_id: int) -> Community:
    community = db.get(Community, community_id)
    if not community:
        raise HTTPException(status_code=404, detail="Comunidad no encontrada.")
    return community


def _facility_or_404(
    db: Session,
    community_id: int,
    facility_id: int,
) -> Facility:
    facility = (
        db.query(Facility)
        .filter(Facility.id == facility_id)
        .filter(Facility.community_id == community_id)
        .first()
    )
    if not facility:
        raise HTTPException(status_code=404, detail="Instalación no encontrada.")
    return facility


def _household_summary(household: Household) -> dict:
    return {
        "id": household.id,
        "community_id": household.community_id,
        "code": household.code,
        "is_active": household.is_active,
        "strikes": household.strikes,
        "suspended_until": household.suspended_until,
        "resident_email": household.user.email if household.user else None,
        "created_at": household.created_at,
    }


def _household_or_404(
    db: Session,
    community_id: int,
    household_id: int,
) -> Household:
    household = (
        db.query(Household)
        .options(joinedload(Household.user))
        .filter(Household.id == household_id)
        .filter(Household.community_id == community_id)
        .first()
    )
    if not household:
        raise HTTPException(status_code=404, detail="Vivienda no encontrada.")
    return household


@router.post("/auth/request-otp", response_model=MessageOut)
def request_admin_otp(
    payload: AdminRequestOTPIn,
    db: Session = Depends(get_db),
):
    email = str(payload.email).strip().lower()
    admin = (
        db.query(User)
        .filter(User.email == email)
        .filter(User.role == UserRole.PLATFORM_ADMIN.value)
        .filter(User.is_active.is_(True))
        .first()
    )

    # Respuesta neutra para no revelar qué correos tienen privilegios.
    message = "Si el correo está autorizado, se ha generado un código de acceso."
    if not admin:
        return {"message": message}

    otp = gen_otp(settings.OTP_LENGTH)
    expires_at = utcnow() + timedelta(minutes=settings.OTP_TTL_MINUTES)
    db.add(
        AuthOTP(
            community_id=None,
            email=email,
            purpose=ADMIN_OTP_PURPOSE,
            otp_hash=hash_secret(otp),
            expires_at=expires_at,
        )
    )
    log_admin_event(
        db,
        event="ADMIN_OTP_REQUESTED",
        admin_user_id=admin.id,
    )
    db.commit()

    if settings.DEV_PRINT_OTP:
        print(
            f"[DEV ADMIN OTP] Email={email} OTP={otp} "
            f"(expira {expires_at.isoformat()})"
        )
    return {"message": message}


@router.post("/auth/verify-otp", response_model=TokenOut)
def verify_admin_otp(
    payload: AdminVerifyOTPIn,
    db: Session = Depends(get_db),
):
    email = str(payload.email).strip().lower()
    admin = (
        db.query(User)
        .filter(User.email == email)
        .filter(User.role == UserRole.PLATFORM_ADMIN.value)
        .filter(User.is_active.is_(True))
        .first()
    )
    otp_row = (
        db.query(AuthOTP)
        .filter(AuthOTP.email == email)
        .filter(AuthOTP.community_id.is_(None))
        .filter(AuthOTP.purpose == ADMIN_OTP_PURPOSE)
        .order_by(AuthOTP.created_at.desc())
        .first()
    )
    if not admin or not otp_row:
        raise HTTPException(status_code=401, detail="Código de acceso no válido.")
    now = utcnow()
    if otp_row.used_at is not None:
        raise HTTPException(status_code=400, detail="OTP ya utilizado.")
    if otp_row.expires_at < now:
        raise HTTPException(status_code=400, detail="OTP expirado.")
    if not verify_secret(payload.otp, otp_row.otp_hash):
        raise HTTPException(status_code=401, detail="OTP incorrecto.")

    otp_row.used_at = now
    log_admin_event(
        db,
        event="ADMIN_LOGIN",
        admin_user_id=admin.id,
    )
    db.commit()
    token, expires_at = create_access_token(
        subject=admin.email,
        role=UserRole.PLATFORM_ADMIN.value,
    )
    return {"access_token": token, "expires_at": expires_at}


@router.get("/me", response_model=AdminMeOut)
def read_admin_me(
    admin: User = Depends(require_platform_admin),
):
    return {"id": admin.id, "email": admin.email, "role": admin.role}


@router.get("/communities", response_model=list[CommunitySummaryOut])
def list_admin_communities(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_platform_admin),
):
    communities = db.query(Community).order_by(Community.name.asc()).all()
    return [_community_summary(db, community) for community in communities]


@router.post(
    "/communities/{community_id}/select",
    response_model=CommunitySummaryOut,
)
def select_admin_community(
    community_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_platform_admin),
):
    community = db.get(Community, community_id)
    if not community:
        raise HTTPException(status_code=404, detail="Comunidad no encontrada.")
    log_admin_event(
        db,
        event="ADMIN_COMMUNITY_SELECTED",
        admin_user_id=admin.id,
        community_id=community.id,
        metadata={"community_slug": community.slug},
    )
    db.commit()
    return _community_summary(db, community)


@router.get(
    "/communities/{community_id}/households",
    response_model=list[AdminHouseholdOut],
)
def list_admin_households(
    community_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_platform_admin),
):
    _community_or_404(db, community_id)
    households = (
        db.query(Household)
        .options(joinedload(Household.user))
        .filter(Household.community_id == community_id)
        .order_by(Household.code_normalized.asc())
        .all()
    )
    return [_household_summary(household) for household in households]


@router.post(
    "/communities/{community_id}/households",
    response_model=AdminHouseholdOut,
    status_code=201,
)
def create_admin_household(
    community_id: int,
    payload: AdminHouseholdCreateIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_platform_admin),
):
    _community_or_404(db, community_id)
    normalized_code = normalize_household_code(payload.code)
    duplicate = (
        db.query(Household)
        .filter(Household.community_id == community_id)
        .filter(Household.code_normalized == normalized_code)
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="Ya existe una vivienda con ese código en la comunidad.",
        )

    household = Household(community_id=community_id, code=payload.code)
    db.add(household)
    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe una vivienda con ese código en la comunidad.",
        ) from error
    log_admin_event(
        db,
        event="ADMIN_HOUSEHOLD_CREATED",
        admin_user_id=admin.id,
        community_id=community_id,
        metadata={
            "household_id": household.id,
            "household_code": household.code,
        },
    )
    db.commit()
    db.refresh(household)
    return _household_summary(household)


@router.put(
    "/communities/{community_id}/households/{household_id}",
    response_model=AdminHouseholdOut,
)
def update_admin_household(
    community_id: int,
    household_id: int,
    payload: AdminHouseholdUpdateIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_platform_admin),
):
    _community_or_404(db, community_id)
    household = _household_or_404(db, community_id, household_id)
    normalized_code = normalize_household_code(payload.code)
    duplicate = (
        db.query(Household)
        .filter(Household.community_id == community_id)
        .filter(Household.code_normalized == normalized_code)
        .filter(Household.id != household.id)
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="Ya existe una vivienda con ese código en la comunidad.",
        )

    changes = {}
    if household.code != payload.code:
        changes["code"] = {"from": household.code, "to": payload.code}
        household.code = payload.code
    if household.is_active != payload.is_active:
        changes["is_active"] = {
            "from": household.is_active,
            "to": payload.is_active,
        }
        household.is_active = payload.is_active

    if changes:
        try:
            db.flush()
        except IntegrityError as error:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Ya existe una vivienda con ese código en la comunidad.",
            ) from error
        event = "ADMIN_HOUSEHOLD_UPDATED"
        if set(changes) == {"is_active"}:
            event = (
                "ADMIN_HOUSEHOLD_ACTIVATED"
                if household.is_active
                else "ADMIN_HOUSEHOLD_DEACTIVATED"
            )
        log_admin_event(
            db,
            event=event,
            admin_user_id=admin.id,
            community_id=community_id,
            metadata={
                "household_id": household.id,
                "changes": changes,
            },
        )
        db.commit()
        db.refresh(household)
    return _household_summary(household)


@router.get(
    "/communities/{community_id}/facilities",
    response_model=list[AdminFacilityOut],
)
def list_admin_facilities(
    community_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_platform_admin),
):
    _community_or_404(db, community_id)
    return (
        db.query(Facility)
        .filter(Facility.community_id == community_id)
        .order_by(Facility.priority.asc(), Facility.name.asc())
        .all()
    )


@router.post(
    "/communities/{community_id}/facilities",
    response_model=AdminFacilityOut,
    status_code=201,
)
def create_admin_facility(
    community_id: int,
    payload: AdminFacilityWriteIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_platform_admin),
):
    _community_or_404(db, community_id)
    duplicate = (
        db.query(Facility)
        .filter(Facility.community_id == community_id)
        .filter(Facility.slug == payload.slug)
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="Ya existe una instalación con ese código en la comunidad.",
        )

    facility = Facility(community_id=community_id, **payload.model_dump())
    db.add(facility)
    db.flush()
    log_admin_event(
        db,
        event="ADMIN_FACILITY_CREATED",
        admin_user_id=admin.id,
        community_id=community_id,
        metadata={
            "facility_id": facility.id,
            "facility_slug": facility.slug,
            "settings": payload.model_dump(),
        },
    )
    db.commit()
    db.refresh(facility)
    return facility


@router.put(
    "/communities/{community_id}/facilities/{facility_id}",
    response_model=AdminFacilityOut,
)
def update_admin_facility(
    community_id: int,
    facility_id: int,
    payload: AdminFacilityWriteIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_platform_admin),
):
    _community_or_404(db, community_id)
    facility = _facility_or_404(db, community_id, facility_id)
    duplicate = (
        db.query(Facility)
        .filter(Facility.community_id == community_id)
        .filter(Facility.slug == payload.slug)
        .filter(Facility.id != facility.id)
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="Ya existe una instalación con ese código en la comunidad.",
        )

    changes = {}
    for field, value in payload.model_dump().items():
        previous = getattr(facility, field)
        if previous != value:
            changes[field] = {"from": previous, "to": value}
            setattr(facility, field, value)

    if changes:
        event = "ADMIN_FACILITY_UPDATED"
        if set(changes) == {"is_active"}:
            event = (
                "ADMIN_FACILITY_ACTIVATED"
                if facility.is_active
                else "ADMIN_FACILITY_DEACTIVATED"
            )
        log_admin_event(
            db,
            event=event,
            admin_user_id=admin.id,
            community_id=community_id,
            metadata={
                "facility_id": facility.id,
                "facility_slug": facility.slug,
                "changes": changes,
            },
        )
        db.commit()
        db.refresh(facility)
    return facility


@router.get(
    "/communities/{community_id}/policy",
    response_model=CommunityPolicyOut,
)
def read_admin_community_policy(
    community_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_platform_admin),
):
    _community_or_404(db, community_id)
    return get_community_policy(db, community_id)


@router.put(
    "/communities/{community_id}/policy/basic",
    response_model=CommunityPolicyOut,
)
def update_admin_basic_policy(
    community_id: int,
    payload: AdminBasicPolicyUpdateIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_platform_admin),
):
    _community_or_404(db, community_id)
    policy = get_community_policy(db, community_id)
    changes = {}
    for field, value in payload.model_dump().items():
        previous = getattr(policy, field)
        if previous != value:
            changes[field] = {"from": previous, "to": value}
            setattr(policy, field, value)

    if changes:
        log_admin_event(
            db,
            event="ADMIN_BASIC_POLICY_UPDATED",
            admin_user_id=admin.id,
            community_id=community_id,
            metadata={"changes": changes},
        )
        db.commit()
        db.refresh(policy)
    return policy


@router.get(
    "/communities/{community_id}/audit",
    response_model=list[AuditLogOut],
)
def read_private_admin_audit(
    community_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_platform_admin),
):
    _community_or_404(db, community_id)
    return (
        db.query(AuditLog)
        .filter(AuditLog.community_id == community_id)
        .filter(AuditLog.visibility == AuditVisibility.ADMIN.value)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .all()
    )
