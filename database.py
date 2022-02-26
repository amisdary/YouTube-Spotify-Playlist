from getpass import getpass
from mysql.connector import connect, Error


database_name = "playlist_project"
show_db_query = "SHOW DATABASES"
show_table_query = "SHOW TABLES"
create_db_query = "CREATE DATABASE database_name"
delete_db_query = "DELETE DATABASE database_name"


create_linkedPlaylist_table_query = """
	CREATE TABLE linkedPlaylist(
	id INT AUTO_INCREMENT PRIMARY KEY,
	title VARCHAR(100),
	youtubePlaylistId VARCHAR(100),
	spotifyPlaylistId VARCHAR(100)
	)
"""
create_songMetadata_table_query = """
	CREATE TABLE songMetadata(
	id INT AUTO_INCREMENT PRIMARY KEY,
	artist VARCHAR(100),
	track VARCHAR(100)
	)
"""
create_youtubeVideoId_table_query = """
	CREATE TABLE youtubeVideoId(
	videoId VARCHAR(100) PRIMARY KEY,
	songMetadata_id INT,
	FOREIGN KEY (songMetadata_id) REFERENCES songMetadata(id)
	)
"""
create_spotifySongId_table_query = """
	CREATE TABLE spotifySongId(
	songId VARCHAR(100) PRIMARY KEY,
	songMetadata_id INT, 
	FOREIGN KEY (songMetadata_id) REFERENCES songMetadata(id)
	)
"""
create_song_table_query = """
	CREATE TABLE song(
	id INT AUTO_INCREMENT PRIMARY KEY,
	linkedPlaylist_id INT,
	songMetadata_id INT,
	FOREIGN KEY (linkedPlaylist_id) REFERENCES linkedPlaylist(id),
	FOREIGN KEY (songMetadata_id) REFERENCES songMetadata(id)
	)
"""


insert_linkedPlaylist_query = """
	INSERT INTO linkedPlaylist
	(title, youtubePlaylistId, spotifyPlaylistId)
	VALUES ( %s, %s, %s)
"""
select_linkedPlaylist_query = """SELECT id, title FROM linkedPlaylist"""

insert_songMetadata_query = """
	INSERT INTO songMetadata
	(artist, track)
	VALUES (%s, %s)
"""
select_songMetadata_query = """SELECT id FROM songMetadata"""

insert_youtubeVideoId_query = """
	INSERT INTO youtubeVideoId
	(videoId, songMetadata_id)
	VALUES (%s, %s)
"""
select_youtubeVideoId_query = """SELECT videoId FROM youtubeVideoId"""

insert_spotifySongId_query = """
	INSERT INTO spotifySongId
	(songId, songMetadata_id)
	VALUES (%s, %s)
"""
select_spotifySongId_query = """SELECT songId FROM spotifySongId"""

insert_song_query = """
	INSERT INTO song
	(linkedPlaylist_id, songMetadata_id)
	VALUES (%s, %s)
"""
select_song_query = """SELECT id FROM song"""



def deleteDatabase():
	with connection.cursor() as cursor:
		cursor.execute(delete_db_query)
		connection.commit()

	return

def deleteTable(tableName):
	with connection.cursor() as cursor:
		cursor.execute("DROP TABLE {}".format(tableName))
		connection.commit()

	return

def deleteAllTables():
	with connection.cursor() as cursor:
		cursor.execute("DROP TABLE youtubeVideoId")
		cursor.execute("DROP TABLE spotifySongId")
		cursor.execute("DROP TABLE song")
		cursor.execute("DROP TABLE songMetadata")
		cursor.execute("DROP TABLE linkedPlaylist")
		connection.commit()
	return	

def deleteTableContents(tableName):	
	with connection.cursor() as cursor:
		cursor.execute("DELETE FROM {}".format(tableName))
		connection.commit()

	return
		
def showAllTables():
	with connection.cursor() as cursor:
		cursor.execute(show_table_query)
		list = cursor.fetchall()
		if len(list) > 0:
			print(list)
		else:
			print("There are no tables yet")
		
		return 

def describeTable(tableName):
	with connection.cursor() as cursor:
		cursor.execute("DESCRIBE {}".format(tableName))
		list = cursor.fetchall()
		for row in list:
			print(row)

	return		

def createTables():
	with connection.cursor() as cursor:
		cursor.execute(show_table_query)
		list = cursor.fetchall()	
		if ("linkedPlaylist",) not in list:
			cursor.execute(create_linkedPlaylist_table_query)
			connection.commit()
		if ("songMetadata",) not in list:
			cursor.execute(create_songMetadata_table_query)
			connection.commit()
		if ("youtubeVideoId",) not in list:
			cursor.execute(create_youtubeVideoId_table_query)
			connection.commit()			
		if ("spotifySongId",) not in list:
			cursor.execute(create_spotifySongId_table_query)
			connection.commit()	
		if ("song",) not in list:
			cursor.execute(create_song_table_query)
			connection.commit()						

	return 

def showTableContents(tableName):
	with connection.cursor() as cursor:
		cursor.execute("SELECT * FROM {}".format(tableName))
		for x in cursor:
			print(x)	

def showAllTableContents():
	with connection.cursor() as cursor:
		cursor.execute(show_table_query)
		list = cursor.fetchall()
		for row in list:
			tableName = row[0]
			cursor.execute("SELECT * FROM {}".format(tableName))
			for x in cursor:
				print(x)

	return

# def getLinkedPlaylistId(playlistTitle):
# 	with connection.cursor() as cursor:
# 		cursor.execute("SELECT id, title FROM linkedPlaylist")

def insertLinkedPlaylistToDb(insert_linkedPlaylist_query, linkedPlaylist_record):
	with connection.cursor() as cursor:
		cursor.execute(insert_linkedPlaylist_query, linkedPlaylist_record)
		connection.commit()
		return cursor.lastrowid

def insertSongMetadataToDb(insert_songMetadata_query, songMetadata_record):
	with connection.cursor() as cursor:
		cursor.execute(insert_songMetadata_query, songMetadata_record)
		connection.commit()
		return cursor.lastrowid

def insertYoutubeVideoIdToDb(insert_youtubeVideoId_query, youtubeVideoId_record):
	with connection.cursor() as cursor:
		cursor.execute(insert_youtubeVideoId_query, youtubeVideoId_record)
		connection.commit()
		return

def insertSpotifySongIdToDb(insert_spotifySongId_query, spotifySongId_record):
	with connection.cursor() as cursor:
		cursor.execute(insert_spotifySongId_query, spotifySongId_record)
		connection.commit()
		return

def insertSongToDb(insert_song_query, song_record):
	with connection.cursor() as cursor:
		cursor.execute(insert_song_query, song_record)
		connection.commit()
		return		



def linkedPlaylistPopulated():
	with connection.cursor() as cursor:
		cursor.execute(select_linkedPlaylist_query)
		list = cursor.fetchall()
		if len(list) > 0:
			return list
		else:
			return False

def showLinkedPlaylists(list):
	print("Below is a list of your linked playlists:")
	print("")
	for row in list:
		title = row[1]
		print(title)
	print("")
	return

def searchLinkedPlaylist(playlistTitle):
	with connection.cursor() as cursor:
		cursor.execute(select_linkedPlaylist_query)
		list = cursor.fetchall()
		for row in list:
			if playlistTitle == row[1]:
				linkedPlaylist_id = row[0]
				return linkedPlaylist_id	
		return False

def searchSongMetadata(artist, track):
	with connection.cursor() as cursor:
		cursor.execute("SELECT * FROM songMetadata")
		list = cursor.fetchall()
		for row in list:
			if (row[1] == artist) and (row[2] == track):
				songMetadata_id = row[0]
				return songMetadata_id
		return False

def searchSong(songMetadata_id):
	with connection.cursor() as cursor:
		cursor.execute("SELECT id, songMetadata_id FROM song")
		list = cursor.fetchall()
		for row in list:
			if row[1] == songMetadata_id:
				song_id = row[0]
				return song_id
		return False

def songDataFromLinkedPlaylist(playlistTitle):
	query = """SELECT artist, track
			   FROM linkedPlaylist
			   INNER JOIN song
			       ON linkedPlaylist.title = '{}' AND linkedPlaylist.id = song.linkedPlaylist_id
		       INNER JOIN songMetadata
		       	   ON song.songMetadata_id = songMetadata.id
	"""
	query = query.format(playlistTitle)
	with connection.cursor() as cursor:
		cursor.execute(query)
		list = cursor.fetchall()
		if list:
			print("")
			print("Below is a list of songs in your linked playlists:")
			print("")
			for row in list:
				print(row[0]," - ",row[1])
			print("")
		else:
			print("")
			print("There are no songs in this playlist yet.")
			print("")
		return

def searchYoutubeVideoId(videoId):
	with connection.cursor() as cursor:
		cursor.execute(select_youtubeVideoId_query)
		list = cursor.fetchall()
		for row in list:
			if videoId == row[0]:
				return True	
		return False

def songDataFromVideoId(videoId):
	query = """SELECT artist, track 
			   FROM songMetadata, youtubeVideoId 
			   WHERE youtubeVideoId.songMetadata_id = songMetadata.id AND youtubeVideoId.videoId = '{}'
	"""
	query = query.format(videoId)
	with connection.cursor() as cursor:
		cursor.execute(query)
		list = cursor.fetchall()
		return list		

def searchSpotifySongId(songId):
	with connection.cursor() as cursor:
		cursor.execute(select_spotifySongId_query)
		list = cursor.fetchall()
		for row in list:
			if songId == row[0]:
				return True	
		return False				

def songDataFromSongId(songId):
	with connection.cursor() as cursor:
		query = """SELECT artist, track 
				   FROM songMetadata, spotifySongId 
				   WHERE spotifySongId.songMetadata_id = songMetadata.id AND spotifySongId.songId = '{}'
		"""
		query = query.format(songId)
		cursor.execute(query)
		list = cursor.fetchall()
		return list	
		 
def videoIdFromSongId(songId):	
	with connection.cursor() as cursor:
		query = """SELECT videoId
				   FROM spotifySongId
				   INNER JOIN songMetadata
				       ON songMetadata.id = spotifySongId.songMetadata_id AND spotifySongId.songId = '{}'
				   INNER JOIN youtubeVideoId
					   ON youtubeVideoId.songMetadata_id = songMetadata.id
		"""
		query = query.format(songId)
		cursor.execute(query)
		list = cursor.fetchall()
		if list:
			return list[0][0]
		else:
			return None

def songIdFromVideoId(videoId):
	with connection.cursor() as cursor:
		query = """SELECT songId
				   FROM youtubeVideoId
				   INNER JOIN songMetadata
				       ON songMetadata.id = youtubeVideoId.songMetadata_id AND youtubeVideoId.videoId = '{}'
				   INNER JOIN spotifySongId
					   ON spotifySongId.songMetadata_id = songMetadata.id
		"""
		query = query.format(videoId)
		cursor.execute(query)
		list = cursor.fetchall()
		if list:
			return list[0][0]	
		else:
			return None	

def searchYoutubePlaylistId(videoId, youtubePlaylistId):
	with connection.cursor() as cursor:
		query = """SELECT youtubePlaylistId 
				   FROM youtubeVideoId
				   INNER JOIN songMetadata
					   ON songMetadata.id = youtubeVideoId.songMetadata_id AND youtubeVideoId.videoId = '{}'
				   INNER JOIN song
					   ON song.songMetadata_id = songMetadata.id
				   INNER JOIN linkedPlaylist
					   ON linkedPlaylist.id = song.linkedPlaylist_id
		"""
		query = query.format(videoId)
		cursor.execute(query)
		list = cursor.fetchall()
		for row in list:
			if youtubePlaylistId == row[0]:
				return True
		return False		 

def searchSpotifyPlaylistId(songId, spotifyPlaylistId):
	with connection.cursor() as cursor:
		query = """SELECT spotifyPlaylistId 
				   FROM spotifySongId
				   INNER JOIN songMetadata
				       ON songMetadata.id = spotifySongId.songMetadata_id AND spotifySongId.songId = '{}'
				   INNER JOIN song
					   ON song.songMetadata_id = songMetadata.id
				   INNER JOIN linkedPlaylist
					   ON linkedPlaylist.id = song.linkedPlaylist_id
		"""
		query = query.format(songId)
		cursor.execute(query)
		list = cursor.fetchall()
		for row in list:
			if spotifyPlaylistId == row[0]:
				return True
		return False



try:
	connection = connect(
		host='localhost',
		user='root',
		password=getpass("Enter password: "),
	)
	with connection.cursor() as cursor:
		cursor.execute(show_db_query)
		list = cursor.fetchall()
		if (database_name,) not in list:
			cursor.execute(create_db_query)
	connection = connect(
		host='localhost',
		user='root',
		password=getpass("Enter password: "),
		database=database_name,
	)
	createTables()
except Error as e:
	print(e)



#database.close()








