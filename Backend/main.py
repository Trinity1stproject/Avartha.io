# main.py

from fastapi import FastAPI, Form, HTTPException, Request, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from email_validator import validate_email, EmailNotValidError
from app.db_operations import register_user, authenticate_user
from app.image_processing import ImageHandler
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# Define the directory paths
templates_dir = os.path.join(os.path.dirname(__file__), "backend")
static_dir = os.path.join(templates_dir, "static")

# Setup Jinja2 for templating
templates = Jinja2Templates(directory="templates")

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    if authenticate_user(email, password):
        response = RedirectResponse(url="/home")
        response.status_code = 303
        return response
    else:
        raise HTTPException(status_code=400, detail="Invalid email or password. Please try again.")

@app.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register_post(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        validate_email(email)
    except EmailNotValidError as e:
        return templates.TemplateResponse("register.html", {"request": request, "message": str(e)})

    if not any(char.isdigit() for char in password):
        return templates.TemplateResponse("register.html", {"request": request, "message": "Password must contain at least one digit."})
    if not any(char.isupper() for char in password):
        return templates.TemplateResponse("register.html", {"request": request, "message": "Password must contain at least one uppercase letter."})

    try:
        register_user(email, password)
        response = RedirectResponse(url="/home")
        response.status_code = 303
        return response
    except Exception as e:
        return templates.TemplateResponse("register.html", {"request": request, "message": str(e)})

@app.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

# Initialize image handler
handler = ImageHandler()

@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    try:
        result = await handler.upload_image(file)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8005)
