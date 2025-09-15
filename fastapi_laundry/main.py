import os
import django

# Ye line Django ko bata rahi hai ki settings kaunse use karne hai
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laundry_pos.settings")
django.setup()

from laundry.models import Customer  # replace with your app name

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi_laundry.routers import auth, customers, orders
import fastapi_laundry.django_setup
from fastapi_laundry.routers.customers import router as customers_router

from . import django_setup

app = FastAPI(title="Laundry FastAPI (mobile)")

# Allow CORS for Android / development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])

app.include_router(customers_router, prefix="/customers", tags=["customers"])

app.include_router(orders.router, prefix="/orders", tags=["orders"])


@app.get("/")
def root():
    return {"message": "Laundry FastAPI (Auth, Customers, Orders)"}
