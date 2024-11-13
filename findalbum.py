import discogs_client
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import paho.mqtt.client as mqtt
import re

# Replace these with your actual Discogs and Spotify credentials
DISCOGS_TOKEN = 'discogs'
SPOTIFY_CLIENT_ID = 'spotify'
SPOTIFY_CLIENT_SECRET = 'spotify'

# MQTT Broker details
MQTT_BROKER = 'mqttbroker'  # Replace with your broker's address
MQTT_PORT = 1883
MQTT_TOPIC = 'desiredtopic'
MQTT_USERNAME = 'mqtt'  # Replace with your MQTT username
MQTT_PASSWORD = 'mqtt'  # Replace with your MQTT password

# Initialize the Discogs client
d = discogs_client.Client('MyDiscogsApp/1.0', user_token=DISCOGS_TOKEN)

def clean_album_title(album_title, artist):
    """Remove artist name from the beginning of the album title if it appears there followed by ' - '."""
    if album_title.startswith(f"{artist} - "):
        album_title = album_title[len(artist) + 3:]  # Remove artist name and " - "
    return album_title

def get_album_from_discogs(upc_code):
    """Search for album information using Discogs API client based on a UPC code."""
    results = d.search(barcode=upc_code, type='release')
    
    # Check if any results were found
    if results:
        release = results[0]  # Get the first result
        album_title = release.title
        artist = release.artists[0].name if release.artists else "Unknown Artist"
        print(f"Found Album: {album_title} by {artist}")
        
        # Clean the album title
        album_title = clean_album_title(album_title, artist)
        
        return album_title, artist
    else:
        print("No album found for this UPC.")
        return None, None

def search_album_on_spotify(album_title, artist):
    """Search for an album on Spotify given the album title and artist, printing all results."""
    # Spotify Authentication
    auth_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
    sp = spotipy.Spotify(auth_manager=auth_manager)

    # Search for the album on Spotify
    query = f"album:{album_title} artist:{artist}"
    results = sp.search(q=query, type='album', limit=10)  # Increase limit if you want more results
    # Check if any results were found
    if results['albums']['items']:
        album = results['albums']['items'][0]
        album_name = album['name']
        spotify_url = album['external_urls']['spotify']
        print(f"Spotify Album Found: {album_name} - {spotify_url}")
        converted_url = re.sub(r'https://open\.spotify\.com/album/', 'spotify://userid/spotify:album:', spotify_url)

        return converted_url
    else:
        print("Album not found on Spotify.")
        return None

def publish_to_mqtt(message):
    """Publish the search results to an MQTT topic."""
    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD) 
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.publish(MQTT_TOPIC, message)
    client.disconnect()

def find_album_on_spotify(upc_code):
    album_title, artist = get_album_from_discogs(upc_code)
    if album_title and artist:
        search_results = search_album_on_spotify(album_title, artist)
        if search_results:
            message = search_results
            publish_to_mqtt(message)
            print("Published to MQTT:", message)
        else:
            print("No albums found on Spotify.")
    else:
        print("Album identification failed.")


if __name__ == "__main__":
    while True:
        upc_code = input("Enter UPC code (or 'exit' to quit): ")
        if upc_code.lower() == 'exit':
            break
        sanitized_string = re.sub(r'[^0-9]', '', upc_code)
        find_album_on_spotify(sanitized_string)
