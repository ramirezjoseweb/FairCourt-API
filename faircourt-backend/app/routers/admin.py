from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

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
)
from app.schemas import (
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
    "/communities/{community_id}/policy",
    response_model=CommunityPolicyOut,
)
def read_admin_community_policy(
    community_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_platform_admin),
):
    if not db.get(Community, community_id):
        raise HTTPException(status_code=404, detail="Comunidad no encontrada.")
    return get_community_policy(db, community_id)


@router.get(
    "/communities/{community_id}/audit",
    response_model=list[AuditLogOut],
)
def read_private_admin_audit(
    community_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_platform_admin),
):
    if not db.get(Community, community_id):
        raise HTTPException(status_code=404, detail="Comunidad no encontrada.")
    return (
        db.query(AuditLog)
        .filter(AuditLog.community_id == community_id)
        .filter(AuditLog.visibility == AuditVisibility.ADMIN.value)
        .order_by(AuditLog.created_at.desc())
        .all()
    )
