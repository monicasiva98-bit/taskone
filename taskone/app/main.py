# app/main.py

from fastapi import FastAPI
from app.database import get_connection
from app.models import create_users_table
from app.auth import router
from app.auth import router as auth_route
from app.auth import router as auth_router

#for svg
from fastapi.staticfiles import StaticFiles


app = FastAPI()
app.include_router(auth_router)

app = FastAPI()
#svg--
app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)


@app.on_event("startup")
def startup():
    conn = get_connection()
    cur = conn.cursor()
    create_users_table(cur)
    conn.commit()
    cur.close()
    conn.close()

app.include_router(router)


@app.get("/")
def root():
    return {"msg": "API running"}

# from fastapi import FastAPI


app = FastAPI()
app.include_router(auth_router)
