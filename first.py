from googleapiclient.discovery import build
import json
import base64
import requests

yt_api = "AIzaSyCFsgez3d--SRL_xHX9KzD_j_-cqgglfgo"

sptfy_auth = "09a63292fb754718b0dd5063b90d1f62"
sptfy_api = "9e28c8872ac54bd2ba0b8926b91cf269"


yt = build('Youtube', 'v3', developerKey=yt_api )   

request = yt.playlistItems().list(part= 'snippet', playlistId='RDylCVkCstuo4',maxResults=50)


response = request.execute()

video_ids = [item['snippet']['resourceId']['videoId'] for item in response['items']]
print(video_ids)

with open('res.json','w') as f:
    json.dump(response,f, indent=4)


SCOPES  = ['https://www.googleapis.com/auth/youtube']

def get_spotify_access_token(client_id, client_secret):
    auth_url = "https://accounts.spotify.com/api/token"
    data = {"grant_type": "client_credentials"}
    headers = {"Authorization": f"Basic {base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode('ascii')}"}
    
    response = requests.post(auth_url, data=data, headers=headers)
    token_data = response.json()
    
    if "access_token" in token_data:
        print("access granted")
        return token_data["access_token"]
    else:
        raise Exception("Failed to get access token: " + str(token_data))

# Get Spotify token
SPOTIFY_ACCESS_TOKEN = get_spotify_access_token(sptfy_auth, sptfy_api)
HEADERS = {"Authorization": f"Bearer {SPOTIFY_ACCESS_TOKEN}"}

# YouTube API setup
youtube = build("youtube", "v3", developerKey=yt_api)

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
            try:
                title = item['snippet']['title']
                artist = item['snippet']['videoOwnerChannelTitle']
                videos.append((title, artist))
            except: 
                print('skipped')
                continue
        next_page_token = response.get('nextPageToken')
        print(next_page_token)
        if not next_page_token:
            break
        print(len(videos))
    
    return videos   

SPOTIFY_API_URL = "https://api.spotify.com/v1"

def search_spotify_track(title, artist):
    query = f"track:{title} artist:{artist}"
    url = f"{SPOTIFY_API_URL}/search?q={query}&type=track&limit=1"
    response = requests.get(url, headers=HEADERS).json()
    print(response,'   ',url)
    tracks = response.get("tracks", {}).get("items", [])

    if tracks:
        return tracks[0]['id']
    return None

def create_spotify_playlist(name, description="YouTube Playlist Import"):
    url = f"{SPOTIFY_API_URL}/me"
    user_id = requests.get(url, headers=HEADERS).json().get("id")
    playlist_url = f"{SPOTIFY_API_URL}/users/{user_id}/playlists"
    data = {"name": name, "description": description, "public": False}
    response = requests.post(playlist_url, json=data, headers=HEADERS).json()
    return response.get('id')

def add_tracks_to_spotify(playlist_id, track_ids):
    url = f"{SPOTIFY_API_URL}/playlists/{playlist_id}/tracks"
    data = {"uris": [f"spotify:track:{track_id}" for track_id in track_ids]}
    requests.post(url, json=data, headers=HEADERS)

if __name__ == "__main__":
    youtube_playlist_id = "PLr-XCZlklEPDuf2KvOKNqujTbPpyRTdZm"
    playlist_name = "Imported YouTube Playlist"
    
    print("Fetching YouTube playlist...")
    youtube_tracks = get_youtube_playlist_videos(youtube_playlist_id)
    print(youtube_tracks)
    print("Creating Spotify playlist...")
    spotify_playlist_id = create_spotify_playlist(playlist_name)
    
    spotify_track_ids = []
    print("Searching and adding tracks to Spotify...")
    for title, artist in youtube_tracks:
        track_id = search_spotify_track(title, artist)
        if track_id:
            spotify_track_ids.append(track_id)
    
    if spotify_track_ids:
        add_tracks_to_spotify(spotify_playlist_id, spotify_track_ids)
        print(f"Successfully added {len(spotify_track_ids)} tracks to Spotify.")
    else:
        print("No tracks found on Spotify.")