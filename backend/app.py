from flask import Flask, render_template, request, redirect
from instagrapi import Client
import os
import schedule
import time
import threading
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')

def post_media(username, password, file_paths, caption, hashtags, disable_comments, disable_likes):
    cl = Client()
    try:
        cl.login(username, password)
        if hashtags:
            caption += ' ' + ' '.join(['#' + tag.strip() for tag in hashtags.split(',')])
        if len(file_paths) == 1:
            cl.photo_upload(file_paths[0], caption, extra_data={'disable_comments': disable_comments, 'disable_likes': disable_likes})
        else:
            cl.album_upload(file_paths, caption, extra_data={'disable_comments': disable_comments, 'disable_likes': disable_likes})
    except Exception as e:
        print(f"Erro ao postar: {e}")

def schedule_post(username, password, file_paths, caption, hashtags, disable_comments, disable_likes, post_time):
    schedule.every().day.at(post_time.strftime("%H:%M")).do(post_media, username, password, file_paths, caption, hashtags, disable_comments, disable_likes)

def scheduler_thread():
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    username = request.form['username']
    password = request.form['password']
    caption = request.form['caption']
    hashtags = request.form['hashtags']
    disable_comments = 'disable_comments' in request.form
    disable_likes = 'disable_likes' in request.form
    immediate_post = 'immediate_post' in request.form
    post_time = request.form['post_time']

    files = request.files.getlist('files')
    file_paths = []
    os.makedirs('uploads', exist_ok=True)

    for file in files:
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)
        file_paths.append(file_path)

    if immediate_post:
        post_media(username, password, file_paths, caption, hashtags, disable_comments, disable_likes)
    else:
        post_datetime = datetime.strptime(post_time, '%Y-%m-%dT%H:%M')
        schedule_post(username, password, file_paths, caption, hashtags, disable_comments, disable_likes, post_datetime)

    return redirect('/')

if __name__ == '__main__':
    threading.Thread(target=scheduler_thread, daemon=True).start()
    app.run(debug=os.getenv('FLASK_DEBUG', 'false') == 'true')
