# File: app/main.py
# Purpose: FastAPI entrypoint — auth routes, BREAD calculation endpoints,
#          user profile/password routes, stats endpoint, and HTML page routes.
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, update as sa_update
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.database import Base, engine, get_db
from app.models.calculation import Calculation
from app.models.user import User
from app.schemas.calculation import (
    CalculationBase,
    CalculationResponse,
    CalculationStatsResponse,
    CalculationUpdate,
)
from app.schemas.token import TokenResponse
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    PasswordUpdate,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    import os
    if not os.getenv("TESTING", ""):
        Base.metadata.create_all(bind=engine)  # pragma: no cover
    yield


# OpenAPI tag groups shown in Swagger UI sidebar
_tags_metadata = [
    {
        "name": "auth",
        "description": (
            "Register and log in. "
            "**Use the `Authorize` button** (🔒) at the top of this page: "
            "enter your `username` and `password`, click *Authorize*, then all "
            "protected routes will automatically include your Bearer token."
        ),
    },
    {
        "name": "users",
        "description": "Read and update the current user's profile and password.",
    },
    {
        "name": "calculations",
        "description": (
            "Full BREAD operations on calculations plus an aggregate stats endpoint. "
            "Supported types: `addition`, `subtraction`, `multiplication`, "
            "`division`, `modulo`, `power`."
        ),
    },
    {
        "name": "health",
        "description": "Service liveness check.",
    },
    {
        "name": "web",
        "description": "HTML page routes served to the browser — not intended for API clients.",
    },
]

app = FastAPI(
    title="CalcApp API",
    description=(
        "## CalcApp — IS601 Final Project\n\n"
        "A production-quality calculator API with JWT authentication, "
        "full BREAD operations (six operation types), history stats, and "
        "profile management.\n\n"
        "### Quick start\n"
        "1. **Register** via `POST /auth/register`\n"
        "2. **Authorize** — click the 🔒 button, enter credentials, click *Authorize*\n"
        "3. **Try any protected route** — the Bearer token is added automatically\n"
    ),
    version="3.0.0",
    lifespan=lifespan,
    openapi_tags=_tags_metadata,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,      # hide schemas section by default
        "persistAuthorization": True,        # keep token after page refresh
        "tryItOutEnabled": True,             # open "Try it out" by default
        "displayRequestDuration": True,      # show response time
    },
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["health"])
def read_health():
    return {"status": "ok"}


# ── HTML page routes ──────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, tags=["web"])
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/login", response_class=HTMLResponse, tags=["web"])
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.get("/register", response_class=HTMLResponse, tags=["web"])
def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html")


@app.get("/dashboard", response_class=HTMLResponse, tags=["web"])
def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")


@app.get("/profile", response_class=HTMLResponse, tags=["web"])
def profile_page(request: Request):
    return templates.TemplateResponse(request, "profile.html")


@app.get("/dashboard/view/{calc_id}", response_class=HTMLResponse, tags=["web"])
def view_page(request: Request, calc_id: str):
    return templates.TemplateResponse(request, "view_calculation.html", {"calc_id": calc_id})


@app.get("/dashboard/edit/{calc_id}", response_class=HTMLResponse, tags=["web"])
def edit_page(request: Request, calc_id: str):
    return templates.TemplateResponse(request, "edit_calculation.html", {"calc_id": calc_id})


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
    summary="Register a new user",
)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """
    **Add a new user account.**

    - Validates password strength (uppercase, lowercase, digit, symbol).
    - Returns the created user (no token — redirect to login).
    """
    user_data = user_create.model_dump(exclude={"confirm_password"})
    try:
        user = User.register(db, user_data)
        db.commit()
        db.refresh(user)
        return user
    except ValueError as e:  # pragma: no cover
        db.rollback()  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # pragma: no cover


@app.post("/auth/login", response_model=TokenResponse, tags=["auth"], summary="Login (JSON)")
def login_json(user_login: UserLogin, db: Session = Depends(get_db)):
    """
    **Login with JSON body.**

    Returns access token, refresh token, and user info.
    """
    auth_result = User.authenticate(db, user_login.username, user_login.password)
    if auth_result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = auth_result["user"]
    db.commit()

    expires_at = auth_result.get("expires_at")
    if expires_at and expires_at.tzinfo is None:  # pragma: no cover
        expires_at = expires_at.replace(tzinfo=timezone.utc)  # pragma: no cover
    if not expires_at:  # pragma: no cover
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)  # pragma: no cover

    return TokenResponse(
        access_token=auth_result["access_token"],
        refresh_token=auth_result["refresh_token"],
        token_type="bearer",
        expires_at=expires_at,
        user_id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
    )


@app.post("/auth/token", tags=["auth"], summary="Login (form — Swagger UI)", response_model=dict)
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    auth_result = User.authenticate(db, form_data.username, form_data.password)
    if auth_result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    db.commit()
    return {"access_token": auth_result["access_token"], "token_type": "bearer"}


# ── User Profile ──────────────────────────────────────────────────────────────

@app.get(
    "/users/me",
    response_model=UserResponse,
    tags=["users"],
    summary="Get current user profile",
)
def get_me(current_user: User = Depends(get_current_active_user)):
    """Return the current user's profile info."""
    return current_user


@app.put(
    "/users/me",
    response_model=UserResponse,
    tags=["users"],
    summary="Update profile (name, email, username)",
)
def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    **Update** profile fields. Only fields you send are changed.

    - Raises 409 if new email/username conflicts with another account.
    """
    fields = update_data.model_dump(exclude_none=True)
    if not fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    # Check unique constraints
    from sqlalchemy import or_
    if "email" in fields or "username" in fields:
        filters = []
        if "email" in fields:
            filters.append(User.email == fields["email"])
        if "username" in fields:
            filters.append(User.username == fields["username"])

        conflict = (
            db.query(User)
            .filter(or_(*filters))
            .filter(User.id != current_user.id)
            .first()
        )
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email or username already taken",
            )

    current_user.update(**fields)
    db.commit()
    db.refresh(current_user)
    return current_user


@app.put(
    "/users/me/password",
    tags=["users"],
    summary="Change password",
)
def change_password(
    pwd_update: PasswordUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    **Change** the current user's password.

    - Verifies the current password before applying the change.
    """
    if not current_user.verify_password(pwd_update.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    current_user.password = User.hash_password(pwd_update.new_password)
    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Password updated successfully"}


# ── Stats ─────────────────────────────────────────────────────────────────────

@app.get(
    "/calculations/stats",
    response_model=CalculationStatsResponse,
    tags=["calculations"],
    summary="Aggregated stats for the current user",
)
def get_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    **Stats** — returns total count, counts per operation type,
    average result, and the 5 most recent calculations.
    """
    calcs = (
        db.query(Calculation)
        .filter(Calculation.user_id == current_user.id)
        .all()
    )

    by_type: dict = {}
    for c in calcs:
        by_type[c.type] = by_type.get(c.type, 0) + 1

    # Average operand count: how many input numbers the user typically uses per calc.
    # e.g. 2.0 means they mostly use two-number operations; 3.5 means multi-value.
    operand_counts = [len(c.inputs) for c in calcs if isinstance(c.inputs, list)]
    avg_operand_count: Optional[float] = (
        round(sum(operand_counts) / len(operand_counts), 2)
    ) if operand_counts else None

    last_5 = (
        db.query(Calculation)
        .filter(Calculation.user_id == current_user.id)
        .order_by(Calculation.created_at.desc())
        .limit(5)
        .all()
    )

    return CalculationStatsResponse(
        total_count=len(calcs),
        by_type=by_type,
        average_operand_count=avg_operand_count,
        last_5=last_5,
    )


# ── BREAD: Calculations ───────────────────────────────────────────────────────

@app.post(
    "/calculations",
    response_model=CalculationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["calculations"],
    summary="Add — create a new calculation",
)
def create_calculation(
    calculation_data: CalculationBase,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    **Add** a new calculation.

    - `type`: one of `addition`, `subtraction`, `multiplication`, `division`, `modulo`, `power`
    - `inputs`: list of ≥ 2 floats

    **Example:**
    ```json
    { "type": "addition", "inputs": [10, 5, 3] }
    ```
    """
    try:
        calc = Calculation.create(
            calculation_type=calculation_data.type,
            user_id=current_user.id,
            inputs=calculation_data.inputs,
        )
        calc.result = calc.get_result()
        db.add(calc)
        db.commit()
        db.refresh(calc)
        return calc
    except ValueError as e:  # pragma: no cover
        db.rollback()  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # pragma: no cover


@app.get(
    "/calculations",
    response_model=List[CalculationResponse],
    tags=["calculations"],
    summary="Browse — list all calculations for the current user",
)
def list_calculations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """**Browse** all calculations belonging to the logged-in user, newest first."""
    return (
        db.query(Calculation)
        .filter(Calculation.user_id == current_user.id)
        .order_by(Calculation.created_at.desc())
        .all()
    )


@app.get(
    "/calculations/{calc_id}",
    response_model=CalculationResponse,
    tags=["calculations"],
    summary="Read — get a single calculation by ID",
)
def get_calculation(
    calc_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """**Read** one calculation by UUID. Returns 404 if not found or owned by another user."""
    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid calculation ID format.",
        )

    calc = (
        db.query(Calculation)
        .filter(Calculation.id == calc_uuid, Calculation.user_id == current_user.id)
        .first()
    )
    if not calc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calculation not found.")
    return calc


@app.put(
    "/calculations/{calc_id}",
    response_model=CalculationResponse,
    tags=["calculations"],
    summary="Edit — update inputs/type and recompute result",
)
def update_calculation(
    calc_id: str,
    calculation_update: CalculationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """**Edit** an existing calculation. Result is automatically recomputed."""
    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid calculation ID format.",
        )

    calc = (
        db.query(Calculation)
        .filter(Calculation.id == calc_uuid, Calculation.user_id == current_user.id)
        .first()
    )
    if not calc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calculation not found.")

    new_type   = calculation_update.type   if calculation_update.type   is not None else calc.type
    new_inputs = calculation_update.inputs if calculation_update.inputs is not None else calc.inputs

    try:
        if new_type == "division" and any(float(v) == 0 for v in new_inputs[1:]):
            raise ValueError("Cannot divide by zero")
        if new_type == "modulo" and any(float(v) == 0 for v in new_inputs[1:]):
            raise ValueError("Cannot modulo by zero")

        tmp        = Calculation.create(new_type, current_user.id, new_inputs)
        new_result = tmp.get_result()

        db.execute(
            sa_update(Calculation)
            .where(Calculation.id == calc_uuid)
            .where(Calculation.user_id == current_user.id)
            .values(
                type=new_type,
                inputs=new_inputs,
                result=new_result,
                updated_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
        return db.query(Calculation).filter(Calculation.id == calc_uuid).first()
    except ValueError as e:  # pragma: no cover
        db.rollback()  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # pragma: no cover


@app.delete(
    "/calculations/{calc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["calculations"],
    summary="Delete — remove a calculation",
)
def delete_calculation(
    calc_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """**Delete** a calculation by UUID. Returns 204 on success."""
    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid calculation ID format.",
        )

    calc = (
        db.query(Calculation)
        .filter(Calculation.id == calc_uuid, Calculation.user_id == current_user.id)
        .first()
    )
    if not calc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calculation not found.")

    db.delete(calc)
    db.commit()
    return None


if __name__ == "__main__":  # pragma: no cover
    import uvicorn  # pragma: no cover
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="info")  # pragma: no cover
