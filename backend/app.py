from flask import Flask, render_template, request, redirect
from instagrapi import Client
from instagrapi.types import Usertag, Location
import os
import schedule
import time
import threading
from datetime import datetime

app = Flask(__name__)
app.secret_key = 's3gR3tK3y123!'  # Substitua pela sua chave secreta

def post_media(username, password, file_paths, caption, hashtags, disable_comments, disable_likes):
    cl = Client()
    cl.login(username, password)

    # Formata as hashtags
    if hashtags:
        caption += ' ' + ' '.join(['#' + tag.strip() for tag in hashtags.split(',')])

    # Publica a foto ou o carrossel
    if len(file_paths) == 1:
        cl.photo_upload(
            file_paths[0],
            caption,
            extra_data={
                'disable_comments': disable_comments,
                'disable_likes': disable_likes
            }
        )
    else:
        try:
            # Remova usertags e location se não forem necessários
            

            cl.album_upload(
                file_paths,
                caption,
                extra_data={
                    'disable_comments': disable_comments,
                    'disable_likes': disable_likes
                }
            )
            print("Carrossel postado com sucesso!")
        except Exception as e:
            print(f"Erro ao postar carrossel: {e}")

def schedule_post(username, password, file_paths, caption, hashtags, disable_comments, disable_likes, post_time):
    # Programação da postagem
    schedule.every().day.at(post_time.strftime("%H:%M")).do(
        post_media, username, password, file_paths, caption, hashtags, disable_comments, disable_likes)

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

    # Salva os arquivos enviados
    files = request.files.getlist('files')
    file_paths = []

    # Cria uma pasta de uploads, se não existir
    os.makedirs('uploads', exist_ok=True)

    for file in files:
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)
        file_paths.append(file_path)

    if immediate_post:
        # Se "Postar Imediatamente" estiver selecionado, publica agora
        post_media(username, password, file_paths, caption, hashtags, disable_comments, disable_likes)
    else:
        # Se agendar, faz a programação
        post_datetime = datetime.strptime(post_time, '%Y-%m-%dT%H:%M')
        schedule_post(username, password, file_paths, caption, hashtags, disable_comments, disable_likes, post_datetime)

    return redirect('/')

if __name__ == '__main__':
    # Inicia a thread do scheduler
    threading.Thread(target=scheduler_thread, daemon=True).start()
    app.run(debug=True)
