from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.database import get_connection
from app.schemas import RegisterRequest,VerifyOtpRequest
from passlib.context import CryptContext
import random

from fastapi.responses import Response

from app.config import SECRET_KEY, ALGORITHM
from app.utils import oauth2_scheme


#login part
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.schemas import LoginRequest

#svg upload

from fastapi import UploadFile, File
from pathlib import Path
import uuid


from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
# from jose import jwt, JWTError
# from datetime import datetime

# import uuid, base64
import  base64

# from app.config import SECRET_KEY, ALGORITHM
# from app.config import SECRET_KEY, ALGORITHM
from app.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)






router = APIRouter(prefix="/auth") #reauired

# ⬇️ ADD HERE (EXACTLY HERE)
BASE_DIR = Path(__file__).resolve().parent.parent
SVG_UPLOAD_DIR = BASE_DIR / "uploads" / "svg"
SVG_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)



# SECRET_KEY = "secretkey@11"
# ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7



pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


#register part-----------------------

@router.post("/register")
def register(data: RegisterRequest):
    conn = get_connection()
    cur = conn.cursor()

    # Check email
    cur.execute("SELECT id FROM users WHERE email=%s", (data.email,))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    email_otp = str(random.randint(100000, 999999))
    sms_otp = str(random.randint(100000, 999999))

    cur.execute("""
        INSERT INTO users (name, email, phone, password, email_otp, sms_otp)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        data.name,
        data.email,
        data.phone,
        hash_password(data.password),
        email_otp,
        sms_otp
    ))

    conn.commit()
    cur.close()
    conn.close()
    
    
    return {
        "message": "Registered successfully",
        "email": data.email
          
    }

#verify part-----------------------

@router.post("/verify-otp")
def verify_otp(data: VerifyOtpRequest):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT email_otp, sms_otp
        FROM users
        WHERE email = %s
    """, (data.email,))

    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="User not found")

    if user[0] != data.email_otp or user[1] != data.sms_otp:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid OTP")

    cur.execute("""
        UPDATE users
        SET is_verified = TRUE
        WHERE email = %s
    """, (data.email,))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "OTP verified successfully",
            }


#login--------------------

@router.post("/login")
def login(data: LoginRequest):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, password, is_verified
        FROM users
        WHERE email = %s
    """, (data.email,))

    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    user_id, hashed_password, is_verified = user

    if not is_verified:
        raise HTTPException(status_code=400, detail="User not verified")

    if not verify_password(data.password, hashed_password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    access_token = create_access_token({"sub": str(user_id)})
    refresh_token = create_refresh_token({"sub": str(user_id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
#to get accesstoken--------------

# @router.post("/refresh-token")
# def refresh_token(refresh_token: str):
#     try:
#         payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id = payload.get("sub")

#         if not user_id:
#             raise HTTPException(status_code=401, detail="Invalid refresh token")

#         new_access_token = create_access_token({"sub": user_id})
#         return {"access_token": new_access_token}

#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid refresh token")



#svg upload----------------------------

@router.post("/upload-svg")
def upload_svg(
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        created_by = payload.get("sub")
        if not created_by:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not file.filename.lower().endswith(".svg"):
        raise HTTPException(status_code=400, detail="Only SVG files are allowed")

    file_name = f"{uuid.uuid4()}.svg"
    file_path = SVG_UPLOAD_DIR / file_name

    file.file.seek(0)
    file_bytes = file.file.read()

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    file_base64 = base64.b64encode(file_bytes).decode("utf-8")

    conn = get_connection()
    cursor = conn.cursor()

    created_at = datetime.utcnow()
    file_type = "svg"

    cursor.execute(
        """
        INSERT INTO files (filename, filetype, file_base64, created_at, created_by)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (file_name, file_type, file_base64, created_at, created_by)
    )
    conn.commit()

    return {
        "filetype": file_type,
        "filename": file_name,
        "created_at": created_at,
        "created_by": created_by,
        "base64": file_base64
    }






#get----

# @router.get("/files")
# def get_my_files(token: str = Depends(oauth2_scheme)):
#     # 🔐 Decode JWT
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id = payload.get("sub")
#         if not user_id:
#             raise HTTPException(status_code=401, detail="Invalid token")
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid token")

#     conn = get_connection()
#     cursor = conn.cursor()

#     cursor.execute(
#         """
#         SELECT id, filename, filetype, file_base64, created_at
#         FROM files
#         WHERE created_by = %s
#         ORDER BY id DESC
#         """,
#         (user_id,)
#     )

#     rows = cursor.fetchall()

#     files = []
#     for row in rows:
#         files.append({
#             "id": row[0],
#             "filename": row[1],
#             "filetype": row[2],
#             "base64": row[3],
#             "created_at": row[4]
#         })

#     return {
#         "count": len(files),
#         "files": files
#     }


#decode

@router.get("/files/{file_id}/view")
def view_file(
    file_id: int,
    token: str = Depends(oauth2_scheme)
):
    # 🔐 Verify JWT
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT file_base64, filetype
        FROM files
        WHERE id = %s AND created_by = %s
        """,
        (file_id, user_id)
    )

    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="File not found")

    file_base64, filetype = row

    # 🔓 Decode Base64 → Bytes
    image_bytes = base64.b64decode(file_base64)

    # 🖼️ Detect media type
    if filetype == "svg":
        media_type = "image/svg+xml"
    elif filetype == "png":
        media_type = "image/png"
    elif filetype == "jpg" or filetype == "jpeg":
        media_type = "image/jpeg"
    else:
        media_type = "application/octet-stream"

    return Response(
        content=image_bytes,
        media_type=media_type
    )

