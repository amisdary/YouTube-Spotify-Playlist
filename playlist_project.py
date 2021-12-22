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

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

#Scope = "https://www.googleapis.com/auth/youtube" if modyfying YouTube account
scopes = ["https://www.googleapis.com/auth/youtube"]

def main():

    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "youtube_client_secret.json"

    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_console()
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    #requests from YouTube API a list of the current user's YouTube playlists
    #part/fields used to filter data and only retrieve relevant information
    def listUsersPlaylists():
        listUsersPlaylists = youtube.playlists().list(
            part="snippet",
            fields="items(id,snippet(title))",
            maxResults=25,
            mine=True
        )
        return listUsersPlaylists.execute()

    #searches current user's YouTube playlists for a specified playlist title 
    #and returns its playlist ID
    def getPlaylistId(playlistTitle):
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
    
    #uses a specified playlist ID and returns a list of items in that playlist
    def listPlaylistItems(playlistId):
        listPlaylistItems = youtube.playlistItems().list(
            part="snippet",
            fields="items(snippet(title,position))",
            maxResults=25,
            playlistId=playlistId
        )
        return listPlaylistItems.execute()
    
    #Lists items of specified playlist or create new playlist if one does not exist
    def listItemsOrCreatePlaylist(playlistId, playlistTitle):
        if(playlistId == None):
            createdPlaylist = createPlaylist(playlistTitle)
            playlistId = createdPlaylist['id']
            return listPlaylistItems(playlistId)

        else:
            return listPlaylistItems(playlistId)
    
    usersPlaylists = listUsersPlaylists()
    #only line of code that user would change
    playlistTitle = "Spotify Songs"
    playlistId = getPlaylistId(playlistTitle)
    playListItems = listItemsOrCreatePlaylist(playlistId, playlistTitle)
    
    print(playListItems)

    #read json file, convert it to a dictionary in python, print last name, print list of skills in alphabetical order

if __name__ == '__main__':
    main()
