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

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Chave secreta da aplicação

# Função para postar a mídia
def post_media(username, password, media_type, file_paths, caption, hashtags, disable_comments, disable_likes):
    cl = Client()
    
    try:
        # Login no Instagram
        cl.login(username, password)
    except Exception as e:
        logging.error(f"Erro de login: {e}")
        return flash(f"Erro de login: {e}", "error")

    # Formatação das hashtags
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
            logging.info("Foto postada com sucesso!")
        elif media_type == 'video' and len(file_paths) == 1:
            cl.video_upload(file_paths[0], caption,
                            extra_data={
                                'disable_comments': disable_comments,
                                'disable_likes': disable_likes
                            })
            logging.info("Reel postado com sucesso!")
        elif media_type == 'storie_photo' and len(file_paths) == 1:
            cl.photo_upload_to_story(file_paths[0])
            logging.info("Storie postado com sucesso!")
        elif media_type == 'storie_video' and len(file_paths) == 1:
            cl.video_upload_to_story(file_paths[0])
            logging.info("Storie postado com sucesso!")
        elif media_type == 'carousel':
            cl.album_upload(file_paths, caption)
            logging.info("Carrossel postado com sucesso!")
        else:
            flash("Tipo de mídia inválido ou número incorreto de arquivos.", "error")
    except Exception as e:
        logging.error(f"Erro ao postar: {e}")
        flash(f"Erro ao postar: {e}", "error")

# Função para agendar o post
def schedule_post(username, password, media_type, file_paths, caption, hashtags, disable_comments, disable_likes, post_time):
    schedule.every().day.at(post_time.strftime("%H:%M")).do(
        post_media, username, password, media_type, file_paths, caption, hashtags, disable_comments, disable_likes
    )

# Thread para rodar o scheduler
def scheduler_thread():
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

# Variáveis de ambiente para as contas de Instagram
empreendedor_user = os.getenv('EMPREENDEDOR_USER')
empreendedor_pass = os.getenv('EMPREENDEDOR_PASS')

maarinlucas_user = os.getenv('MAARINLUCAS_USER')
maarinlucas_pass = os.getenv('MAARINLUCAS_PASS')

agenciaroyalx_user = os.getenv('AGENCIAROYALX_USER')
agenciaroyalx_pass = os.getenv('AGENCIAROYALX_PASS')

@app.route('/upload', methods=['POST'])
def upload():
    conta = request.form['conta']
    
    # Verifica qual conta foi selecionada e atribui as credenciais
    if conta == 'empreendedor.do.futuro':
        username = empreendedor_user
        password = empreendedor_pass
        logging.info('Postando em Empreendedor do futuro...')
    elif conta == 'maarinlucas':
        username = maarinlucas_user
        password = maarinlucas_pass
        logging.info('Postando na conta pessoal...')
    elif conta == 'agenciaroyalx':
        username = agenciaroyalx_user
        password = agenciaroyalx_pass
        logging.info('Postando em Royal X...')
    else:
        flash('Escolha uma conta para continuar...', 'error')
        return redirect('/')

    # Obtém dados do formulário
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

    # Verifica se o post é imediato ou agendado
    if immediate_post:
        post_media(username, password, media_type, file_paths, caption, hashtags, disable_comments, disable_likes)
    else:
        try:
            post_datetime = datetime.strptime(post_time, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash("Formato de horário inválido. Use o formato YYYY-MM-DDTHH:MM.", "error")
            return redirect('/')
        schedule_post(username, password, media_type, file_paths, caption, hashtags, disable_comments, disable_likes, post_datetime)

    return redirect('/')

if __name__ == '__main__':
    threading.Thread(target=scheduler_thread, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))  # Heroku atribui a porta automaticamente
    app.run(host='0.0.0.0', port=port, debug=False)  # Mude debug para False em produção
