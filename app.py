from flask import Flask, render_template, request, redirect, flash
from instagrapi import Client
import os
import schedule
import time
import threading
from datetime import datetime
from dotenv import load_dotenv
import logging 

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Chave secreta da aplicação

def post_media(username, password, media_type, file_paths, caption, hashtags, disable_comments, disable_likes):
    cl = Client()
      
    
        
    cl.login(username, password)

    # Formata as hashtags
    if hashtags:
        caption += '\n'.join(['.'] * 15) + '\n' + ' '.join([f'#{tag.strip()}' for tag in hashtags.split(',')])

    try:
        if media_type == 'photo' and len(file_paths) == 1:
            cl.photo_upload(
                file_paths[0],
                caption,
                extra_data={
                    'disable_comments': disable_comments,
                    'disable_likes': disable_likes
                }
            )
            print("Foto postada com sucesso!")
        elif media_type == 'video' and len(file_paths) == 1:
            cl.video_upload(file_paths[0], caption,
                extra_data={
                    'disable_comments': disable_comments,
                    'disable_likes': disable_likes
                })
            print("Reel postado com sucesso!")
        elif media_type == 'storie_photo' and len(file_paths) == 1:
            cl.photo_upload_to_story(file_paths[0])
            
            print("Storie postado com sucesso!") 
        elif media_type == 'storie_video' and len(file_paths) == 1:
            cl.video_upload_to_story(file_paths[0])
               
            print("Storie postado com sucesso!")                
        elif media_type == 'carousel':
            cl.album_upload(file_paths, caption)
            print("Carrossel postado com sucesso!")
        else:
            flash("Tipo de mídia inválido ou número incorreto de arquivos.", "error")
    except Exception as e:
        print(f"Erro ao postar: {e}")
        logging.info("Foto postada com sucesso!")

def schedule_post(username, password, media_type, file_paths, caption, hashtags, disable_comments, disable_likes, post_time):
    schedule.every().day.at(post_time.strftime("%H:%M")).do(
        post_media, username, password, media_type, file_paths, caption, hashtags, disable_comments, disable_likes
    )

def scheduler_thread():
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')



empreendedor_user = os.getenv('EMPREENDEDOR_USER')
empreendedor_pass = os.getenv('EMPREENDEDOR_PASS')

maarinlucas_user = os.getenv('MAARINLUCAS_USER')
maarinlucas_pass = os.getenv('MAARINLUCAS_PASS')

agenciaroyalx_user = os.getenv('AGENCIAROYALX_USER')
agenciaroyalx_pass = os.getenv('AGENCIAROYALX_PASS')

@app.route('/upload', methods=['POST'])
def upload():
    conta = request.form['conta']
    
    
    if conta == 'empreendedor':
        username = empreendedor_user
        password = empreendedor_pass
        print('Postando em Empreendedor do futuro...')
    elif conta == 'maarinlucas':
        username = maarinlucas_user
        password = maarinlucas_pass
        print('Postando na conta pessoal...')
    elif conta == 'agenciaroyalx':
        username = agenciaroyalx_user
        password = agenciaroyalx_pass
        print('Postando em Royal X...')
    else:
        username = ''
        password = ''
        print('Escolha uma conta para comtinuar...')
           
        
    
    media_type = request.form['media_type']
    caption = request.form['caption']
    hashtags = request.form['hashtags']
    disable_comments = 'disable_comments' in request.form
    disable_likes = 'disable_likes' in request.form
    immediate_post = 'immediate_post' in request.form
    post_time = request.form['post_time']

    # Salva os arquivos enviados
    files = request.files.getlist('files')
    file_paths = []

    # Cria a pasta de uploads, se não existir
    os.makedirs('uploads', exist_ok=True)

    for file in files:
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)
        file_paths.append(file_path)

    if immediate_post:
        post_media(username, password, media_type, file_paths, caption, hashtags, disable_comments, disable_likes)
    else:
        post_datetime = datetime.strptime(post_time, '%Y-%m-%dT%H:%M')
        schedule_post(username, password, media_type, file_paths, caption, hashtags, disable_comments, disable_likes, post_datetime)

    return redirect('/')

if __name__ == '__main__':
    threading.Thread(target=scheduler_thread, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))  # Heroku atribui a porta automaticamente
    app.run(host='0.0.0.0', port=port, debug=False)  # Mude debug para False em produção