import math
import base64
import os

from collections import defaultdict
from tempfile import NamedTemporaryFile
from flask import Flask, jsonify, redirect, request, render_template, url_for 
from celery import Celery
from worker import tracks
from mutagen.id3 import ID3
from io import BytesIO
from pydub import AudioSegment
from celery.result import AsyncResult 
from demucs.apply import apply_model
from demucs.pretrained import get_model, SOURCES
from demucs.audio import AudioFile, save_audio
from sys import getsizeof
import threading



celery = Celery()

celery.conf.task_acks_late = True


musics = []
MusicsFiles = {}


app = Flask(__name__)
# ------------------API------------------
@app.route('/')
def index():
    return render_template('index.html')


def encode_audio_to_base64(audio):
    if isinstance(audio, str):
        # Caminho do arquivo
        with open(audio, "rb") as audio_file:
            audio_data = audio_file.read()
    else:
        # Objeto BytesIO
        audio_data = audio.read()

    encoded_audio = base64.b64encode(audio_data).decode("utf-8")
    return encoded_audio

id = 0
id_lock = threading.Lock()
def get_metadados(music):
    global id
    with id_lock:
        id += 1
        current_id = id
    
    audio = ID3(music)
    title = audio.get("TIT2")
    artist = audio.get("TPE1")
    

    return {"title": str(title) if title else "Unknown Title", "artist": str(artist) if artist else "Unknown Artist", "id": current_id, "tracks": [{"track_id" : f"{id}1", "name": "drums"}, {"track_id" : f"{id}2", "name": "bass"}, {"track_id" : f"{id}3", "name": "vocals"}, {"track_id" : f"{id}4", "name": "other"}] }
        
   
    
MusicsFiles = {}

@app.route('/music', methods=['POST', 'GET'])
def music(): 
    dados = {}
    if request.method == 'POST':
        try:
            if 'music_file' not in request.files:
                return 'No music file uploaded', 405

            music_file = request.files['music_file']

            dados = get_metadados(music_file)

            musicbytes = music_file.read()

            music = AudioSegment.from_file(BytesIO(musicbytes), format="mp3")
            MusicsFiles[dados.get("id")] = music #alterar para gerar ID aleatorios e tambem ID para musica com title = None

            musics.append(dados) # adiciona à lista de todas as musicas




            return jsonify(dados), 200
        except:
            return "Invalid input",405
    
    elif request.method == 'GET' :
        return jsonify(musics), 200

 
        
        

ids_processed = {}
results = {}
selc = {}
AudioVazio = {}
instruments = {}
job_ids = []
sizes = []
semi_tracks_id = {}
job_tracks = {}
semi_tracks_id_generator = 0
trackOut = ""
result_dict = {}
finalTrack = {}
list_ids = []


@app.route('/music/<int:id>', methods=['GET', 'POST'])
def music_id(id):
    global result
    global AudioVazio
    global other
    global bass
    global vocals
    global drums
    global instruments
    global selc 
    global job_ids
    global execution_time
    global sizes
    global job_tracks
    global semi_tracks_id_generator
    global trackOut
    global result_dict
    global lista
    global finalTrack
    global results
    global taskID

    
   
    if request.method == 'POST':


        music_id = int(request.form.get('id'))

        if music_id not in list_ids:
            list_ids.append(music_id)
        
        selector = []
        finalTrack[music_id] = ""
        results[music_id] = 0
        
        
        try:
            music = MusicsFiles[music_id]
        except:
            return "Music not found", 404
        
        AudioVazio[music_id] = AudioSegment.empty() # limpar o audio vazio sempre que alguem faz um post
        result_dict[music_id] = {'drums': AudioSegment.empty(), 'bass': AudioSegment.empty(), 'vocals': AudioSegment.empty(), 'other': AudioSegment.empty()}
        instruments[music_id] = []
        
        other = request.form.get('other')
        bass = request.form.get('bass')
        vocals = request.form.get('vocals')
        drums = request.form.get('drums')
        
        if(other != None):selector.append(other)
        if(bass != None): selector.append(bass)
        if(vocals != None):selector.append(vocals)
        if(drums != None): selector.append(drums)

        selc[music_id] = selector

        if(len(selc) == 0):
            return "Track not found ", 405

        ids_processed[music_id] = []
        
        numWorkers = 4

        

        part_duration = 120000 #partes de 120000
        taskID = []
        for i in range(0, len(music), part_duration):
            part = music[i:i+part_duration]
            music_base64 = encode_audio_to_base64(BytesIO(part.export(format='mp3').read()))
            size = getsizeof(music_base64)
            task = tracks.delay(music_base64)#envia para o celery cada musicpart em forma base64]
            
            sizes.append({task : size})
            taskID.append(task) # guarda o id de cada worker
        ids_processed[music_id] = taskID
        
        for i in range(len(taskID)):
            job_ids.append(taskID[i].id)
        
        
             
            
        
        

        

        return "successful operation", 200
        
  
    elif request.method == 'GET':

        music_id = int(request.args.get('id'))

        

        try:
            for x in ids_processed[music_id]:
                result = tracks.AsyncResult(x)
                if result.ready():
                
                    for key, value in (result.get().items()):
                        semi_tracks_id_generator += 1
                        if key != "execution_time": ## Ler e juntar apenas os valores que sao tracks
                            if(x == ids_processed[music_id][0]): #### o incremento do audiosegmente + audioemppty so funciona se o audioempty vier depois do +
                                ValueAudioSegment = AudioSegment.from_file(BytesIO(base64.b64decode(value)), format="wav")
                                result_dict[music_id][key] = ValueAudioSegment + result_dict[music_id][key]
                                
                            else: #### nese caso o valor armazenado já nao é empty e entao podemos adicionar o valor do audiosegment a seguir do +, 
                                #porem aqui entra a logica de identificar as tasks do celery e sempre adicionar a menor antes (drums1 vir antes de drums2)
                                ValueAudioSegment = AudioSegment.from_file(BytesIO(base64.b64decode(value)), format="wav")
                                result_dict[music_id][key] = result_dict[music_id][key] + ValueAudioSegment 
                                
                            semi_tracks_id[key] = semi_tracks_id_generator
                        else:
                            execution_time = value
                    if x not in job_tracks.keys():
                        job_tracks[x.id] = semi_tracks_id
                    

                    if x == ids_processed[music_id][-1]:
                        
                        for key, value in result_dict[music_id].items():
                            audio_dir = 'static/tracks'
                            if key in selc[music_id]:
                                # Diretório para armazenar os arquivos de áudio
                                os.makedirs(audio_dir, exist_ok=True)  # Criar o diretório se não existir
                                name = f"{music_id}_{key}.mp3"  # Nome do arquivo de áudio
                                file_path = os.path.join(audio_dir, name)  # Caminho completo do arquivo de áudio
                                # Salvar o AudioSegment como arquivo estático
                                value.export(file_path, format='mp3')
                                track_url = url_for('static', filename=f'tracks/{name}', _external=True)
                                AudioVazio[music_id] = value.overlay(AudioVazio[music_id])

                                instruments[music_id].append({"name": key, "track": track_url})
                            name = f"{music_id}_final.mp3"  # Nome do arquivo de áudio
                            file_path = os.path.join(audio_dir, name)  # Caminho completo do arquivo de áudio
                            # Salvar o AudioSegment como arquivo estático
                            AudioVazio[music_id].export(file_path, format='mp3')
                            finalTrack[music_id] = url_for('static', filename=f'tracks/{name}', _external=True)

                    results[music_id] += 1
                    #results[music_id] = results[music_id] 


                percentagem = results[music_id] / len(ids_processed[music_id]) * 100 ## isto tem que mudar, porque se a lista de trabalhos aumentar ja falha a percentagem



            return jsonify({"instrumentos": instruments[music_id], "progress" : float(percentagem), "final music": finalTrack[music_id]}), 200
            
        except KeyError:
            return "Music not found", 404


# ------------------SERVER------------------
@app.route('/job/<int:music_id>', methods=['GET'])
def job(music_id):
    id = int(request.args.get('music_id'))
    ## job_ids contem os ids de todos os jobs
    try:
        job = job_ids[id]
        tracks_ids = []

        print(execution_time)
        for i in range(len(sizes)):
            for key, value in sizes[i].items():
                if(key == job):
                    size = value
        print(size)

        for x , y in job_tracks.items():
            if(x == job):
                tracks = y

        for i in tracks.keys():
            tracks_ids.append(tracks[i])




        for i in (ids_processed.keys()):
            jobs = ids_processed[i]
            print(jobs)
            if job in jobs:
                id_music = i
        print(id_music)

        return jsonify({"size" : size, "job_id" : id, "track_id" : tracks_ids , "music_id" : id_music, "time" : execution_time}), 200
    
    except KeyError:
        return "Job not found", 404
 

@app.route('/job', methods=['GET'])
def job_list():
    try:
        jobs_output = []
        for i in range(len(job_ids)):
            jobs_output.append(i+1)

        return jsonify(jobs_output), 200
    except KeyError:
        return "invalid input", 405

@app.route('/reset', methods=['POST'])
def reset():
     # Apagar todos os ficheiros
    # Apagar todos os ficheiros

    global sizes
    global job_ids
    global list_ids
    global ids_processed
    global results
    global instruments
    global AudioVazio
    global selc
    global musics
    global id
    global trackOut
    global MusicsFiles
    global semi_tracks_id
    global job_tracks
    global semi_tracks_id_generator
    global result_dict
    global finalTrack


    

    files_dir = os.path.join(app.static_folder, 'tracks')
    for file_name in os.listdir(files_dir):
        file_path = os.path.join(files_dir, file_name)
        os.remove(file_path)

    for tarefasLista in ids_processed.values():
        for tarefa in tarefasLista:
            celery.control.revoke(tarefa.id, terminate=True)

    list_ids = []
    ids_processed = {}
    results = {}
    instruments = []
    AudioVazio == {}
    selc = []
    musics = []
    MusicsFiles = {}
    id = 0
    trackOut = ""
    job_ids = {}
    sizes = []
    semi_tracks_id = {}
    job_tracks = {}
    semi_tracks_id_generator = 0
    result_dict = {}
    finalTrack = {}

    return ('Todos os ficheiros foram apagados e ast tarefas foram canceladas', 200)

    



if __name__ == '__main__':
    app.run()



