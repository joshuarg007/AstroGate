from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests
import logging

# Importing the passphrase from config.py
from config import SECRET_PASSPHRASE 


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_horoscope(sign: str):
    valid_signs = {
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
    }
    if sign not in valid_signs:
        return {"error": f"Invalid zodiac sign: {sign}"}

    url = "https://aztro.sameerkumar.website/"
    params = (("sign", sign), ("day", "today"))  # Use a tuple of tuples for params
    
    try:
        response = requests.post(url, params=params)  # Pass params as a tuple
        if response.status_code == 200:
            data = response.json()
            return {
                "date_range": data.get("date_range"),
                "description": data.get("description"),
                "current_date": data.get("current_date"),
                "sign": sign,
            }
        else:
            return {"error": f"Failed to fetch horoscope. Status code: {response.status_code}"}
    except Exception as e:
        return {"error": f"Error fetching horoscope: {str(e)}"}

# Homepage with passphrase form and zodiac dropdown (single form)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    zodiac_signs = [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra",
        "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
    ]
    return templates.TemplateResponse("home.html", {"request": request, "error": None, "zodiac_signs": zodiac_signs})

@app.post("/", response_class=HTMLResponse)
async def handle_form(request: Request, passphrase: str = Form(None), sign: str = Form(...)):
    if passphrase and passphrase == SECRET_PASSPHRASE:
        return RedirectResponse(url="/scrape-form", status_code=303)
    
    if sign:
        horoscope_data = get_horoscope(sign.lower())
        if "error" in horoscope_data:
            logger.error(f"Error fetching horoscope: {horoscope_data['error']}")
        return templates.TemplateResponse("horoscope.html", {"request": request, "data": horoscope_data})
    
    zodiac_signs = [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra",
        "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
    ]
    
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "error": "Please provide a valid passphrase or select a zodiac sign!", "zodiac_signs": zodiac_signs},
    )

# Scrape form page (only accessible after correct passphrase)
@app.get("/scrape-form", response_class=HTMLResponse)
async def scrape_form(request: Request):
    return templates.TemplateResponse("scrape_form.html", {"request": request})
