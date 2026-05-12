from flask import Flask, redirect, url_for, request, render_template, flash
from main import *

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/update', methods=['POST'])
def login():
    if request.method == 'POST':
        user = request.form['nm']
        sp = set_up(user)
        length = int(request.form['length'])
        long_to_short = bool(request.form['long_to_short'])
        recomendations = None
        genres = (request.form['genres']).split(",")
        artists = (request.form['artists']).split(",")
        print(f"[update] genres={genres} artists={artists} length={length} long_to_short={long_to_short}")
        if '' not in genres:
            recomendations = rec_genre_songs(genres)
            print(f"[update] used genre recs, pool size={len(recomendations)}")
        elif '' not in artists:
            recomendations = rec_artists_songs(artists)
            print(f"[update] used artist recs, pool size={len(recomendations)}")
        else:
            recomendations = rec_ttracks_songs()
            print(f"[update] used top-tracks recs, pool size={len(recomendations)}")
        songs = find_songs_in_length(recomendations, length, long_to_short)
        print(f"[update] selected {len(songs)} songs for playlist")
        add_to_playlist(songs)
        return render_template("index.html")
    else:
        exit()

if __name__ == '__main__':
	app.run(debug=True, port=5002)
