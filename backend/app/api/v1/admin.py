"""
backend/app/api/v1/admin.py

Admin-only management endpoints.

GET    /api/v1/admin/users           — list all users
POST   /api/v1/admin/users           — create a new user
PATCH  /api/v1/admin/users/{user_id} — update role / active status
GET    /api/v1/admin/audit-logs      — paginated audit event log
GET    /api/v1/admin/model-versions  — list trained model versions
POST   /api/v1/admin/model-versions/{version_id}/activate — activate a model
"""


import datetime
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import AdminUser
from app.core.security import hash_password
from app.database import get_db
from app.models.audit_event import AuditEvent
from app.models.model_version import ModelVersion
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import audit_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

@router.get("/users", response_model=List[UserRead])
def list_users(
    current_user: AdminUser,
    db: Session = Depends(get_db),
) -> list[User]:
    """List all user accounts."""
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    request: Request,
    current_user: AdminUser,
    db: Session = Depends(get_db),
) -> User:
    """Create a new user account."""
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    valid_roles = {"admin", "hr", "readonly"}
    if payload.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid role '{payload.role}'. Valid roles: {', '.join(sorted(valid_roles))}.",
        )

    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        is_active=True,
        is_admin=(payload.role == "admin"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    audit_service.log_event(
        db,
        event_type="admin.user_created",
        summary=f"User '{user.email}' created with role '{user.role}'",
        actor_id=current_user.id,
        actor_email=current_user.email,
        resource_type="user",
        resource_id=str(user.id),
        ip_address=request.client.host if request.client else None,
    )

    return user


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    current_user: AdminUser,
    db: Session = Depends(get_db),
) -> User:
    """Update a user's role or active status. Cannot demote yourself."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot modify your own account through this endpoint.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    update_data = payload.model_dump(exclude_unset=True)

    # --- Last-admin protection ---
    # If this user is currently an admin, check if this action would remove
    # the last active admin (via role change or deactivation).
    if user.role == "admin" and user.is_active:
        would_lose_admin = (
            ("role" in update_data and update_data["role"] != "admin")
            or ("is_active" in update_data and not update_data["is_active"])
        )
        if would_lose_admin:
            active_admin_count = db.query(User).filter(
                User.role == "admin",
                User.is_active == True,  # noqa: E712
            ).count()
            if active_admin_count <= 2:
                # 2 because current_user is also an admin; removing this one leaves 1
                # But if only this user + current_user are admins, removing this one is ok
                # We really need: would there be at least 1 active admin left?
                remaining = active_admin_count - 1  # after this change
                if remaining < 1:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            "Cannot demote or disable the last active administrator. "
                            "Promote another user to admin first."
                        ),
                    )

    if "role" in update_data:
        valid_roles = {"admin", "hr", "readonly"}
        if update_data["role"] not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid role. Valid: {', '.join(sorted(valid_roles))}.",
            )
        user.role = update_data["role"]
        user.is_admin = (update_data["role"] == "admin")

    if "full_name" in update_data:
        user.full_name = update_data["full_name"]
    if "is_active" in update_data:
        user.is_active = update_data["is_active"]

    db.commit()
    db.refresh(user)

    audit_service.log_event(
        db,
        event_type="admin.user_updated",
        summary=f"User '{user.email}' updated: {list(update_data.keys())}",
        actor_id=current_user.id,
        actor_email=current_user.email,
        resource_type="user",
        resource_id=str(user.id),
        ip_address=request.client.host if request.client else None,
    )

    return user


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

@router.get("/audit-logs")
def get_audit_logs(
    current_user: AdminUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    event_type: str | None = None,
    actor_email: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    """
    Paginated audit event log.
    Filterable by event_type prefix and actor_email.
    """
    q = db.query(AuditEvent).order_by(AuditEvent.occurred_at.desc())

    if event_type:
        q = q.filter(AuditEvent.event_type.startswith(event_type))
    if actor_email:
        q = q.filter(AuditEvent.actor_email == actor_email.lower())

    total = q.count()
    events = q.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "summary": e.summary,
                "actor_email": e.actor_email,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "outcome": e.outcome,
                "ip_address": e.ip_address,
                "occurred_at": e.occurred_at.isoformat() if e.occurred_at else None,
            }
            for e in events
        ],
    }


# ---------------------------------------------------------------------------
# Model version management
# ---------------------------------------------------------------------------

@router.get("/model-versions")
def list_model_versions(
    current_user: AdminUser,
    db: Session = Depends(get_db),
) -> list[dict]:
    """List all trained model versions with their evaluation metrics."""
    versions = db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).all()
    return [
        {
            "id": v.id,
            "version_tag": v.version_tag,
            "artifact_filename": v.artifact_filename,
            "description": v.description,
            "training_samples": v.training_samples,
            "test_accuracy": v.test_accuracy,
            "test_macro_f1": v.test_macro_f1,
            "test_weighted_f1": v.test_weighted_f1,
            "is_active": v.is_active,
            "deployed_at": v.deployed_at.isoformat() if v.deployed_at else None,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]


@router.post("/model-versions/{version_id}/activate", status_code=status.HTTP_200_OK)
def activate_model_version(
    version_id: int,
    request: Request,
    current_user: AdminUser,
    db: Session = Depends(get_db),
) -> dict:
    """
    Activate a specific model version. Deactivates all others.
    The classification service must be restarted or its cache cleared to pick up the change.
    """
    version = db.query(ModelVersion).filter(ModelVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model version not found.")

    # Deactivate all others
    db.query(ModelVersion).filter(ModelVersion.id != version_id).update({"is_active": False})

    version.is_active = True
    version.deployed_at = datetime.datetime.now(datetime.timezone.utc)
    version.deployed_by = current_user.id
    db.commit()

    # Invalidate the in-process model cache
    from app.services.classification_service import invalidate_model_cache
    invalidate_model_cache()

    audit_service.log_event(
        db,
        event_type="admin.model_activated",
        summary=f"Model version '{version.version_tag}' activated",
        actor_id=current_user.id,
        actor_email=current_user.email,
        resource_type="model_version",
        resource_id=str(version.id),
        ip_address=request.client.host if request.client else None,
    )

    return {
        "detail": f"Model version '{version.version_tag}' is now active.",
        "note": "Classification service cache cleared — next request will load new model.",
    }


# ---------------------------------------------------------------------------
# Model version auto-discovery (sync from disk)
# ---------------------------------------------------------------------------

@router.post("/model-versions/sync", status_code=status.HTTP_200_OK)
def sync_model_versions_from_disk(
    request: Request,
    current_user: AdminUser,
    db: Session = Depends(get_db),
) -> dict:
    """
    Scan the ml/artifacts/ directory for model metadata JSON files and register
    any unregistered model versions into the database.

    This is idempotent — already-registered versions are skipped.
    Auto-activates the newest model if no model is currently active.
    """
    import json
    from pathlib import Path
    from app.config import get_settings

    settings = get_settings()
    artifact_dir = Path(settings.model_dir)

    if not artifact_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact directory not found: {artifact_dir}",
        )

    registered = 0
    skipped = 0
    errors = []

    # Find all metadata JSON files (exclude dataset_report.json)
    meta_files = sorted(artifact_dir.glob("model_*_metadata.json"))

    for meta_file in meta_files:
        try:
            with meta_file.open("r", encoding="utf-8") as f:
                meta = json.load(f)

            version_tag = meta.get("version")
            if not version_tag:
                errors.append(f"{meta_file.name}: missing 'version' field")
                continue

            # Check if already registered
            existing = db.query(ModelVersion).filter(
                ModelVersion.version_tag == version_tag
            ).first()
            if existing:
                skipped += 1
                continue

            # Derive artifact filename from version tag
            artifact_filename = f"model_{version_tag}.joblib"
            artifact_path = artifact_dir / artifact_filename
            if not artifact_path.exists():
                errors.append(f"{meta_file.name}: artifact file not found: {artifact_filename}")
                continue

            version = ModelVersion(
                version_tag=version_tag,
                artifact_filename=artifact_filename,
                description=f"Auto-registered from disk. Model: {meta.get('model_name', 'Unknown')}",
                training_samples=meta.get("training_samples"),
                random_seed=meta.get("random_seed"),
                test_macro_f1=meta.get("test_macro_f1"),
                test_weighted_f1=meta.get("test_weighted_f1"),
                classification_report_json=meta.get("classification_report"),
                is_active=False,
            )
            db.add(version)
            db.flush()
            registered += 1

        except Exception as exc:
            errors.append(f"{meta_file.name}: {exc}")

    # Auto-activate the newest model if none is active
    active_count = db.query(ModelVersion).filter(ModelVersion.is_active == True).count()  # noqa: E712
    if active_count == 0 and registered > 0:
        newest = db.query(ModelVersion).order_by(ModelVersion.version_tag.desc()).first()
        if newest:
            newest.is_active = True
            newest.deployed_at = datetime.datetime.now(datetime.timezone.utc)
            newest.deployed_by = current_user.id

            from app.services.classification_service import invalidate_model_cache
            invalidate_model_cache()

    db.commit()

    audit_service.log_event(
        db,
        event_type="admin.model_sync",
        summary=f"Synced {registered} model(s) from disk",
        actor_id=current_user.id,
        actor_email=current_user.email,
        resource_type="model_version",
        resource_id=None,
        ip_address=request.client.host if request.client else None,
    )

    return {
        "registered": registered,
        "skipped": skipped,
        "errors": errors,
        "detail": f"Registered {registered} new model(s), skipped {skipped} already-registered.",
    }

