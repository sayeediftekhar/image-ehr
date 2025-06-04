from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import logging
import requests

from app.services.auth import authenticate_user, log_login_attempt, update_user_last_login

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

def get_location_from_ip(ip):
    try:
        url = f"http://ip-api.com/json/{ip}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "success":
            return {
                "country": data.get("country"),
                "region": data.get("regionName"),
                "city": data.get("city"),
                "lat": data.get("lat"),
                "lon": data.get("lon"),
                "isp": data.get("isp"),
            }
        else:
            logger.warning(f"GeoIP API error: {data.get('message')}")
            return None
    except Exception as e:
        logger.error(f"GeoIP API request failed: {e}")
        return None

@router.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    logger.info(f"🚀 LOGIN ATTEMPT: username='{username}'")
    client_host = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")
    location_data = get_location_from_ip(client_host)
    logger.info(f"User IP: {client_host}, Location: {location_data}")

    if not username or not password:
        log_login_attempt(username, client_host, location_data, False, user_agent)
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Username and password are required"
        })

    user = authenticate_user(username, password)

    if user:
        log_login_attempt(username, client_host, location_data, True, user_agent)
        update_user_last_login(username, client_host, location_data)
        request.session["user"] = user
        return RedirectResponse(url="/dashboard", status_code=302)
    else:
        log_login_attempt(username, client_host, location_data, False, user_agent)
        logger.warning(f"❌ Login failed for {username}")
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password"
        })

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login")