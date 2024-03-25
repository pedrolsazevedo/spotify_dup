import os
import requests
import base64
from datetime import datetime, timedelta
import json
from urllib.parse import urlparse, parse_qs

CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')


def get_access_token(client_id, client_secret):
    client_creds = f"{client_id}:{client_secret}"
    client_creds_b64 = base64.b64encode(client_creds.encode())

    token_url = "https://accounts.spotify.com/api/token"

    # Token request headers
    token_headers = {
        "Authorization": f"Basic {client_creds_b64.decode()}"
    }

    # Token request body
    token_data = {
        "grant_type": "client_credentials"
    }

    # Make token request
    token_response = requests.post(token_url, data=token_data, headers=token_headers)
    
    # Check if response is successful
    if token_response.status_code in range(200, 299):
        # Extract access token from response
        access_token = token_response.json()['access_token']
        # Get token expiration time
        expires_in = token_response.json()['expires_in']
        # Calculate token expiration time
        now = datetime.now()
        expires = now + timedelta(seconds=expires_in)
        return access_token, expires
    else:
        raise Exception("Unable to fetch access token")

# Function to fetch all tracks using access token
def fetch_all_tracks(access_token, playlist_id, limit=100):
    # Initialize an empty list to store all tracks
    all_tracks = []

    # Spotify Playlist Tracks URL
    playlist_tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

    # Playlist tracks request headers
    playlist_tracks_headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Initialize offset to 0
    offset = 0

    while True:
        # Playlist tracks request parameters
        playlist_tracks_params = {
            "limit": limit,
            "offset": offset
        }

        # Make playlist tracks request
        playlist_tracks_response = requests.get(playlist_tracks_url, headers=playlist_tracks_headers, params=playlist_tracks_params)

        if playlist_tracks_response.status_code == 200:
            # Extract tracks from the response
            tracks_data = playlist_tracks_response.json()

            # Append tracks to the list
            all_tracks.extend(tracks_data['items'])

            # Increment the offset
            offset += limit

            # Check if all tracks have been retrieved
            if len(tracks_data['items']) < limit:
                break
        else:
            print("Error:", playlist_tracks_response.text)
            raise Exception("Unable to fetch playlist tracks")

    return all_tracks

# Function to format playlist output
def format_playlist(all_tracks):
    formatted_tracks = []
    for track in all_tracks:
        track_name = track['track']['name']
        artist_name = track['track']['artists'][0]['name']
        added_by = track['added_by']['id'] if 'added_by' in track else 'Unknown'  # Adjusted this line
        formatted_tracks.append({
            'name': track_name,
            'artist': artist_name,
            'added_by': added_by
        })
    return formatted_tracks

# Function to find duplicate tracks
def find_duplicates(formatted_playlist):
    duplicates = {}
    for track in formatted_playlist:
        key = (track['name'], track['artist'])
        if key in duplicates:
            # If the track is already in duplicates, check if the added_by field is different
            if track['added_by'] not in duplicates[key]:
                duplicates[key].append(track['added_by'])
        else:
            duplicates[key] = [track['added_by']]
    # Filter out tracks without duplicates
    return {key: value for key, value in duplicates.items() if len(value) > 1}

# Function to generate full JSON
def generate_full_json(playlist_id, formatted_playlist, duplicates):
    # Convert tuples to strings for duplicate keys
    str_duplicates = {str(key): value for key, value in duplicates.items()}
    full_json = {
        'playlist_name': playlist_id,
        'tracks': formatted_playlist,
        'duplicates': str_duplicates
    }
    return full_json

# Function to write full JSON to a JSON file
def write_full_json_to_file(full_json, file_path):
    with open(file_path, 'w') as file:
        json.dump(full_json, file, indent=4)

# Function to get username from user ID
def get_username(user_id, access_token):
    # Spotify User Profile URL
    user_profile_url = f"https://api.spotify.com/v1/users/{user_id}"

    # User profile request headers
    user_profile_headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Make user profile request
    user_profile_response = requests.get(user_profile_url, headers=user_profile_headers)

    # Check if response is successful
    if user_profile_response.status_code == 200:
        # Extract username from response
        user_profile_data = user_profile_response.json()
        username = user_profile_data['display_name'] if 'display_name' in user_profile_data else 'Unknown'
        return username
    else:
        print("Error:", user_profile_response.text)
        raise Exception("Unable to fetch user profile")

# Main function
def main():
    # Get access token
    access_token, expires = get_access_token(CLIENT_ID, CLIENT_SECRET)
    print(f"Access Token: {access_token}")
    print(f"Token Expires at: {expires}")

    # Get playlist ID from URL
    playlist_url = input("Enter Spotify playlist URL: ")
    parsed_url = urlparse(playlist_url)
    path_segments = parsed_url.path.split('/')
    playlist_id = path_segments[-1]  # Extract the last segment of the path

    # Fetch all tracks
    all_tracks_data = fetch_all_tracks(access_token, playlist_id, limit=50)

    # Format playlist
    formatted_playlist = format_playlist(all_tracks_data)

    # Find duplicates
    duplicates = find_duplicates(formatted_playlist)

    # Print duplicated tracks
    print("Duplicated Tracks:")
    for key, users in duplicates.items():
        track_name, artist_name = key
        added_by_users = [get_username(user_id, access_token) for user_id in users]
        added_by = ", ".join(added_by_users)
        print(f"Track: {track_name}, Artist: {artist_name}, Added by: {added_by}")

    # Generate full JSON
    full_json = generate_full_json(playlist_id, formatted_playlist, duplicates)

    # Write full JSON to file
    json_file_path = 'playlist.json'
    write_full_json_to_file(full_json, json_file_path)
    print(f"Full JSON written to JSON file: {json_file_path}")

if __name__ == "__main__":
    main()
