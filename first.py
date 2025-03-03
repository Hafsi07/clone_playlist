from googleapiclient.discovery import build
import json
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import re

load_dotenv("credentials.env")

yt_api = os.getenv("yt_api")
sptfy_auth = os.getenv("sptfy_auth")
sptfy_api = os.getenv("sptfy_api")

yt = build('youtube', 'v3', developerKey=yt_api )   

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
        video_ids = []
        for item in response['items']:
            try:
                video_id = item['snippet']['resourceId']['videoId']
                title = item['snippet']['title']
                artist = item['snippet']['videoOwnerChannelTitle']
                publish_date = item['contentDetails']['videoPublishedAt']
                videos.append({"video_id" : video_id, "title" : title, "artist" : artist, "date" : publish_date})
                video_ids.append(video_id)
            except: 
                k=k+1
                continue
        print(len(videos)," first len")
        req = youtube.videos().list(part = "contentDetails,statistics", id = ",".join(video_ids))
        res = req.execute()
        details={}
        for item in res['items']:
            video_id = item['id']
            duration = item['contentDetails']['duration']
            views = item['statistics'].get('viewCount', '0')
            likes = item['statistics'].get('likeCount', '0')

            details[video_id] = {
                "duration": duration,
                "views": int(views),
                "likes": int(likes)
            }
        for i,video in enumerate(videos[-len(videos):]):
            video.update(details.get(video["video_id"], {}))
        print(len(videos)," second len")

        next_page_token = response.get('nextPageToken')
        print('Next page token :',next_page_token,'\n')
        if not next_page_token:
            break
    print(f"we have {len(videos)} tracks")
    print('skipped ',k,' tracks')
    
    return videos   

SPOTIFY_API_URL = "https://api.spotify.com/v1"

def clean_dict(song):
    # print('\n',song)
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', song["duration"])
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    song["duration"] = ((hours * 3600) + (minutes * 60) + seconds) * 1000

    song["artist"] = re.sub(r"(?i)\b(vevo|topic|various artists|official channel|official|records|music|productions)\b", "", song["artist"], flags=re.IGNORECASE)
    song["artist"] = re.sub(r"[^\w\s]", "", song["artist"]).strip()

    song["title"]= re.sub(r"\(.*?\)|\[.*?\]", "", song["title"]) 
    song["title"] = re.sub( rf"^{re.escape(song["artist"])}\s*[-:]\s*", "", song["title"], flags=re.IGNORECASE).strip()
    # print(song["artist"].replace(' ',''))
    song["title"] = re.sub( rf"^{re.escape(str(song["artist"]).replace(' ',''))}\s*[-:]\s*", "", song["title"], flags=re.IGNORECASE).strip()
    unwanted_words = r"\b(official|video|lyrics|audio|hd|4k|remastered|vevo|cover|live|mix|edit|extended|ft\.?|feat\.?)\b"
    song["title"] = re.sub(unwanted_words, "", song["title"], flags = re.IGNORECASE)
    song["title"] = song["title"].strip()
    # print(song,'\n')
    
    return song



def search_spotify_track(song):
    query = f"track:{song["title"]}"
    
    url = f"{SPOTIFY_API_URL}/search?q={query}&type=track&limit=1"
    response = requests.get(url, headers=HEADERS).json()
    tracks = response.get("tracks", {}).get("items", [])

    
    
    if not tracks:
        return None
    
    matche=None
    duration_error=float(9999000)
    for track in tracks:
        spotify_duration = track["duration_ms"]
        diff = abs(spotify_duration - song["duration"])

        if diff < duration_error:  
            duration_error = diff
            matche = track
    print('\n',song["title"],' -- ',song["artist"],' -- ',song["duration"],' :: ', matche["name"],' -- ',matche["duration_ms"])
    if matche: return matche["id"]
    

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
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i:i + 100]
        payload = {"uris": [f"spotify:track:{track_id}" for track_id in batch]}
        
        response = requests.post(url, json=payload, headers=HEADERS)
        
        if response.status_code == 201:
            print(f"✅{len(batch)} tracks added!")
        else:
            print(f"❌ Error adding tracks: {response.status_code} - {response.text}")

if __name__ == "__main__":
    youtube_playlist_id = "PLr-XCZlklEPDuf2KvOKNqujTbPpyRTdZm"
    
    print("Fetching YouTube playlist...")
    youtube_tracks = get_youtube_playlist_videos(youtube_playlist_id)
    print("\nCreating Spotify playlist...")
    
    spotify_playlist_id = create_spotify_playlist(name = "Code_trial")
    
    spotify_track_ids = []
    print("\nSearching and adding tracks to Spotify...")
    for song in youtube_tracks:
        track_id = search_spotify_track(clean_dict(song))
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