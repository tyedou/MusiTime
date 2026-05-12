
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
from spotipy import util
from dotenv import load_dotenv
import os
from utils import Song

load_dotenv()
SPOTIPY_CLIENT_ID = os.getenv("CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("CLIENT_SECRET")
redirect_uri = "http://127.0.0.1:8888/callback"
OFFSET = 120 # this offset is what is used in the determining songs to add to playlist

# set up a spotify class so that we can access user information
# uses client_id for the app and client_secret to connect

# OAuth Method for accessing Spotify Data (individual user accounts, browser verification required)
scope = ["playlist-modify-public", "playlist-modify-private", "user-top-read", "playlist-read-private", "user-library-read", "user-read-private", "user-read-email"]
def OAuth(user: str):
    global sp
    token = util.prompt_for_user_token(username=user, scope=scope, client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=redirect_uri, cache_path=".cache")
    sp = Spotify(auth=token)
    return sp
# Client Credential Method for accessing Spotify Data (any user accounts, no outside browser opened)
def ClientCred():
    sp = Spotify(auth_manager=SpotifyClientCredentials(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET))
    return sp

# to get username
# go to spotify.com --> account settings --> edit profile 
# spotify ID 

# 04/17/24 -- Works
def get_song_duration(track: str) -> int:
    # can give info of track by ID or URL or URI
    trackInfo = sp.track(track)
    duration_ms = trackInfo["duration_ms"]
    total_seconds = duration_ms // 1_000        # total seconds is acquired here, everything below is extra (optional)
    # mins, secs = divmod(total_seconds, 60)
    # print("{:0>2}:{:0>2}".format(mins, secs))
    # print(total_seconds)
    return total_seconds

# 04/17/24 -- Works
def get_length_of_playlist(playlist_id) -> int: # accuratley working 
    total = 0
    playlist = sp.playlist(playlist_id)
    for item in playlist['tracks']['items']:
        # print(item['track']['id'])
        total += get_song_duration(item['track']['id'])
    # print(str(total) + " total seconds in the playlist, " + playlist['name'])
    return total
# ON A TEST RUN
# get_length_playlist returned the correct seconds in the playlist offset by ~3 minutes
# we can implement a "grace offset" which allows our program to be off by a given time (EX: 5 Minutes)

# 04/17/24 -- Not Tested
def is_valid(playlist_length: int, goal_length: int) -> bool:
        return playlist_length == goal_length
    
# 04/17/24 -- Not Tested  
def create_playlist() -> None:
    user_has = _user_has_playlist(user, "MusiTime")  
    if user_has is not None:
        _clear_playlist(user_has)
        # print("Playlist wiped!")
        return
    else:
        sp.user_playlist_create(user=user, public=True, name="MusiTime", collaborative=False,description="Playlist made by MusiTime")
        # print("Successfully created MusiTime Playlist!")
        return
    
# 04/17/24 -- Works
def _user_has_playlist(user_id, playlist_name):
    # paginate through the authenticated user's own playlists (/me/playlists);
    # /users/{id}/playlists returns 403 for apps still in Developer Mode
    offset = 0
    while True:
        playlists = sp.current_user_playlists(limit=50, offset=offset)
        items = playlists.get('items', [])
        for playlist in items:
            if playlist['name'] == playlist_name:
                return playlist['id']
        if len(items) < 50:
            return None
        offset += 50
# 04/17/24 -- Works
def _clear_playlist(playlist_id):   # working
    # Get all tracks in the playlist
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']
    # Iterate over each track and remove it from the playlist
    while tracks:
        for track in tracks:
            sp.playlist_remove_all_occurrences_of_items(playlist_id, [track['track']['id']])
        results = sp.playlist_tracks(playlist_id)
        tracks = results['items']
    # print("_clear_playlist ends here...")
        
# 04/17/24 -- Works        
def _get_OPTION(songs: list, OPTION: str) -> list: # function returns id's of songs in given playlist
    tracks = songs["items"]
    return_list = []
    for track in tracks:
        return_list.append(track[OPTION])
    # print("_get_OPTION ends here...")
    return return_list
# 04/17/24 -- Works
def add_to_playlist(songs: list) -> None: # always the MusiTime playlist; assumes list being passed is ID's
    print(f"[add_to_playlist] user={user!r} count={len(songs)} ids={songs[:5]}...")
    create_playlist()
    playlist_id = _user_has_playlist(user, "MusiTime")
    print(f"[add_to_playlist] playlist_id={playlist_id!r}")
    if not songs:
        print("[add_to_playlist] WARNING: empty song list — playlist will be empty")
        return
    sp.user_playlist_add_tracks(user=user, playlist_id=playlist_id, tracks=songs, position=None)
    print(f"[add_to_playlist] added {len(songs)} tracks")



def get_artist_id(artists):
    artist_ids = []
    for artist in artists:
        search_results = sp.search(q="artist:" + artist, type='artist')
        if 'artists' in search_results and 'items' in search_results['artists']:
            for item in search_results['artists']['items']:
                if (len(artist_ids) < 5):
                    artist_ids.append(item['id'])
    return artist_ids
# Spotify deprecated /v1/recommendations in Nov 2024. The functions below now
# build a candidate pool via search / artist top-tracks instead of the recs API.
def rec_artists_songs(artists: list) -> list:
    artist_ids = get_artist_id(artists)
    recs = []
    seen = set()
    for aid in artist_ids:
        try:
            results = sp.artist_top_tracks(aid)
        except Exception:
            continue
        for track in results.get('tracks', []):
            tid = track.get('id')
            if tid and tid not in seen:
                seen.add(tid)
                recs.append(tid)
    return recs

def rec_genre_songs(genres: list) -> list:
    recs = []
    seen = set()
    for genre in genres:
        genre = genre.strip()
        if not genre:
            continue
        success_query = None
        for query in (f'genre:"{genre}"', genre):
            try:
                results = sp.search(q=query, type='track', limit=10)
                print(f"[rec_genre_songs] query={query!r} returned {len(results.get('tracks', {}).get('items', []))} items")
            except Exception as e:
                print(f"[rec_genre_songs] query={query!r} failed: {e}")
                continue
            items = results.get('tracks', {}).get('items', [])
            if items:
                success_query = query
                for track in items:
                    tid = track.get('id')
                    if tid and tid not in seen:
                        seen.add(tid)
                        recs.append(tid)
                break
        # paginate to grow the pool past the dev-mode per-call cap
        if success_query:
            for offset in (10, 20, 30, 40):
                try:
                    results = sp.search(q=success_query, type='track', limit=10, offset=offset)
                except Exception:
                    break
                items = results.get('tracks', {}).get('items', [])
                if not items:
                    break
                for track in items:
                    tid = track.get('id')
                    if tid and tid not in seen:
                        seen.add(tid)
                        recs.append(tid)
    return recs

def rec_ttracks_songs() -> list:
    top = sp.current_user_top_tracks(limit=20, time_range="long_term")
    artist_ids = []
    seen_artists = set()
    for item in top.get('items', []):
        for artist in item.get('artists', []):
            aid = artist.get('id')
            if aid and aid not in seen_artists and len(artist_ids) < 5:
                seen_artists.add(aid)
                artist_ids.append(aid)
    recs = []
    seen = set()
    # seed with the user's own top tracks
    for item in top.get('items', []):
        tid = item.get('id')
        if tid and tid not in seen:
            seen.add(tid)
            recs.append(tid)
    # expand with top tracks from those artists
    for aid in artist_ids:
        try:
            results = sp.artist_top_tracks(aid)
        except Exception:
            continue
        for track in results.get('tracks', []):
            tid = track.get('id')
            if tid and tid not in seen:
                seen.add(tid)
                recs.append(tid)
    return recs
    
# 04/17/24 -- works-ish; not perfect, not bad
# THIS IS WHERE THE ALGORITHM IS NEEDED
def find_songs_in_length(recs: list, goal_length: int, long_to_short: bool = None) -> list:
    if goal_length <= 0:                # EDGE CASE: user provides length less than or equal to 0
        return ["43JK3XJKQ5MJ7ddlF0ylUX"]
    if goal_length > 300:               # EDGE CASE: user wants a playlist longer than we can provide
        goal_length = 300
    goal_length *= 60           # increase goal_length to account for seconds rather than minutes (EX: 20 minutes = 1200 seconds)
    
    total_length = 0
    song_to_add = []
    
    # changing here now
    songs = []
    for song in recs:
        songs.append(Song(get_song_duration(song), song))
    # song.time and song.id hold respective songs id and time
    # we can use this to call quicksort on the associated times 
    # and use the ids as the songs we are going to return back to the program
    
    def quicksort(arr, rev: bool): # sort the songs
        if len(arr) <= 1:
            return arr
        else:
            pivot = arr[0]
            left = [x for x in arr[1:] if x.time < pivot.time]
            right = [x for x in arr[1:] if x.time >= pivot.time]
            if rev:
                return quicksort(right, rev) + [pivot] + quicksort(left, rev)
            else:
                return quicksort(left, rev) + [pivot] + quicksort(right, rev)
    if long_to_short is not None:       # if long_to_short is None, it acts as a "dont care" order of the playlist
        songs = quicksort(songs, long_to_short)
    for song in songs:
        if song.time + total_length <= goal_length + OFFSET:
            total_length += song.time 
            song_to_add.append(song.id)
    return song_to_add

    
    
    return song_to_add
# 04/17/24 -- Works
def set_up(username: str): # FOR USAGE WITH: flask_TEST.py
    global sp
    global user
    OAuth(user=username)
    me = sp.current_user()
    user = me['id']
    print(f"[set_up] form_user={username!r} authenticated_as={user!r} country={me.get('country')!r} product={me.get('product')!r}")
    return sp

# 04/17/24 -- Works
def main():                 # FOR USAGE WITH: main.py; DRIVER CODE to TEST functions
    global user
    user = "edouardtyler"
    sp=OAuth(user=user)
    recs = rec_ttracks_songs()
    # recs = rec_genre_songs(["pop", "country", "hip-hop"])
    # recs = rec_artists_songs(['Morgan Wallen', 'Juice WRLD', 'Zach Bryan'])
    # get_artist_id(['Morgan Wallen', 'Juice WRLD', 'Zach Bryan'])
    songs = find_songs_in_length(recs, 300)
    add_to_playlist(songs)
if __name__ == '__main__':
    main()
