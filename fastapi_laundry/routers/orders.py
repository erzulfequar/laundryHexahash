from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..schemas import OrderCreate
from ..deps import get_current_user
from ..database import get_session, Base
from sqlalchemy.orm import Session
from fastapi import Depends
import datetime
from fastapi import APIRouter

router = APIRouter()

OrderTable = getattr(Base.classes, "laundry_order")
OrderItemTable = getattr(Base.classes, "laundry_orderitem")
CustomerTable = getattr(Base.classes, "laundry_customer")

def get_db():
    yield from get_session()

@router.get("/")
def list_orders(user=Depends(get_current_user), db: Session = Depends(get_db)):
    qs = db.query(OrderTable)
    if hasattr(user, "organization") and user.organization:
        qs = qs.filter(OrderTable.organization_id == user.organization.id)
    if hasattr(user, "staff") and getattr(user, "staff", None):
        qs = qs.filter(OrderTable.branch_id == user.staff.branch.id)
    items = qs.order_by(OrderTable.id.desc()).all()
    return items

@router.post("/")
def create_order(payload: OrderCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    # Validate customer
    customer = db.query(CustomerTable).filter(CustomerTable.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    new_order = OrderTable()
    new_order.customer_id = payload.customer_id
    new_order.weight_kg = payload.weight
    # build services_items text as in save_order
    lines = []
    for it in payload.ironing_items:
        if it.article.strip().lower() == "washing":
            continue
        label = f"{it.article} {'(With Wash)' if it.with_wash else '(Without Wash)'} × {it.qty}"
        lines.append(f"Ironing: {label}")
    for it in payload.dryclean_items:
        label = f"{it.article} × {it.qty}"
        lines.append(f"Dry Clean: {label}")
    new_order.services_items = "\n".join(lines)
    new_order.total_amount = payload.total_amount
    new_order.status = payload.status or "Pending"
    # set branch/org from user if present
    if hasattr(user, "organization") and user.organization:
        new_order.organization_id = user.organization.id
    if hasattr(user, "staff") and getattr(user, "staff", None):
        new_order.branch_id = user.staff.branch.id

    new_order.created_at = datetime.datetime.utcnow()

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # add items
    for it in payload.ironing_items:
        if it.article.strip().lower() == "washing":
            continue
        item = OrderItemTable()
        item.order_id = new_order.id
        item.service_type = "Ironing"
        item.item_name = it.article
        item.with_wash = bool(it.with_wash)
        item.quantity = int(it.qty)
        db.add(item)
    for it in payload.dryclean_items:
        item = OrderItemTable()
        item.order_id = new_order.id
        item.service_type = "Dryclean"
        item.item_name = it.article
        item.with_wash = False
        item.quantity = int(it.qty)
        db.add(item)
    db.commit()
    return {"success": True, "order_id": new_order.id}

@router.put("/{order_id}/status")
def update_status(order_id: int, status: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(OrderTable).filter(OrderTable.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # permission checks similar to Django
    if hasattr(user, "organization") and user.organization:
        if order.organization_id != user.organization.id:
            raise HTTPException(status_code=403, detail="Forbidden")
    if hasattr(user, "staff") and getattr(user, "staff", None):
        if order.branch_id != user.staff.branch.id:
            raise HTTPException(status_code=403, detail="Forbidden")
    if status not in ["Pending", "Completed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    order.status = status
    db.commit()
    return {"success": True}
