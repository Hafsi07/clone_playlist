from googleapiclient.discovery import build
import json
import base64
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth

yt_api = "AIzaSyCFsgez3d--SRL_xHX9KzD_j_-cqgglfgo"

sptfy_auth = "f3d33bf066ab4f07bf4685bcf81ee0a2"
sptfy_api = "faf4810bfc7e4195aeaacebb613b3bd7"


yt = build('youtube', 'v3', developerKey=yt_api )   

request = yt.playlistItems().list(part= 'snippet', playlistId='RDylCVkCstuo4',maxResults=50)


response = request.execute()

video_ids = [item['snippet']['resourceId']['videoId'] for item in response['items']]
print(video_ids)

with open('res.json','w') as f:
    json.dump(response,f, indent=4)


SCOPES  = ['https://www.googleapis.com/auth/youtube']

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=sptfy_auth,
                                            client_secret=sptfy_api,
                                            redirect_uri="http://localhost:8888/callback",
                                            scope="playlist-modify-public playlist-modify-private"))
def get_spotify_access_token(sp):
    token_info = sp.auth_manager.get_cached_token()
    if not token_info or sp.auth_manager.is_token_expired(token_info):
        token_info = sp.auth_manager.refresh_access_token(token_info['refresh_token'])
    return token_info['access_token']


# Get Spotify token
SPOTIFY_ACCESS_TOKEN = get_spotify_access_token(sp)
HEADERS = {"Authorization": f"Bearer {SPOTIFY_ACCESS_TOKEN}"}
print("\nHeaders :",HEADERS)



# YouTube API setup
youtube = build("youtube", "v3", developerKey=yt_api)

def get_youtube_playlist_videos(playlist_id):
    videos = []
    next_page_token = None
    
    k=0
    while True:
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
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
                k=k+1
                continue
        next_page_token = response.get('nextPageToken')
        print('Next page token :',next_page_token,'\n')
        if not next_page_token:
            break
        print(f"we have {len(videos)} tracks")
    print('skipped ',k,' tracks')
    
    return videos   

SPOTIFY_API_URL = "https://api.spotify.com/v1"

def search_spotify_track(title, artist):
    query = f"track:{title} artist:{artist}"
    url = f"{SPOTIFY_API_URL}/search?q={query}&type=track&limit=1"
    response = requests.get(url, headers=HEADERS).json()
    tracks = response.get("tracks", {}).get("items", [])
    

    if tracks:
        print('\n', title,'<>',artist,' -- ',tracks[0].get("name"))
        with open('track_example.json','w') as f:
            json.dump(tracks[0],f, indent=4)
        return tracks[0]['id']
    return None

def get_user_id(token):
    url = "https://api.spotify.com/v1/me"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.json()

def create_spotify_playlist(name, description="trialList",public=True):
    user_id = get_user_id(SPOTIFY_ACCESS_TOKEN).get("id")
    print("la mama: ",user_id)
    try:
        playlist = sp.user_playlist_create(user=user_id, name=name, public=public, description=description)
        return playlist['id']
    except Exception as e:
        print("Error while creating playlist :",e)
        return None
    

def add_tracks_to_spotify(playlist_id, track_ids):
    url = f"{SPOTIFY_API_URL}/playlists/{playlist_id}/tracks"
    data = {"uris": [f"spotify:track:{track_id}" for track_id in track_ids]}
    res=requests.post(url, json=data, headers=HEADERS)
    print('\n',res)

if __name__ == "__main__":
    youtube_playlist_id = "PLr-XCZlklEPDuf2KvOKNqujTbPpyRTdZm"
    
    print("Fetching YouTube playlist...")
    youtube_tracks = get_youtube_playlist_videos(youtube_playlist_id)
    print("Creating Spotify playlist...")
    
    spotify_playlist_id = create_spotify_playlist(name = "Code_trial")
    
    spotify_track_ids = []
    print("Searching and adding tracks to Spotify...")
    for title, artist in youtube_tracks:
        track_id = search_spotify_track(title, artist)
        if track_id:
            spotify_track_ids.append(track_id)
    print(spotify_track_ids)
    if spotify_track_ids:
        add_tracks_to_spotify(spotify_playlist_id, spotify_track_ids)
        print(f"Successfully added {len(spotify_track_ids)} tracks to Spotify.")
    else:
        print("No tracks found on Spotify.")

# add more specifications to improve search 
# handle naming and check for playlist existence beforehand