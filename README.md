# YouTube-Spotify-Playlist

Links a playlist between YouTube and Spotify.

Uses OAuth 2.0 to get permission to access and edit playlist information. 

Features include listing user's playlists, listing the items in any of user's playlists, creating playlists, adding items to playlists.

Uses youtube_dl library to find song metadata from youtube links via webscraping. Uses ytmusicapi library and spotify song metadata to search YouTube Music for the corresponding YouTube links.

Uses MySQL to create a database to store linked playlist titles and Ids, song metadata, and youtube and spotify ids. Database queries reduces YouTube quota usage, API requests, and webscraping.
