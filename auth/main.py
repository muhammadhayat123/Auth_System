from fastapi import FastAPI, Request, Form, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from database import SessionLocal, engine
from models import User, Base  # <-- Base is imported

app = FastAPI()

# Setup templates
templates = Jinja2Templates(directory="templates")

# Add session middleware (for login session handling)
app.add_middleware(SessionMiddleware, secret_key="your-super-secret-key")

# Create tables
Base.metadata.create_all(bind=engine)

# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
# ----------------- Registration -----------------
@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register_user(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    new_user = User(name=name, email=email, password=password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return RedirectResponse(url="/login", status_code=303)

# ----------------- Login -----------------
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
async def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email, User.password == password).first()

    if user:
        request.session["user"] = user.email  # Save logged-in user in session
        return RedirectResponse(url="/student", status_code=303)
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials!"})

# ----------------- Student Page (Protected) -----------------
@app.get("/student", response_class=HTMLResponse)
async def student_page(request: Request):
    user_email = request.session.get("user")

    if not user_email:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse("student.html", {"request": request, "user_email": user_email})

# ----------------- Logout -----------------
@app.api_route("/logout", methods=["GET", "POST"])
async def logout(request: Request):
    request.session.clear()  # Clear session
    return templates.TemplateResponse("bye.html", {"request": request})
