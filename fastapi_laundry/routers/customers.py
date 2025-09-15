from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..schemas import CustomerCreate, CustomerOut
from ..deps import get_current_user
from ..database import get_session, Base
from sqlalchemy.orm import Session
from fastapi import Depends
from fastapi import APIRouter
router = APIRouter()

# automapped class names depend on table names. Commonly Django tables look like "laundry_customer"
CustomerTable = getattr(Base.classes, "laundry_customer")

def get_db():
    yield from get_session()

@router.get("/", response_model=List[CustomerOut])
def list_customers(user=Depends(get_current_user), db: Session = Depends(get_db)):
    # scoped by organization if present
    qs = db.query(CustomerTable)
    if hasattr(user, "organization") and user.organization:
        qs = qs.filter(CustomerTable.organization_id == user.organization.id)
    if hasattr(user, "staff") and getattr(user, "staff", None) and user.staff.branch:
        qs = qs.filter(CustomerTable.branch_id == user.staff.branch.id)
    items = qs.order_by(CustomerTable.id.desc()).all()
    # convert rows (SQLAlchemy automap returns objects) to Pydantic via ORM mode
    return items

@router.post("/", response_model=CustomerOut)
def create_customer(payload: CustomerCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    new = CustomerTable()
    new.name = payload.name
    new.phone = payload.phone
    new.email = payload.email
    # assign branch if user is staff
    if hasattr(user, "staff") and getattr(user, "staff", None):
        new.branch_id = user.staff.branch.id
    if hasattr(user, "organization") and user.organization:
        new.organization_id = user.organization.id

    db.add(new)
    db.commit()
    db.refresh(new)
    return new
