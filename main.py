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

    token_headers = {
        "Authorization": f"Basic {client_creds_b64.decode()}"
    }

    token_data = {
        "grant_type": "client_credentials"
    }

    token_response = requests.post(token_url, data=token_data, headers=token_headers)
    
    if token_response.status_code in range(200, 299):
        access_token = token_response.json()['access_token']
        expires_in = token_response.json()['expires_in']
        now = datetime.now()
        expires = now + timedelta(seconds=expires_in)
        return access_token, expires
    else:
        raise Exception("Unable to fetch access token")

def fetch_all_tracks(access_token, playlist_id, limit=100):
    all_tracks = []

    playlist_tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

    playlist_tracks_headers = {
        "Authorization": f"Bearer {access_token}"
    }

    offset = 0

    while True:
        playlist_tracks_params = {
            "limit": limit,
            "offset": offset
        }

        playlist_tracks_response = requests.get(playlist_tracks_url, headers=playlist_tracks_headers, params=playlist_tracks_params)

        if playlist_tracks_response.status_code == 200:
            tracks_data = playlist_tracks_response.json()

            all_tracks.extend(tracks_data['items'])
            offset += limit
            if len(tracks_data['items']) < limit:
                break
        else:
            print("Error:", playlist_tracks_response.text)
            raise Exception("Unable to fetch playlist tracks")

    return all_tracks


def format_playlist(all_tracks):
    formatted_tracks = []
    for track in all_tracks:
        track_name = track['track']['name']
        artist_name = track['track']['artists'][0]['name']
        added_by = track['added_by']['id'] if 'added_by' in track else 'Unknown'
        formatted_tracks.append({
            'name': track_name,
            'artist': artist_name,
            'added_by': added_by
        })
    return formatted_tracks

def find_duplicates(formatted_playlist):
    duplicates = {}
    for track in formatted_playlist:
        key = (track['name'], track['artist'])
        if key in duplicates:
            if track['added_by'] not in duplicates[key]:
                duplicates[key].append(track['added_by'])
        else:
            duplicates[key] = [track['added_by']]
    return {key: value for key, value in duplicates.items() if len(value) > 1}

def generate_full_json(playlist_id, formatted_playlist, duplicates):
    str_duplicates = {str(key): value for key, value in duplicates.items()}
    full_json = {
        'playlist_name': playlist_id,
        'tracks': formatted_playlist,
        'duplicates': str_duplicates
    }
    return full_json

def write_full_json_to_file(full_json, file_path):
    with open(file_path, 'w') as file:
        json.dump(full_json, file, indent=4)

def get_username(user_id, access_token):
    user_profile_url = f"https://api.spotify.com/v1/users/{user_id}"

    user_profile_headers = {
        "Authorization": f"Bearer {access_token}"
    }

    user_profile_response = requests.get(user_profile_url, headers=user_profile_headers)

    if user_profile_response.status_code == 200:
        user_profile_data = user_profile_response.json()
        username = user_profile_data['display_name'] if 'display_name' in user_profile_data else 'Unknown'
        return username
    else:
        print("Error:", user_profile_response.text)
        raise Exception("Unable to fetch user profile")

def main():
    access_token, expires = get_access_token(CLIENT_ID, CLIENT_SECRET)
    # print(f"Access Token: {access_token}")
    print(f"Token Expires at: {expires}")

    playlist_url = input("Enter Spotify playlist URL: ")
    parsed_url = urlparse(playlist_url)
    path_segments = parsed_url.path.split('/')
    playlist_id = path_segments[-1] 

    # Get all tracks
    all_tracks_data = fetch_all_tracks(access_token, playlist_id, limit=50)

    formatted_playlist = format_playlist(all_tracks_data)

    duplicates = find_duplicates(formatted_playlist)

    print("Duplicated Tracks:")
    for key, users in duplicates.items():
        track_name, artist_name = key
        added_by_users = [get_username(user_id, access_token) for user_id in users]
        added_by = ", ".join(added_by_users)
        print(f"Track: {track_name}, Artist: {artist_name}, Added by: {added_by}")

    full_json = generate_full_json(playlist_id, formatted_playlist, duplicates)

    json_file_path = 'playlist.json'
    write_full_json_to_file(full_json, json_file_path)
    print(f"Full JSON written to JSON file: {json_file_path}")

if __name__ == "__main__":
    main()
