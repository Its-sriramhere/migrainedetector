from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..api.deps import get_current_user
from ..core.security import utcnow
from ..db.session import get_db
from ..models import Device, User
from ..schemas import DeviceOut, DeviceRegisterRequest

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.post("/heartbeat", response_model=DeviceOut)
def heartbeat(
    body: DeviceRegisterRequest,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a device as alive. Called periodically by the Raspberry Pi."""
    device = (
        db.execute(
            select(Device).where(
                Device.device_identifier == body.device_identifier,
                Device.user_id == current.id,
            )
        )
        .scalars()
        .first()
    )
    if device is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Device not registered for this user")
    device.last_seen = utcnow()
    device.status = "online"
    db.commit()
    db.refresh(device)
    return device


@router.post("/register", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
def register_device(
    body: DeviceRegisterRequest,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    device = db.execute(
        select(Device).where(Device.device_identifier == body.device_identifier)
    ).scalar_one_or_none()
    if device:
        device.user_id = current.id
        device.status = "online"
        device.last_seen = utcnow()
    else:
        device = Device(
            user_id=current.id,
            device_identifier=body.device_identifier,
            device_name=body.device_name,
            status="online",
            last_seen=utcnow(),
        )
        db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.get("", response_model=list[DeviceOut])
def list_devices(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return db.execute(
        select(Device).where(Device.user_id == current.id)
    ).scalars().all()


@router.get("/{device_id}/status", response_model=DeviceOut)
def device_status(
    device_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    device = db.execute(
        select(Device).where(Device.id == device_id, Device.user_id == current.id)
    ).scalar_one_or_none()
    if device is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Device not found")
    return device