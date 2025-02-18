from googleapiclient.discovery import build
import json
import requests

yt_api="AIzaSyCFsgez3d--SRL_xHX9KzD_j_-cqgglfgo"

sptfy_api="9e28c8872ac54bd2ba0b8926b91cf269"


yt = build('Youtube', 'v3', developerKey=yt_api )   

request = yt.playlistItems().list(part= 'snippet,contentDetails', playlistId='RDylCVkCstuo4',maxResults=50)


response = request.execute()

video_ids = [item['snippet']['resourceId']['videoId'] for item in response['items']]
print(video_ids)

with open('res.json','w') as f:
    json.dump(response,f, indent=4)


SCOPES  = ['https://www.googleapis.com/auth/youtube']

def vids_getter(playlist_id):
    videos = []
    next_page_token = None
    
    while True:
        request = yt.playlistItems().list(
            part = "snippet",
            playlistId = playlist_id,
            maxResults = 50,
            pageToken = next_page_token
        )
        response = request.execute()
        
        for item in response['items']:
            title = item['snippet']['title']
            artist = item['snippet']['videoOwnerChannelTitle']
            videos.append((title, artist))
        
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    
    return videos

SPOTIFY_API_URL = "https://api.spotify.com/v1"
HEADERS = {"Authorization": f"Bearer {sptfy_api}"}

def find_sptfy_track(title, artist):
    query = f"track:{title} artist:{artist}"
    url = f"{SPOTIFY_API_URL}/search?q={query}&type=track&limit=1"
    response = requests.get(url, headers=HEADERS).json()
    tracks = response.get("tracks", {}).get("items", [])
    if tracks:
        return tracks[0]['id']
    return None

def create_spotify_playlist(name, description="YouTube Playlist Import"):
    url = f"{SPOTIFY_API_URL}/me"
    user_id = requests.get(url, headers=HEADERS).json()
    print(user_id)
    #playlist creation proble 
    playlist_url = f"{SPOTIFY_API_URL}/users/{user_id}/playlists"
    data = {"name": name, "description": description, "public": False}
    response = requests.post(playlist_url, json=data, headers=HEADERS).json()
    return response['id']

def tracks_to_playlist(playlist_id, track_ids):
    url = f"{SPOTIFY_API_URL}/playlists/{playlist_id}/tracks"
    data = {"uris": [f"spotify:track:{track_id}" for track_id in track_ids]}
    requests.post(url, json=data, headers=HEADERS)


youtube_playlist_id = "PLhwcfFjZh5sg2kjcxek8lzFZ5ud9xaw9K" #weekend
primo_nome = "trial"

yt_tracks = vids_getter(youtube_playlist_id)

spotify_playlist_id = create_spotify_playlist(primo_nome)

spotify_track_ids = []
for title, artist in yt_tracks:
    track_id = find_sptfy_track(title, artist)
    if track_id:
        spotify_track_ids.append(track_id)

if spotify_track_ids:
    tracks_to_playlist(spotify_playlist_id, spotify_track_ids)
    print(len(spotify_track_ids))
else:
    print("sheesh")
