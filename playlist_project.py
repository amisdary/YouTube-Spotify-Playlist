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
# from youtube_dl.extractor import YoutubeIE

from ytmusicapi.ytmusic import YTMusic

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import database
from mysql.connector import connect, Error


class Youtube:
    
    def __init__(self):
        self.youtube = self.youtubeOauthLogin()

    #logs user into their Youtube account and gives requested permission to the program
    def youtubeOauthLogin(self):
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        youtube_client_secrets_file = "youtube_client_secret.json"
        scopes = ["https://www.googleapis.com/auth/youtube"]

        if os.path.exists('youtube_token.json'):
            user_credentials = Credentials.from_authorized_user_file(
                'youtube_token.json', scopes
            )
        else:
            user_credentials = None
        if not user_credentials or not user_credentials.valid:
            if user_credentials and user_credentials.expired and user_credentials.refresh_token:
                try:
                    # will fail if refresh token has expired or access has been revoked
                    user_credentials.refresh(Request())
                except:
                    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                        youtube_client_secrets_file, 
                        scopes
                    )
                    user_credentials = flow.run_local_server(
                        port=8080, 
                        prompt="consent", 
                        authorization_prompt_message=""
                    )
                    authorization_url, state = flow.authorization_url(
                        access_type='offline'
                    )                    
            else:
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                    youtube_client_secrets_file, 
                    scopes
                )
                user_credentials = flow.run_local_server(
                    port=8080, 
                    prompt="consent", 
                    authorization_prompt_message=""
                )
                authorization_url, state = flow.authorization_url(
                    access_type='offline'
                )
            with open('youtube_token.json', 'w') as token:
                token.write(user_credentials.to_json())  

        youtube = googleapiclient.discovery.build(
            api_service_name, 
            api_version, 
            credentials=user_credentials
        )

        return youtube

    #lists current user's YouTube playlists
    def listPlaylists(self):
        nextPageToken = None
        listPlaylists = self.youtube.playlists().list(
            part="snippet",
            fields="nextPageToken,items(id,snippet(title))",
            maxResults=25,
            pageToken=nextPageToken,
            mine=True
        )
        results = listPlaylists.execute()
        output = results

        while('nextPageToken' in results):
            nextPageToken = results['nextPageToken']
            listPlaylists = self.youtube.playlists().list(
                part="snippet",
                fields="nextPageToken,items(id,snippet(title))",
                maxResults=25,
                pageToken=nextPageToken,
                mine=True
            )
            results = listPlaylists.execute()
            for i in range(len(results['items'])):
                output['items'].append(results['items'][i])      
        
        if 'nextPageToken' in output:
            del output['nextPageToken']

        return output

    #searches current user's YouTube playlists for a specified playlist title and returns its playlistId. Returns None if playlist doesn't exist
    def getPlaylistId(self, playlists, playlistTitle):
        for title in playlists['items']:
            if(title['snippet']['title'] == playlistTitle):
                return title['id']
        
        return None
    
    #creates a playlist on YouTube and returns the properties of the playlist
    def createPlaylist(self, playlistTitle):
        createPlaylist = self.youtube.playlists().insert(
            part="snippet",
            body={
                "snippet": {
                    "title": playlistTitle
                }
            }
        )
        
        return createPlaylist.execute()
    
    #uses a specified youtube playlistID and returns a list of titles and urls for the items in that playlist
    def playlistItems(self, playlistId):
        nextPageToken = None
        playlistItems = self.youtube.playlistItems().list(
            part="snippet",
            fields="nextPageToken,items(snippet(title,resourceId(videoId)))",
            maxResults=25,
            pageToken=nextPageToken,
            playlistId=playlistId
        )
        results = playlistItems.execute()
        output = results  
        while 'nextPageToken' in results:
            nextPageToken = results['nextPageToken'] 
            playlistItems = self.youtube.playlistItems().list(
                part="snippet",
                fields="nextPageToken,items(snippet(title,resourceId(videoId)))",
                maxResults=25,
                pageToken=nextPageToken,
                playlistId=playlistId
            )
            results = playlistItems.execute()
            for i in range(len(results['items'])):
                output['items'].append(results['items'][i])
        if 'nextPageToken' in output:
            del output['nextPageToken']
            
        playlistItems = {}
        playlistItems['items'] = {}
        listOfItems = []
        for item in output['items']:
            itemInfo = dict()
            itemInfo['title'] = item['snippet']['title']
            itemInfo['videoId'] = item['snippet']['resourceId']['videoId']
            itemInfo['url'] = "https://www.youtube.com/watch?v={}".format(item['snippet']['resourceId']['videoId'])
            listOfItems.append(itemInfo)
        playlistItems['items'] = listOfItems
        playlistItems['playlistId'] = {}
        playlistItems['playlistId'] = playlistId
        
        return playlistItems

    #Lists items of specified youtube playlist or create new playlist if one does not exist
    def listItemsOrCreatePlaylist(self, playlistId, playlistTitle):
        if(playlistId == None):
            createdPlaylist = self.createPlaylist(playlistTitle)
            playlistId = createdPlaylist['id']
            return self.playlistItems(playlistId)
        else:
            return self.playlistItems(playlistId)

    #Adds a video to a specified youtube playlist given its videoId 
    def addItemToPlaylist(self, playlistId, videoId):
        addItemToPlaylist = self.youtube.playlistItems().insert(
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
            
        
        return addItemToPlaylist.execute()

    def listPlaylistItems(self, playlistTitle):
        usersPlaylists = self.listPlaylists()
        playlistId = self.getPlaylistId(usersPlaylists, playlistTitle)
        playlistItems = self.listItemsOrCreatePlaylist(playlistId, playlistTitle)

        return playlistItems

    #Uses youtube_dl library methods to provide artist name and song title given a list of playlist items from youtube
    def youtubeSongAndArtistName(self, playlistItems):
        data = {}
        data['songs'] = {}
        listOfSongs = []
        for song in playlistItems['items']:
            songs = dict()
            videoId = song['videoId']
            if database.searchYoutubeVideoId(videoId):
                info = database.songDataFromVideoId(videoId)
                songArtist = info[0][0]
                songName = info[0][1] 
                songs['videoId'] = videoId
                songs['artist'] = songArtist
                songs['track'] = songName
                listOfSongs.append(songs)                              
            else:
                ydl_opts = {
                    'nocheckcertificate':True,
                    'quiet':True,
                    'skip_download':True,
                    'force_generic_extractor':True,
                    'extract_flat':True,
                    'youtube_include_dash_manifest':False
                }
                ydl = YoutubeDL(ydl_opts)

                # ydl.add_default_info_extractors()
                info = ydl.extract_info(
                    song['url'], download=False)
                song['title'] = song['title'].lower()
                if 'artist' in info and 'track' in info:
                    # videoId = song['videoId']
                    songName = info['track']
                    songArtist = info['artist']
                    songName = songName.replace("(Explicit Version)", "")
                    songName = songName.replace("(Explicit)", "")
                    songName = songName.replace("Album Version", "")
                    songName = songName.replace(" feat.", "")
                    songName = songName.replace("feat. ", "")               
                    if "instrumental" not in song['title']:
                        songName = songName.replace("(Instrumental)", "")
                    songArtist = songArtist.replace(" feat.", "")
                    songArtist = songArtist.replace("feat. ", "")
                    songArtist = songArtist.replace(",", "")
                    songArtist = songArtist.replace(" & ", " ")
                    songArtist = songArtist.replace("&", " ")
                    songs['videoId'] = videoId
                    songs['artist'] = songArtist
                    songs['track'] = songName
                    listOfSongs.append(songs)
                elif 'track' in info:
                    # videoId = song['videoId']
                    songName = info['track']
                    songArtist = ''
                    songs['videoId'] = videoId
                    songs['artist'] = songArtist
                    songs['track'] = songName
                    if "instrumental" not in song['title']:
                        songName = songName.replace("(Instrumental)", "")               
                    listOfSongs.append(songs)
                else:
                    # videoId = song['videoId']
                    songName = song['title']
                    songName = songName.replace("(official lyric video)", "")
                    songName = songName.replace("(lyrics)", "")
                    songName = songName.replace("(official video)", "")
                    songName = songName.replace("feat.", "") 
                    songName = songName.replace(" feat.", "")                               
                    songName = songName.replace("-", "")
                    songName = songName.replace(" | ", " ")
                    songName = songName.replace("|", "")
                    songName = songName.replace(" x ", " ")
                    songArtist = ''
                    songs['videoId'] = videoId
                    songs['artist'] = songArtist
                    songs['track'] = songName
                    listOfSongs.append(songs)
        data['songs'] = listOfSongs
        
        return data 

    #lists current user's YouTube playlists
    def printPlaylists(self):
        print("")
        print("Below is a list of your YouTube playlists:")
        print("")
        usersPlaylists = self.listPlaylists()
        if usersPlaylists['items']:
            for playlists in usersPlaylists['items']:
                print(playlists['snippet']['title'])
            print("")
        else:
            print("You have no Youtube playlists.")
            print("")

        return usersPlaylists        

    #
    def explorePlaylist(self, playlists):
        playlistTitle = None
        playlistTitleLookup = input("Please type the name of the Youtube playlist exactly as seen: ")
        for playlists in playlists['items']:    
            if playlistTitleLookup in playlists['snippet']['title']:
                playlistTitle = playlistTitleLookup
        if playlistTitle:    
            print("")
            print("Below are the items in your {} playlist.".format(playlistTitle))
            playlistItems = self.listPlaylistItems(playlistTitle)
            if playlistItems['items']:
                print("")
                for songs in playlistItems['items']:
                    print("video title: ", songs['title'])
                print("")
                return
            else:
                print("")
                print("There are no items in this playist yet.")
                print("")
                return
        else: 
            print(playlistTitleLookup, " does not exist.")
            return self.explorePlaylist(youtubePlaylists) 


class Spotify:

    def __init__(self):
        self.sp = self.spotifyOAuthLogin()

    #logs user into their Spotify account and gives requested permission to the program
    def spotifyOAuthLogin(self):
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
                scope=scopes
        ))

        return sp        

    #lists current user's Spotify playlists
    def listPlaylists(self):
        results = self.sp.current_user_playlists()
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

    #searches current user's Spotify playlists for a specified playlist title and returns its playlistId. Returns None if playlist doesn't exist    
    def getPlaylistId(self, playlists, playlistTitle):
        for playlists in playlists['items']:
            if (playlists['playlistName'] == playlistTitle):
                return playlists['playlistId'] 
        
        return None

    #creates a public Spotify playlist under the current user's account
    def createPlaylist(self, playlistTitle):
        userId = self.sp.current_user()['id']
        results = self.sp.user_playlist_create(
            user=userId, 
            name=playlistTitle, 
            public=True, 
            collaborative=False, 
            description=""
        )
        
        return results

    #uses a specified Spotify playlistID and returns a list of track names, artists, and songIDs for the items in that playlist
    def playlistItems(self, playlistId):
        results = self.sp.playlist_items(
            playlistId,
            fields="items(track(artists(name),name,id))"
        )
        data = {}
        data['items'] = {}
        list = []
        for song in results['items']:
            itemInfo = dict()
            itemInfo['track'] = song['track']['name']
            itemInfo['artist'] = song['track']['artists'][0]['name']
            itemInfo['songId'] = song['track']['id']
            list.append(itemInfo)
        data['items'] = list
        data['playlistId'] = {}
        data['playlistId'] = playlistId 
        
        return data

    #a Spotify playlist and new playlistId is created if the given ID is None. Lists playlist items using the playlistID. 
    def listItemsOrCreatePlaylist(self, playlistId, playlistTitle):
        if(playlistId == None):
            createdPlaylist = self.createPlaylist(playlistTitle)
            playlistId = createdPlaylist['id']
        
        return self.playlistItems(playlistId)

    #adds item to a spotify playlist given its playlistID and songId
    def addItemToPlaylist(self, playlistId, songId):
        results = self.sp.playlist_add_items(
            playlist_id=playlistId,
            items=songId
        )
        
        return results

    def listPlaylistItems(self, playlistTitle):    
        usersPlaylists = self.listPlaylists()
        playlistId = self.getPlaylistId(usersPlaylists, playlistTitle)
        playlistItems = self.listItemsOrCreatePlaylist(playlistId,playlistTitle)

        return playlistItems

    #lists current user's Spotify playlists
    def printPlaylists(self):
        print("")
        print("Below is a list of your Spotify playlists:")
        print("")
        usersPlaylists = self.listPlaylists()
        if usersPlaylists['items']:
            for playlists in usersPlaylists['items']:
                print(playlists['playlistName'])
            print("") 
        else:
            print("You have no Spotify playlists")
            print("")

        return usersPlaylists       

    def explorePlaylist(self, playlists):
        playlistTitle = None
        playlistTitleLookup = input("Please type the name of the Spotify playlist exactly as seen: ")
        for playlists in playlists['items']:
            if playlistTitleLookup in playlists['playlistName']:
                playlistTitle = playlistTitleLookup
        if playlistTitle:
            playlistItems = self.listPlaylistItems(playlistTitle)
            if playlistItems['items']:
                print("")
                print("Below are the items in your {} playlist.".format(playlistTitle))
                print("")
                for song in playlistItems['items']:
                    print(song['artist'], " - ", song['track'])
                print("")
                return
            else:
                print("")
                print("There are no items in this playlist yet.")
                print("")
                return
        else:
            print(playlistTitleLookup, " does not exist.")
            return self.explorePlaylist(playlists)    


class LinkPlaylist():

    def __init__(self):
        self.yt = Youtube()
        self.spotify = Spotify()
        self.playlistTitle = self.askUserForPlaylistTitle()
        self.linkPlaylist(self.playlistTitle)
    
    #Uses ytmusic library methods to search youtube music for a given artist and song title, returning the videoId of the top result
    def youtubeIdFromArtisAndTitle(self, artistAndTitle):
        ytmusic = YTMusic('headers_auth.json')
        search_results = ytmusic.search(
            artistAndTitle, 
            filter="songs", 
            limit=2, 
            ignore_spelling=True
        )
        videoId = search_results[0]['videoId']
        
        return videoId

    # querys database or uses ytmusicapi library to find the videoId for each song. If the videoId is not already in the database, it adds it
    def addSongsToYoutube(self, listSpotifyPlaylistItems, playlistId):
        record = []
        for song in listSpotifyPlaylistItems['items']:
            songId = song['songId']
            artist = song['artist']
            track = song['track']
            name = artist+" "+track
            videoId = database.videoIdFromSongId(songId)
            if not videoId:
                videoId = self.youtubeIdFromArtisAndTitle(name)
            if videoId:
                if not database.searchYoutubePlaylistId(videoId, playlistId):
                    self.yt.addItemToPlaylist(playlistId, videoId)
            record.append((videoId, songId, artist, track))

        return record

    def addSongstoSpotify(self, youtubeSongAndArtistName, playlistId):
        record = []
        songIds = []
        for song in youtubeSongAndArtistName['songs']:
            videoId = song['videoId']
            artist = song['artist']
            track = song['track']
            songId = database.songIdFromVideoId(videoId)
            if songId:
                info = database.songDataFromVideoId(videoId)
                artist = info[0][0]
                track = info[0][1]
            else:
                name = artist+" "+track
                search_results = self.spotify.sp.search(name, limit=1, type='track')
                if(search_results['tracks']['items']):
                    artist = search_results['tracks']['items'][0]['artists'][0]['name']
                    track = search_results['tracks']['items'][0]['name']
                    songId = search_results['tracks']['items'][0]['id']
                else:
                    search_results = self.spotify.sp.search(track, limit=1, type='track')
                    if(search_results['tracks']['items']):
                        artist = search_results['tracks']['items'][0]['artists'][0]['name']
                        track = search_results['tracks']['items'][0]['name']
                        songId = search_results['tracks']['items'][0]['id']
            if songId:
                if not database.searchSpotifyPlaylistId(songId, playlistId):
                    songIds.append(songId)
                    record.append((videoId, songId, artist, track))                
        if songIds:
            self.spotify.addItemToPlaylist(playlistId, songIds)
        
        return record

    def explorePlaylist(self, youtubePlaylists, spotifyPlaylists):
        specifyPlaylistResponse = input("Please specify if you would like to explore a Youtube or Spotify playlist ('youtube'/'spotify'): ")
        specifyPlaylistResponse = specifyPlaylistResponse.lower()
        if specifyPlaylistResponse == "youtube":
            self.yt.explorePlaylist(youtubePlaylists)
            return
        if specifyPlaylistResponse == "spotify":
            self.spotify.explorePlaylist(spotifyPlaylists)
            return
        else:
            print(specifyPlaylistResponse, " is not an option.")
            return self.explorePlaylist(youtubePlaylists, spotifyPlaylists)

    def exploreLinkedPlaylists(self, linkedPlaylists):
        playlistTitle = None
        playlistTitleLookup = input("Please type the name of a playlist exactly as seen: ")
        for playlists in linkedPlaylists:
            if playlistTitleLookup in playlists[1]:
                playlistTitle = playlistTitleLookup         
        if playlistTitle:
            database.songDataFromLinkedPlaylist(playlistTitle)
        else:
            print(playlistTitleLookup, " does not exist.")
            return self.continueExploringLinkedPlaylists(linkedPlaylists)

    def continueExploringPlaylists(self):
        continueExploring = True
        response = input("Would you like to see the items of any of your existing Youtube or Spotify playlists ('yes'/'no')?: ")
        response = response.lower()
        if response == "no":
            continueExploring = False
            return continueExploring
        if response == "yes":
            return continueExploring
        else:
            print(response, " is not an option.")
            return self.continueExploringPlaylists()

    def continueExploringLinkedPlaylists(self):
        continueExploring = True
        response = input("Would you like to see the items of any of your existing linked playlists ('yes'/'no')?: ")
        response = response.lower()
        if response == "no":
            continueExploring = False
            return continueExploring
        if response == "yes":
            return continueExploring
        else:
            print(response," is not an option.")
            return self.continueExploringLinkedPlaylists()

    def askUserForPlaylistTitle(self):
        linkedPlaylists = database.linkedPlaylistPopulated()
        if(not linkedPlaylists):
            print("There are no linked playlists yet.")
            print("")
            while self.continueExploringPlaylists():
                youtubePlaylists = self.yt.printPlaylists()
                spotifyPlaylists = self.spotify.printPlaylists()
                self.explorePlaylist(youtubePlaylists, spotifyPlaylists)
            playlistTitle = input("Please type the name of a playlist exactly as seen or the name of a new playlist you want to create and be linked: ")
            return playlistTitle          
        else:
            while self.continueExploringLinkedPlaylists():
                database.showLinkedPlaylists(linkedPlaylists)
                self.exploreLinkedPlaylists(linkedPlaylists)
            print("")
            while self.continueExploringPlaylists():
                youtubePlaylists = self.yt.printPlaylists()
                spotifyPlaylists = self.spotify.printPlaylists()
                self.explorePlaylist(youtubePlaylists, spotifyPlaylists)
            playlistTitle = input("Please type the name of a playlist exactly as seen or the name of a new playlist you want to create and be linked: ")
            return playlistTitle      
            response = input("Would you like to add songs to view")

    def linkPlaylist(self, playlistTitle):
        youtubePlaylistItems = self.yt.listPlaylistItems(playlistTitle)
        spotifyPlaylistItems = self.spotify.listPlaylistItems(playlistTitle)
        youtubeItemInfo = self.yt.youtubeSongAndArtistName(youtubePlaylistItems)
        spotifySong_record = self.addSongsToYoutube(spotifyPlaylistItems, youtubePlaylistItems['playlistId'])
        youtubeSong_record = self.addSongstoSpotify(youtubeItemInfo, spotifyPlaylistItems['playlistId'])
        linkedPlaylist_id = database.searchLinkedPlaylist(playlistTitle)
        if not linkedPlaylist_id:
            linkedPlaylist_record = (playlistTitle, youtubePlaylistItems['playlistId'], spotifyPlaylistItems['playlistId'])
            linkedPlaylist_id = database.insertLinkedPlaylistToDb(database.insert_linkedPlaylist_query, linkedPlaylist_record)
        combinedSongs_record = spotifySong_record + youtubeSong_record
        for song in combinedSongs_record:
            songMetadata_id = database.searchSongMetadata(song[2], song[3])
            if not songMetadata_id:
                songMetadata_record = (song[2], song[3])
                songMetadata_id = database.insertSongMetadataToDb(database.insert_songMetadata_query, songMetadata_record)
            song_id = database.searchSong(songMetadata_id)
            song_record = (linkedPlaylist_id, songMetadata_id)
            if not song_id:
                database.insertSongToDb(database.insert_song_query, song_record)
            if (song[0] is not None) and not database.searchYoutubeVideoId(song[0]):
                youtubeVideoId_record = (song[0], songMetadata_id)
                database.insertYoutubeVideoIdToDb(database.insert_youtubeVideoId_query, youtubeVideoId_record)
            if (song[1] is not None) and not database.searchSpotifySongId(song[1]):
                spotifySongId_record = (song[1], songMetadata_id)
                database.insertSpotifySongIdToDb(database.insert_spotifySongId_query, spotifySongId_record)

        print("")
        print("The playlist has been successfully linked!")

        return


if __name__ == '__main__':
    linkedPlaylist = LinkPlaylist()