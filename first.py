yt_api="AIzaSyCFsgez3d--SRL_xHX9KzD_j_-cqgglfgo"

sptfy_api="9e28c8872ac54bd2ba0b8926b91cf269"


from Google import Create_Service

import pandas as pd

CLIENT_SECRET_FILE  =  yt_api
API_NAME  =  'youtube'
API_VERSION  =  'v3'
SCOPES  = ['https://www.googleapis.com/auth/youtube']

service =  Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)


playlistId_Source = '<Source YouTube Playlist>'
playlistId_Target = '<Your YouTube Playlist>'

response = service.playlistItems().list(
    part='contentDetails',
    playlistId=playlistId_Source,
    maxResults=50
).execute()

playlistItems = response['items']
nextPageToken = response.get('nextPageToken')
