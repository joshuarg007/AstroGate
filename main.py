from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import swisseph as swe
from datetime import datetime
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

# Zodiac signs and their date ranges (degree ranges)
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Zodiac degree ranges (each sign spans 30 degrees, from 0 to 360 degrees)
ZODIAC_RANGES = [
    (0, 30), (30, 60), (60, 90), (90, 120), (120, 150), (150, 180),
    (180, 210), (210, 240), (240, 270), (270, 300), (300, 330), (330, 360)
]

# Map planets to themes
PLANET_THEMES = {
    "Sun": "identity and vitality",
    "Moon": "emotions and intuition",
    "Mercury": "communication and thoughts",
    "Venus": "love and relationships",
    "Mars": "energy and action",
    "Jupiter": "growth and expansion",
    "Saturn": "responsibility and discipline",
    "Uranus": "change and innovation",
    "Neptune": "dreams and spirituality",
    "Pluto": "transformation and power"
}

# Calculate the position of planets
def calculate_planet_positions():
    now = datetime.now()
    jd = swe.julday(now.year, now.month, now.day)  # Calculate Julian day
    positions = {}

    for planet in [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS,
                   swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO]:
        result = swe.calc_ut(jd, planet)
        if len(result) >= 2:  # Ensure the result has at least two values
            planet_name = result[0]
            lon = result[1]  # Longitude of the planet
            positions[planet_name] = lon
            logger.info(f"{planet_name} is at longitude {lon}")
        else:
            logger.warning(f"Unexpected result from swisseph for planet {planet}: {result}")
    return positions

# Determine the zodiac sign of a planet based on its longitude
def get_zodiac_sign(longitude):
    longitude = longitude % 360  # Normalize longitude to be within 0-360 degrees
    for idx, (start, end) in enumerate(ZODIAC_RANGES):
        if start <= longitude < end:
            logger.info(f"Longitude {longitude} is in {ZODIAC_SIGNS[idx]}")
            return ZODIAC_SIGNS[idx]
    return "Unknown"

# Default themes for each zodiac sign
DEFAULT_THEMES = {
    "aries": "Today is a day of action. Take the initiative and push forward.",
    "taurus": "Patience will pay off today. Stay grounded and steady.",
    "gemini": "The winds of change are blowing. Embrace new ideas.",
    "cancer": "Nurturing energy surrounds you. Take care of yourself and others.",
    "leo": "Confidence is your key today. Shine brightly and lead the way.",
    "virgo": "Practicality will bring success. Focus on the details.",
    "libra": "Balance is important today. Seek harmony in all things.",
    "scorpio": "Intensity is your strength today. Dive deep and explore.",
    "sagittarius": "Adventure is calling. Step out of your comfort zone.",
    "capricorn": "Hard work will bring rewards. Stay disciplined and focused.",
    "aquarius": "Innovation is in the air. Think outside the box.",
    "pisces": "Dreams and intuition guide you. Trust your inner voice."
}

def generate_horoscope(sign, positions):
    themes = []
    # Convert the user's sign to lowercase for case-insensitive comparison
    sign = sign.lower()
    
    # Check each planet's position to determine if it's in the user's sign
    for planet, position in positions.items():
        planet_sign = get_zodiac_sign(position)
        logger.info(f"{planet} is in {planet_sign} with longitude {position}")
        
        # Only include planets that match the selected zodiac sign
        if planet_sign.lower() == sign:  # Compare in lowercase for consistency
            themes.append(f"{planet}: {PLANET_THEMES.get(planet, 'Unknown theme')}")
    
    # If no planets matched, use the default theme for that sign
    if not themes:
        themes.append(DEFAULT_THEMES.get(sign, "Today is a calm day. Reflect and recharge."))

    return f"{sign.capitalize()}: {', '.join(themes)}"

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
    logger.info(f"Received sign: {sign} and passphrase: {passphrase}")
    
    if passphrase and passphrase == SECRET_PASSPHRASE:
        logger.info("Redirecting to scrape form due to valid passphrase.")
        return RedirectResponse(url="/scrape-form", status_code=303)

    if sign:
        positions = calculate_planet_positions()
        horoscope_data = generate_horoscope(sign.capitalize(), positions)
        logger.info(f"Generated horoscope: {horoscope_data}")
        
        return templates.TemplateResponse("horoscope.html", {
            "request": request,
            "data": {"sign": sign, "horoscope": horoscope_data},
            "current_year": datetime.now().year
        })

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
