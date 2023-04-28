from flask import Flask, request, url_for, session, redirect
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import time
from random import randint
import lyricsgenius
import math
import spacy
nlp = spacy.load("en_core_web_sm")
import en_core_web_sm
nlp = en_core_web_sm.load()

# if the random lyrics includes the artist's name, stop it before or begin it after

 
app = Flask(__name__)




app.secret_key = "something_random"
app.config['SESSION_COOKIE_NAME'] = 'Lydias Cookie'
TOKEN_INFO = 'token_info'



@app.route('/')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route('/redirect')
def redirectPage():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('getRandomTrack', _external=True))


@app.route('/getTracks')
def getTracks(): # gets the user's top tracks with a given time range
    # this isn't really used but it is a good template for getRandomTrack()
    try:
        token_info = get_token()
    except:
        print("user not logged in")
        return redirect('/')
    sp = spotipy.Spotify(auth=token_info['access_token'])
    all_songs = []
    iteration = 0
    while True:
        items = sp.current_user_top_tracks(limit=50, offset=0, time_range="short_term")['items']
        iteration += 1
        all_songs += items # items are objects with many values, all_songs is a list of these objects
        if len(items) < 50:
            break
        song_list = ''
        for i in all_songs:
            song_list = song_list + str(all_songs.index(i) + 1) + '. ' + i["name"] + " \n" # "name" gets the name of the track
        return song_list


# list of items to delete from the lyrics that are automatically included by genius
delete_list = [ "[Chorus]", "[Verse", "[Verse]", "[Pre-Chorus]", "[Chorus:",
               "[Post-Chorus]", "[Bridge]", "[Break]", 
               "1]", "2]", "3]","4]","5]", "[", "]", ":"]

# list of items to delete that show up at the beginning. these get deleted, along with any
# extra words or characters that come before it so that the lyrics actually start with real lyrics
beg_del_list = [ "Lyrics[Intro]", "Lyrics[Intro]:", "Lyrics[Verse", "Lyrics[Intro:"]


# the code counts capital letters as the beginning of a line. however, these words that 
# are automatically capitalized should not be considered the beginning of a line because they often aren't
# this does not include proper nouns (this comes later)
i_list = [ "I", "I've", "I'm", "I'd", "I'll"]



@app.route('/getRandomTrack')    
def getRandomTrack():
    try:
        token_info = get_token()
    except:
        print("user not logged in")
        return redirect('/')
    sp = spotipy.Spotify(auth=token_info['access_token'])
    rand = randint(0, 49) # random integer from 0 to 49 to use as an index for the list of top songs
    rand_song = sp.current_user_top_tracks(limit=1, offset=rand, time_range="short_term")["items"] # code seems to run fin without the "items" = index but i am too afraid to remove it so it's staying there
    global song_name
    song_name = rand_song[0]["name"] # gets the name of the song
    global artist
    artist = str(rand_song[0]["artists"][0]["name"]) # gets the artist of the song
    return generateLyrics(song_name)


@app.route('/getRandomTrackNoSpotify')
def getRandomTrackNoSpotify():
    return { 'lyric': 'Coming soon!' }


@app.route('/generateLyrics')
def generateLyrics(song): 
    api_key = '27c90b32da6bcdcdf18c588780d97e5a'
    genius = lyricsgenius.Genius(api_key)
    song = genius.search_song(song, get_full_info=False)
    str_lyrics = str(song.lyrics)
    list_lyrics = str_lyrics.split()
    global artist
    if artist in song.artist:
        artist = song.artist
    global song_and_artist
    song_and_artist = song_name + " by " + artist # combines the name and artist of the song



    print(artist)
    print(song.artist)


    proper_nouns = []
    words = nlp(" ".join(list_lyrics))
    for w in words:
        if w.pos_ == "PROPN":
            proper_nouns.append(w.text)


    if "Cleanup" in list_lyrics:
        print("not actually lyrics")
        return getRandomTrack()

    if artist not in song.artist:
        print("artist doesnt match")
        return getRandomTrack()


# elements at the beginning of the song to delete      

    for elem in beg_del_list:
        for item in list_lyrics:
            if elem == item:
                del_idx = list_lyrics.index(item)
                list_lyrics = list_lyrics[(del_idx + 1):]



                


# elements in the middle of the songs to delete

    for elem in delete_list:
        for item in list_lyrics:
            if elem == item:
                list_lyrics.remove(item)
    




# deletes items that has elements within it that need to be gone



    for item in list_lyrics:
        for elem in beg_del_list:
            if elem in item:
                del_idx = list_lyrics.index(item)
                list_lyrics = list_lyrics[:(del_idx)] + list_lyrics[(del_idx + 1):]



    for item in list_lyrics:
        for elem in delete_list:
            if elem in item:
                item_idx = list_lyrics.index(item)
                list_lyrics[item_idx] = ""
                break




    list_lyrics = list_lyrics[4:-15]
    for item in list_lyrics:
        if "$" in item and item != "A$AP":
            dollar_index = list_lyrics.index(item)
            list_lyrics = list_lyrics[:(dollar_index - 7)] + list_lyrics[(dollar_index + 3):]



    
    hello = len(list_lyrics)
    end_index = randint(hello-math.ceil(hello * 0.75), hello)
    beg_index = end_index - 10





#making sure that the lyrics begin at the beginning of a phrase or line

    while list_lyrics[beg_index].islower() == True:
        if list_lyrics[beg_index] in i_list or list_lyrics[beg_index] in proper_nouns or '"' in list_lyrics[beg_index] or "'" in list_lyrics[beg_index]:
            return
        beg_index += 1


    
# making sure that the lyrics end at the end of a phrase or line

    if end_index +1 < len(list_lyrics):
        while list_lyrics[end_index + 1].islower() == True or list_lyrics[end_index + 1] in i_list or list_lyrics[end_index + 1] in proper_nouns or '"' in list_lyrics[end_index + 1]:
            end_index += 1
    random_lyrics = list_lyrics[beg_index:end_index+1]
    if "You might also" in random_lyrics:
        random_lyrics.replace("You might also", "this is a test")
    random_lyrics = " ".join(random_lyrics)



   # new_page = '<body className="App" style="background-color:#c7d8faab; color: #647bbe; font-family: Arial"> <p> "   ˚　　　　  ੈ✧˳·˖✶✦　　　.　　. 　 ˚　.　　　　　 . ✦　　　 　˚　　　　 . ★⋆.  ੈ✧˳·˖✶  ˚　.˚　　　　✦　　　.  ੈ✧˳·˖✶ 　　*　　 　　✦  ੈ✧˳·˖✶　　　.　　.　　　✦　˚ 　　　　 ˚　.˚　　　　✦　　　.　　. 　 ˚　.　　　　 　　 　　　　   ੈ✧˳·˖✶ "   ˚　　　　  ੈ✧˳·˖✶✦  ˚　　　　  ੈ✧˳·˖✶✦　　　.　　. 　 ˚　.　　　　　 . ✦　　　 　˚　　　　 . ★⋆.  ੈ✧˳·˖✶  ˚　.˚　　　　✦　　　.  ੈ✧˳·˖✶ 　　*　　 　　✦  ੈ✧˳·˖✶　　　.　　.　　　✦　˚ 　　　　 ˚　.˚　　　　✦　　　.　　. 　 ˚　.　　　　 　　 　　　　   ੈ✧˳·˖✶ "   ˚　　　　  ੈ✧˳·˖✶✦　　　.　　. 　 ˚　.　　　　　 . ✦　　　 　˚　　　　 . ★⋆.  ੈ✧˳·˖✶  ˚　.˚　　　　✦　　　.  ੈ✧˳·˖✶ 　　*　　 　　✦  ੈ✧˳·˖✶　　　.　　.　　　✦　˚ 　　　　 ˚　.˚　　　　✦　　　.　　. 　 ˚　.　　　　.　　. 　 ˚　.　　　　　 . ✦　　　 　˚　　　　 . ★⋆.  ੈ✧˳·˖✶  ˚　.˚　　　　✦　　　.  ੈ✧˳·˖✶ 　　*　　 　　✦  ੈ✧˳·˖✶　　　.　　.　　　✦　˚ 　　　　 ˚　.˚　　　　✦　　　.　　. 　 ˚　.　　　　 　　 　　　　   ੈ✧˳˖ ✶ "</p> <div  style="font-family: Helvetica;  text-align:center; font-size:300%"> <b/>' + str(random_lyrics) + '<b/>' + '</div> <p> "   ˚　　　　  ੈ✧˳·˖✶✦　　　.　　. 　 ˚　.　　　　　 . ✦　　　 　˚　　　　 . ★⋆.  ੈ✧˳·˖✶  ˚　.˚　　　　✦　　　.  ੈ✧˳·˖✶ 　　*　　 　　✦  ੈ✧˳·˖✶　　　.　　.　　　✦　˚ 　　　　 ˚　.˚　　　　✦　　　.　　. 　 ˚　.　　　　 　　 　　　　   ੈ✧˳˖ ✶ "</p>"   ˚　　　　  ੈ✧˳·˖✶✦　　　.　　. 　 ˚　.　　　　　 . ✦　　　 　˚　　　　 . ★⋆.  ੈ✧˳·˖✶  ˚　.˚　　　　✦　　　.  ੈ✧˳·˖✶ 　　*　　 　　✦  ੈ✧˳·˖✶　　　.　　.　　　✦　˚ 　　　　 ˚　.˚　　　　✦　　　.　　. 　 ˚　.　　　　 　　 　　　　   ੈ✧˳˖   ˚　　　　  ੈ✧˳·˖✶✦　　　.　　. 　 ˚　.　　　　　 . ✦　　　 　˚　　　　 . ★⋆.  ੈ✧˳·˖✶  ˚　.˚　　　　✦　　　.  ੈ✧˳·˖✶ 　　*　　 　　✦  ੈ✧˳·˖✶　　　.　　.　　　✦　˚ 　　　　 ˚　.˚　　　　✦　　　.　　. 　 ˚　.　　　　 　　 　　　　   ੈ✧˳˖   ˚　　　　  ੈ✧˳·˖✶✦　　　.　　. 　 ˚　.　　　　　 . ✦　　　 　˚　　　　 . ★⋆.  ੈ✧˳·˖✶  ˚　.˚　　　　✦　　　.  ੈ✧˳·˖✶ 　　*　　 　　✦  ੈ✧˳·˖✶　　　.　　.　　　✦　˚ 　　　　 ˚　.˚　　　　✦　　　.　　. 　 ˚　.　　　　 　　 　　　　   ੈ✧˳˖ ✶ ""   ˚　　　　  ੈ✧˳·˖✶✦　　　.　　. 　 ˚　.　　　　　 . ✦　　　 　˚　　　　 . ★⋆.  ੈ✧˳·˖✶  ˚　.˚　　　　✦　　　.  ੈ✧˳·˖✶ 　　*　　 　　✦  ੈ✧˳·˖✶　　　.　　.　　　✦　˚ 　　　　 ˚　.˚　　　　✦　　　.　　. 　 ˚　.　　　　 　　 　　　　   ੈ✧˳˖ ✶ ""   ˚　　　　  ੈ✧˳·˖✶✦　　　.　　. 　 ˚　.　　　　　 . ✦　　　 　˚　　　　 . ★⋆.  ੈ✧˳·˖✶  ˚　.˚　　　　✦　　　.  ੈ✧˳·˖✶ 　　*　　 　　✦  ੈ✧˳·˖✶　　　.　　.　　　✦　˚ 　　　　 ˚　.˚　　　　✦　　　.　　. 　 ˚　.　　　　 　　 　　　　   ੈ✧˳˖ ✶ "</body>'



    
    print(random_lyrics)
    return {"lyrics": random_lyrics}


def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        raise "exception"
    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if is_expired:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.referesh_access_token(token_info['refresh_token'])
    return token_info



def create_spotify_oauth():
    return SpotifyOAuth(
        client_id='2e373e2ad2c2470ba2234a4e988cdca9',
        client_secret='433aee393e9f4bf78acf98088fba0b48',
        redirect_uri=url_for('redirectPage', _external=True),
        scope="user-top-read",
        username = "lydiaw2882")
