# Log into YouTube
# Request a list of current user's playlists
# Get the playlist ID of a specified playlist
# If specified playlist doesn't exist, create new playlist and get its playlist ID
# Use playlist ID to retrieve list of playlist contents
# Log into Spotify
# Create playlist, if it doesn't already exist
# Add song to playlist using info from YouTube, if it isn't already in playlist 

import requests
import json
import os
import string

import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import googleapiclient.discovery
import googleapiclient.errors

from youtube_dl import YoutubeDL

from ytmusicapi.ytmusic import YTMusic

import spotipy
from spotipy.oauth2 import SpotifyOAuth

def main():

    def YoutubeOauthLogin():
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        youtube_client_secrets_file = "youtube_client_secret.json"
        #Scope = "https://www.googleapis.com/auth/youtube" if modyfying YouTube account
        scopes = ["https://www.googleapis.com/auth/youtube"]

        
        user_credentials = None
        if os.path.exists('youtube_token.json'):
            user_credentials = Credentials.from_authorized_user_file(
                'youtube_token.json', scopes)
        if not user_credentials or not user_credentials.valid:
            if user_credentials and user_credentials.expired and user_credentials.refresh_token:
                user_credentials.refresh(Request()) 
            else:
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                    youtube_client_secrets_file, scopes)
                user_credentials = flow.run_local_server(
                    port=8080, prompt="consent", authorization_prompt_message="")
                authorization_url, state = flow.authorization_url(
                    access_type='offline')
            with open('youtube_token.json', 'w') as token:
                token.write(user_credentials.to_json())  

        youtube = googleapiclient.discovery.build(
            api_service_name, 
            api_version, 
            credentials=user_credentials)

        return youtube


    def SpotifyOAuthLogin():
        client_secrets_file = open("spotify_client_secret.json")
        data = json.load(client_secrets_file)
        client_id = data['spotify_client_id']
        client_secret = data['spotify_client_secret']
        redirect_uri = data['spotify_redirect_uri']
        scopes = "playlist-modify-public"

        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scopes))

        return sp

    def listSpotifyPlaylists():
        results = sp.current_user_playlists()
        data = {}
        data['items'] = {}
        list = []
        for playlists in results['items']:
            itemInfo = dict()
            itemInfo['playlistName'] = playlists['name']
            itemInfo['playlistId'] = playlists['id']
            list.append(itemInfo)
        data['items'] = list
        
        return data

    def getSpotifyPlaylistId(SpotifyPlaylists, playlistTitle):
        for playlists in SpotifyPlaylists['items']:
            if (playlists['playlistName'] == playlistTitle):
                return playlists['playlistId'] 
        
        return None

    def spotifyPlaylistItems(playlistId):
        results = sp.playlist_items(playlistId,fields="items(track(artists(name),name,id))")
        data = {}
        data['items'] = {}
        list = []
        for song in results['items']:
            itemInfo = dict()
            itemInfo['songName'] = song['track']['name']
            itemInfo['songArtist'] = song['track']['artists'][0]['name']
            itemInfo['songId'] = song['track']['id']
            list.append(itemInfo)
        data['items'] = list 
        
        return data

    def createSpotifyPlaylist(playlistTitle):
        userId = sp.current_user()['id']
        results = sp.user_playlist_create(user=userId, name=playlistTitle, public=True, collaborative=False, description="")
        
        return results

    def listItemsOrCreatePlaylistSpotify(playlistId, playlistTitle):
        if(playlistId == None):
            createdPlaylist = createSpotifyPlaylist(playlistTitle)
            playlistId = createdPlaylist['id']
        
        return spotifyPlaylistItems(playlistId)

    def addItemToSpotifyPlaylist(playlistId, trackId):
        results = sp.playlist_add_items(playlist_id=playlistId,items=trackId)
        
        return results


    # From dotenv import load_dotenv
    # load_dotenv()
    # client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    # client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    # redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI")

    # scope = "user-library-read"

    # sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    #     client_id=client_id,
    #     client_secret=client_secret,
    #     redirect_uri=redirect_uri,
    #     scope=scope))

    # results = sp.current_user_saved_tracks()
    # for idx, item in enumerate(results['items']):
    #     track = item['track']
    #     print(idx, track['artists'][0]['name'], " – ", track['name'])


    #requests a list of the current user's YouTube playlists
    #part/fields used to filter data and only retrieve relevant information
    def listUsersPlaylists():
        listUsersPlaylists = youtube.playlists().list(
            part="snippet",
            fields="items(id,snippet(title))",
            maxResults=25,
            mine=True
        )
        
        return listUsersPlaylists.execute()

    #searches current user's YouTube playlists for a specified playlist title and returns its playlistId. Returns None if playlist doesn't exist
    def getPlaylistId(usersPlaylists, playlistTitle):
        for title in usersPlaylists['items']:
            if(title['snippet']['title'] == playlistTitle):
                return title['id']
        
        return None
    
    #creates a playlist on YouTube and returns the properties of the playlist
    def createPlaylist(playlistTitle):
        createPlaylist = youtube.playlists().insert(
            part="snippet",
            body={
                "snippet": {
                    "title": playlistTitle
                }
            }
        )
        
        return createPlaylist.execute()
    
    #uses a specified youtube playlistID and returns a list of titles and urls for the items in that playlist
    def listPlaylistItems(playlistId):
        listPlaylistItems = youtube.playlistItems().list(
            part="snippet",
            fields="items(snippet(title,resourceId(videoId)))",
            maxResults=25,
            playlistId=playlistId
        )
        youtubeOutput = listPlaylistItems.execute()

        playListItems = {}
        playListItems['items'] = {}
        listOfItems = []
        for item in youtubeOutput['items']:
            itemInfo = dict()
            title = item['snippet']['title']
            url = "https://www.youtube.com/watch?v={}".format(item['snippet']['resourceId']['videoId'])
            itemInfo['title'] = title
            itemInfo['url'] = url
            listOfItems.append(itemInfo)
        playListItems['items'] = listOfItems
        
        return playListItems

    #Lists items of specified youtube playlist or create new playlist if one does not exist
    def listItemsOrCreatePlaylist(playlistId, playlistTitle):
        if(playlistId == None):
            createdPlaylist = createPlaylist(playlistTitle)
            playlistId = createdPlaylist['id']
            return listPlaylistItems(playlistId)
        else:
            return listPlaylistItems(playlistId)

    #Adds a video to a specified youtube playlist given its videoId 
    def addItemToPlaylist(playlistId, videoId):
        addItemsToPlaylist = youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet":{
                    "playlistId": playlistId,
                    "resourceId":{
                        "kind": "youtube#video",
                        "videoId": videoId
                    }
                }
            }
        )
        
        return addItemsToPlaylist.execute()

    #Uses youtube_dl library methods to provide artist name and song title given a list of playlist items from youtube
    def youtubeSongAndArtistName(listPlaylistItems):
        data = {}
        data['songs'] = {}
        listOfSongs = []
        for song in listPlaylistItems['items']:
            songs = dict()
            ydl_opts = {
                'nocheckcertificate':True
            }
            ydl = YoutubeDL(ydl_opts)
            ydl.add_default_info_extractors()
            info = ydl.extract_info(
                song['url'], download=False)
            if 'artist' in info and 'track' in info:
                songName = info['track']
                songArtist = info['artist']
                songs['songName'] = songName
                songs['songArtist'] = songArtist
                listOfSongs.append(songs)
            #else:
                #print(info)
        data['songs'] = listOfSongs
        
        return data
    
    #Uses ytmusic library methods to search youtube music for a given artist and song title, returning the videoId of the most viewed video
    def youtubeIdFromArtisAndTitle(artistAndTitle):
        ytmusic = YTMusic('headers_auth.json')
        search_results = ytmusic.search(artistAndTitle, filter="videos", limit=2, ignore_spelling=True)
        max = None
        videoId = None
        for i in range(len(search_results)):
            songViewCount = search_results[i]['views']
            songViewCount = songViewCount.translate(str.maketrans('','', string.punctuation))
            songViewCount = songViewCount.replace("M","000000")
            songViewCount = songViewCount.replace("K","000")
            songViewCount = int(songViewCount)
            if max is None or songViewCount > max:
                max = songViewCount
                videoId = search_results[i]['videoId']
        
        return videoId

    def listYoutubePlaylistItems(youtube):
        usersPlaylists = listUsersPlaylists()
        #only line of code that user would change
        playlistTitle = "Spotify Songs"
        playlistId = getPlaylistId(usersPlaylists, playlistTitle)
        playListItems = listItemsOrCreatePlaylist(playlistId, playlistTitle)

        return playListItems
    
    def listSpotifyPlaylistItems(sp):    
        SpotifyPlaylists = listSpotifyPlaylists()
        #only line of code that user would change
        SpotifyPlaylistTitle = "YouTube Music"
        spotifyPlaylistId = getSpotifyPlaylistId(SpotifyPlaylists, SpotifyPlaylistTitle)
        spotifyPlaylistItems = listItemsOrCreatePlaylistSpotify(spotifyPlaylistId,SpotifyPlaylistTitle)

        return spotifyPlaylistItems
        
    def addSongsToYoutube(listSpotifyPlaylistItems):
        for song in spotifyPlaylistItems['items']:
            artist = song['songArtist']
            track = song['songName']
            name = artist+" "+track
            youtubeId = youtubeIdFromArtisAndTitle(name)
            addItemToPlaylist('PLuzTVX73OkY7Z2Wx5hWHuytfYiQQ6DNka',youtubeId)

    def addSongsToSpotify(listYoutubePlaylistItems):
        for song in 

    
    #youtubeSongAndArtistName = youtubeSongAndArtistName(playListItems)
    #createSpotifyPlaylist(playlistTitle="Test1")
    #addItemToSpotifyPlaylist(playlistId="6ig704Ayq97zIM36dNVyDn",trackId=["6tNnz0d4tijmTed5YB434Q"])
    #addItemsToPlaylist(playlistId, videoId = "G_83KKDrggU")
    youtube = YoutubeOauthLogin()
    sp = SpotifyOAuthLogin()
    listYoutubePlaylistItems(youtube)
    listSpotifyPlaylistItems(sp)
    youtubeSongAndArtistName = youtubeSongAndArtistName(listYoutubePlaylistItems(youtube))
    print(youtubeSongAndArtistName)
    addSongsToYoutube(listSpotifyPlaylistItems(sp))
    
    #print(playListItems)
    #youtubeIdFromArtisAndTitle(artistAndTitle)

if __name__ == '__main__':
    main()