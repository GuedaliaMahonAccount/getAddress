import requests
import time
from dotenv import load_dotenv
import os
import re

# Load environment variables
load_dotenv()
api_key = os.getenv('GOOGLE_MAP_API_KEY')

if not api_key:
    raise ValueError("API key not found. Ensure .env is configured correctly.")

# Parameters for search
location = "32.0853,34.7818"  # Coordonnées centrales d'Israël
radius = 150000  # Augmenté à 150km
type_place = "establishment"  # Type générique pour avoir plus de résultats
max_addresses = 50

# Lists for storing data
addresses = []
latitudes = []
longitudes = []

def get_places(location, radius, place_type, api_key, token=None):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": location,
        "radius": radius,
        "type": place_type,
        "key": api_key,
        "language": "he"  # Ajouter le paramètre de langue pour avoir plus d'adresses en hébreu
    }
    if token:
        params["pagetoken"] = token
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error in API request: {e}")
        return None

def get_coordinates(address, api_key):
    url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}&language=he'
    try:
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        if result['status'] == 'OK':
            location = result['results'][0]['geometry']['location']
            return location['lat'], location['lng']
    except requests.exceptions.RequestException as e:
        print(f"Error in geocoding request: {e}")
    return None, None

def extract_address_components(raw_address, place_name):
    hebrew_regex = re.compile(r"[\u0590-\u05FF\s]+")
    number_regex = re.compile(r"\b\d+\b")

    if not raw_address:
        return None

    # Recherche du texte en hébreu et du numéro
    street_hebrew = hebrew_regex.search(raw_address)
    number = number_regex.search(raw_address)

    # Si pas de numéro, utiliser 1 comme numéro par défaut
    street_number = number.group(0) if number else "1"

    # Si pas de rue en hébreu, essayer d'utiliser le raw_address
    if not street_hebrew:
        return None

    street = street_hebrew.group(0).strip()

    # Traitement du nom de lieu
    if hebrew_regex.search(place_name):
        # Si le nom est en hébreu, extraire la ville de l'adresse
        location_parts = raw_address.split(',')
        if len(location_parts) > 1:
            location_name = location_parts[-1].strip()
            # Si la ville est en hébreu, utiliser une ville par défaut
            if hebrew_regex.search(location_name):
                location_name = "Israel"
        else:
            location_name = "Israel"
    else:
        location_name = place_name.split(" - ")[0].strip()
        # Garder les caractères anglais et quelques caractères spéciaux
        location_name = re.sub(r'[^a-zA-Z\s\-\']', '', location_name).strip()
        if not location_name:
            location_name = "Israel"

    if street and street_number and location_name:
        return f"{street}, {street_number}, {location_name}"
    return None

# Main search loop
next_page_token = None
retry_count = 0
max_retries = 3

while len(addresses) < max_addresses and retry_count < max_retries:
    places_result = get_places(location, radius, type_place, api_key, next_page_token)

    if not places_result or places_result.get('status') != 'OK':
        print("Error with Places API request:", places_result.get('status') if places_result else "No response")
        retry_count += 1
        continue

    for place in places_result.get("results", []):
        if len(addresses) >= max_addresses:
            break

        raw_address = place.get("vicinity")
        place_name = place.get("name")

        if raw_address:
            formatted_address = extract_address_components(raw_address, place_name)
            if formatted_address and formatted_address.count(',') == 2:
                lat, lng = get_coordinates(formatted_address, api_key)
                if lat is not None and lng is not None:
                    addresses.append(formatted_address)
                    latitudes.append(lat)
                    longitudes.append(lng)

    next_page_token = places_result.get("next_page_token")
    if not next_page_token:
        # Si on n'a pas assez d'adresses, on change légèrement la location et on recommence
        if len(addresses) < max_addresses:
            location = f"{float(location.split(',')[0]) + 0.1},{float(location.split(',')[1]) + 0.1}"
            retry_count += 1
        else:
            break
    time.sleep(2)

# Print results
print("string[] addresses = {")
print(",\n".join(f'    "{address}"' for address in addresses))
print("};\n")

print("float[] latitudes = {")
print(", ".join(f"{lat}f" for lat in latitudes))
print("};\n")

print("float[] longitudes = {")
print(", ".join(f"{lng}f" for lng in longitudes))
print("};")