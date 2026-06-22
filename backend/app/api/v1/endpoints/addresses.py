from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.address import Address
from app.schemas.address import AddressCreate, AddressUpdate, AddressResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/users/me/addresses", tags=["addresses"])


@router.get("", response_model=list[AddressResponse], summary="List user addresses")
def list_addresses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Address)
        .filter(Address.user_id == current_user.id)
        .all()
    )


@router.post("", response_model=AddressResponse, status_code=status.HTTP_201_CREATED, summary="Create a new address")
def create_address(
    address_in: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if address_in.is_default:
        _unset_default(current_user.id, db)

    address = Address(**address_in.model_dump(), user_id=current_user.id)
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


@router.put("/{address_id}", response_model=AddressResponse, summary="Update an address")
def update_address(
    address_id: int,
    address_in: AddressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    address = _get_user_address(address_id, current_user.id, db)

    update_data = address_in.model_dump(exclude_unset=True)

    if update_data.get("is_default"):
        _unset_default(current_user.id, db)

    for field, value in update_data.items():
        setattr(address, field, value)

    db.commit()
    db.refresh(address)
    return address


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an address")
def delete_address(
    address_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    address = _get_user_address(address_id, current_user.id, db)
    db.delete(address)
    db.commit()


@router.put("/{address_id}/default", response_model=AddressResponse, summary="Set address as default")
def set_default_address(
    address_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    address = _get_user_address(address_id, current_user.id, db)
    _unset_default(current_user.id, db)
    address.is_default = True
    db.commit()
    db.refresh(address)
    return address


def _get_user_address(address_id: int, user_id: int, db: Session) -> Address:
    address = (
        db.query(Address)
        .filter(Address.id == address_id, Address.user_id == user_id)
        .first()
    )
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )
    return address


def _unset_default(user_id: int, db: Session) -> None:
    db.query(Address).filter(
        Address.user_id == user_id, Address.is_default.is_(True)
    ).update({"is_default": False})
    db.flush()
