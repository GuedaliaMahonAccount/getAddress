import requests
import time

# Paramètres de la recherche
location = "31.0461,34.8516"  # Coordonnées pour Israël
radius = 50000  # Rayon en mètres pour la recherche
type_place = "restaurant"  # Type de lieu, exemple : "restaurant", "school", etc.
max_addresses = 50  # Nombre maximum d'adresses à récupérer

# API Key de Google
api_key = 'Your_Api_Key'

# Listes pour stocker les adresses et leurs coordonnées
addresses = []
latitudes = []
longitudes = []

# Fonction pour obtenir les lieux via l'API Google Places
def get_places(location, radius, place_type, api_key, token=None):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": location,
        "radius": radius,
        "type": place_type,
        "key": api_key
    }
    if token:
        params["pagetoken"] = token
    response = requests.get(url, params=params)
    result = response.json()
    return result

# Fonction pour obtenir les coordonnées d'une adresse
def get_coordinates(address, api_key):
    url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}'
    response = requests.get(url)
    result = response.json()
    if result['status'] == 'OK':
        lat = result['results'][0]['geometry']['location']['lat']
        lng = result['results'][0]['geometry']['location']['lng']
        return lat, lng
    else:
        return None, None

# Recherche des adresses et coordonnées
next_page_token = None
while len(addresses) < max_addresses:
    places_result = get_places(location, radius, type_place, api_key, next_page_token)

    if places_result.get('status') != 'OK':
        print("Erreur dans la requête de l'API Places:", places_result.get('status'))
        break

    for place in places_result.get("results", []):
        if len(addresses) >= max_addresses:
            break
        address = place.get("vicinity")
        if address:
            lat, lng = get_coordinates(address, api_key)
            if lat is not None and lng is not None:
                addresses.append(address)
                latitudes.append(lat)
                longitudes.append(lng)

    next_page_token = places_result.get("next_page_token")
    if not next_page_token:
        break
    time.sleep(2)

# Affichage des résultats dans le format requis
print("string[] addresses = new[] {")
print(",\n".join(f'    "{address}"' for address in addresses))
print("};\n")

print("float[] latitudes = new float[] {")
print(", ".join(f"{lat}f" for lat in latitudes))
print("};\n")

print("float[] longitudes = new float[] {")
print(", ".join(f"{lng}f" for lng in longitudes))
print("};")
