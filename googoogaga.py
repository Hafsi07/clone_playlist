import os
import requests
import googleapiclient.discovery
import base64
import urllib.parse

# Set up API keys (Replace with your own keys)
YOUTUBE_API_KEY = "AIzaSyCFsgez3d--SRL_xHX9KzD_j_-cqgglfgo"
SPOTIFY_CLIENT_ID = "09a63292fb754718b0dd5063b90d1f62"
SPOTIFY_CLIENT_SECRET = "9e28c8872ac54bd2ba0b8926b91cf269"
SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"
SPOTIFY_API_URL = "https://api.spotify.com/v1"


# Function to get Spotify authorization token
def get_spotify_access_token(client_id, client_secret):
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_data = {
        'grant_type': 'client_credentials'
    }
    auth_header = {
        'Authorization': 'Basic ' + base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode('ascii')
    }

    response = requests.post(auth_url, headers=auth_header, data=auth_data)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception("Failed to get access token")

# YouTube API setup
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def get_youtube_playlist_videos(playlist_id):
    videos = []
    next_page_token = None
    
    while True:
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response['items']:
            title = item['snippet']['title']
            artist = item['snippet'].get('videoOwnerChannelTitle', 'Unknown Artist')
            videos.append((title, artist))
        
        next_page_token = response.get('nextPageToken')
        print(next_page_token)
        if not next_page_token:
            break
    
    return videos

def search_spotify_track(title, artist, headers):
    query = urllib.parse.quote(f"track:{title} artist:{artist}")
    url = f"{SPOTIFY_API_URL}/search?q={query}&type=track&limit=1"
    response = requests.get(url, headers=headers).json()
    tracks = response.get("tracks", {}).get("items", [])
    if tracks:
        return tracks[0]['id']
    return None

def create_spotify_playlist(name, headers):
    url = f"{SPOTIFY_API_URL}/me"
    user_data = requests.get(url, headers=headers).json()
    user_id = user_data.get("id")
    if not user_id:
        raise Exception("Failed to retrieve Spotify user ID: " + str(user_data))
    
    playlist_url = f"{SPOTIFY_API_URL}/users/{user_id}/playlists"
    data = {"name": name, "description": "YouTube Playlist Import", "public": False}
    response = requests.post(playlist_url, json=data, headers=headers).json()
    return response.get('id')

def add_tracks_to_spotify(playlist_id, track_ids, headers):
    url = f"{SPOTIFY_API_URL}/playlists/{playlist_id}/tracks"
    data = {"uris": [f"spotify:track:{track_id}" for track_id in track_ids]}
    requests.post(url, json=data, headers=headers)

if __name__ == "__main__":
    authorization_code = "AQBI8N-8Q0WKOdyrtqwpfjUwU3nsmezvl8RMogmszq7vbV5gs66BU4_VS9-Y-JZTYXNXGHwjzIabthWivbh_b66mGKduQqaEpuxNvpe01tP5Xy5zui-IpvON0BfpBH87W5VQAxoUUQ_9ZLDe3WSz9ecM2bbrpNF4WMGHwVvpcEnnKPkNO51iTsadszEg3b-52_vsByg9t5zy7QCeLxT2eakqLfN_Ss_3k3JXas4JC78K1xo"
    spotify_access_token = get_spotify_access_token(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

    HEADERS = {"Authorization": f"Bearer {spotify_access_token}"}
    
    youtube_playlist_id = "RDylCVkCstuo4"
    playlist_name = "Imported YouTube Playlist"
    
    print("Fetching YouTube playlist...")
    youtube_tracks = get_youtube_playlist_videos(youtube_playlist_id)
    
    print("Creating Spotify playlist...")
    spotify_playlist_id = create_spotify_playlist(playlist_name, HEADERS)
    
    spotify_track_ids = []
    print("Searching and adding tracks to Spotify...")
    for title, artist in youtube_tracks:
        track_id = search_spotify_track(title, artist, HEADERS)
        if track_id:
            spotify_track_ids.append(track_id)
    
    if spotify_track_ids:
        add_tracks_to_spotify(spotify_playlist_id, spotify_track_ids, HEADERS)
        print(f"Successfully added {len(spotify_track_ids)} tracks to Spotify.")
    else:
        print("No tracks found on Spotify.")
