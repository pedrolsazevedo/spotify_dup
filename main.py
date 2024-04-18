import os
import requests
import base64
from datetime import datetime, timedelta
import json
import logging
from urllib.parse import urlparse, parse_qs

CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')

logging.basicConfig(level=logging.INFO)

def get_access_token(client_id, client_secret):
    logging.info("Fetching access token...")
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
        logging.info("Access token fetched successfully.")
        return access_token, expires
    else:
        logging.error("Failed to fetch access token.")
        raise Exception("Unable to fetch access token")

def fetch_all_tracks(access_token, playlist_id, limit=100):
    logging.info("Fetching playlist tracks...")
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

    logging.info("Playlist tracks fetched successfully.")
    return all_tracks

def get_username(user_id, access_token):
    logging.info(f"Fetching username for user ID: {user_id}...")
    user_profile_url = f"https://api.spotify.com/v1/users/{user_id}"

    user_profile_headers = {
        "Authorization": f"Bearer {access_token}"
    }

    user_profile_response = requests.get(user_profile_url, headers=user_profile_headers)

    if user_profile_response.status_code == 200:
        user_profile_data = user_profile_response.json()
        username = user_profile_data['display_name'] if 'display_name' in user_profile_data else 'Unknown'
        logging.info(f"Username fetched successfully for user ID: {user_id}.")
        return username
    else:
        logging.error(f"Failed to fetch username for user ID: {user_id}.")
        print("Error:", user_profile_response.text)
        raise Exception("Unable to fetch user profile")

def get_users_info(track_list, access_token):
    user_ids = set(track['added_by']['id'] for track in track_list if 'added_by' in track)
    users_info = {}
    for user_id in user_ids:
        users_info[user_id] = get_username(user_id, access_token)
    return users_info

def format_playlist(all_tracks, users_info):
    logging.info("Formatting playlist...")
    formatted_tracks = []
    for track in all_tracks:
        track_name = track['track']['name']
        artist_name = track['track']['artists'][0]['name']
        added_by_id = track['added_by']['id'] if 'added_by' in track else 'Unknown'
        added_by_username = users_info.get(added_by_id, 'Unknown')
        formatted_tracks.append({
            'name': track_name,
            'artist': artist_name,
            'added_by': added_by_username
        })
    logging.info("Playlist formatted successfully.")
    return formatted_tracks

def find_duplicates(formatted_playlist):
    logging.info("Finding duplicates...")
    duplicates = {}
    for track in formatted_playlist:
        key = (track['name'], track['artist'])
        if key in duplicates:
            if track['added_by'] not in duplicates[key]:
                duplicates[key].append(track['added_by'])
        else:
            duplicates[key] = [track['added_by']]
    logging.info("Duplicates found successfully.")
    return {key: value for key, value in duplicates.items() if len(value) > 1}

def generate_full_json(playlist_id, formatted_playlist, duplicates):
    logging.info("Generating full JSON...")
    str_duplicates = {str(key): value for key, value in duplicates.items()}
    full_json = {
        'playlist_name': playlist_id,
        'tracks': formatted_playlist,
        'duplicates': str_duplicates
    }
    logging.info("Full JSON generated successfully.")
    return full_json

def write_full_json_to_file(full_json, file_path):
    logging.info("Writing JSON to file...")
    with open(file_path, 'w') as file:
        json.dump(full_json, file, indent=4)
    logging.info(f"JSON written to file: {file_path}")

def save_playlist_to_text(formatted_playlist, file_path):
    with open(file_path, 'w') as file:
        for track in formatted_playlist:
            track_name = track['name']
            artist_name = track['artist']
            added_by = track['added_by']
            file.write(f"{track_name}, {artist_name}, Added by: {added_by}\n")
    print(f"Playlist saved to text file: {file_path}")


def main():
    access_token, expires = get_access_token(CLIENT_ID, CLIENT_SECRET)
    print(f"Token Expires at: {expires}")

    playlist_url = input("Enter Spotify playlist URL: ")
    parsed_url = urlparse(playlist_url)
    path_segments = parsed_url.path.split('/')
    playlist_id = path_segments[-1] 

    # Get all tracks
    all_tracks_data = fetch_all_tracks(access_token, playlist_id, limit=50)

    # Get users info
    users_info = get_users_info(all_tracks_data, access_token)

    formatted_playlist = format_playlist(all_tracks_data, users_info)

    duplicates = find_duplicates(formatted_playlist)

    print("playlist")
    # print(formatted_playlist)
    # for track in formatted_playlist:
    #     track_name = track['name']
    #     artist_name = track['artist']
    #     added_by = track['added_by']
    #     print(f"{track_name}, {artist_name}, Added by: {added_by}")
    save_playlist_to_text(formatted_playlist, 'playlist.txt')


    print("Duplicated Tracks:")
    for key, users in duplicates.items():
        track_name, artist_name = key
        added_by_users = [users_info[user_id] for user_id in users]
        added_by = ", ".join(added_by_users)
        print(f"Track: {track_name}, Artist: {artist_name}, Added by: {added_by}")

    full_json = generate_full_json(playlist_id, formatted_playlist, duplicates)

    json_file_path = 'playlist.json'
    write_full_json_to_file(full_json, json_file_path)
    print(f"Full JSON written to JSON file: {json_file_path}")

if __name__ == "__main__":
    main()
