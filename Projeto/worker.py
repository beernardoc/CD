
# coding: utf-8

__author__ = 'Mário Antunes'
__version__ = '1.0'
__email__ = 'mario.antunes@ua.pt'
__status__ = 'Production'
__license__ = 'MIT'

import base64
import json
import logging
import argparse
import subprocess
import tempfile
import requests
from demucs.apply import apply_model
from demucs.pretrained import get_model, SOURCES
from demucs.audio import AudioFile, save_audio
import time

from celery import Celery
from flask import request
import torch

torch.set_num_threads(1)

import torch
torch.set_num_threads(1)


logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

app = Celery('worker', broker='pyamqp://guest@localhost//', backend='rpc://')

app.conf.worker_concurrency = 1




# ...




@app.task
def tracks(fileBytes):
    start_time = time.time()

    #filename = filename.decode("utf-8")
    File = base64.b64decode(fileBytes)
    #print(File)
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(File)                        #ficheiro temporario para que dessa forma o AudioFile funcione corretamente (so aceita path)
        temp_file_path = temp_file.name
    
    # get the model
    model = get_model(name='htdemucs')
    model.cpu()
    model.eval()
    
    # load the audio file
    wav = AudioFile(temp_file_path).read(streams=0, samplerate=model.samplerate, channels=model.audio_channels) 
    ref = wav.mean(0)
    wav = (wav - ref.mean()) / ref.std()


    sources = apply_model(model, wav[None], device='cpu', progress=True, num_workers=app.conf.worker_concurrency)[0]
    sources = sources * ref.std() + ref.mean()

    tracks = {}
    list = []
    end_time = time.time()
    execution_time = end_time - start_time
    
    # store the model
    for source, name in zip(sources, model.sources):

        with tempfile.NamedTemporaryFile(suffix='.wav') as temp_file:
            temp_file_path = temp_file.name
            save_audio(source, str(temp_file_path), samplerate=model.samplerate)
            tracks[name] = base64.b64encode((temp_file.read())).decode('utf-8')
    
    tracks['execution_time'] = execution_time
    return tracks


def main(args):
    # get the model
    model = get_model(name='htdemucs')
    model.cpu()
    model.eval()

    # load the audio file
    wav = AudioFile(args.i).read(streams=0, 
    samplerate=model.samplerate, channels=model.audio_channels) 
    ref = wav.mean(0)
    wav = (wav - ref.mean()) / ref.std()
    
    # apply the model
    # alterar para se o tamanho da musica for maior que 10 minutos dividir em partes e aumentar o numero de workers usados
    #if len(wav) > 600000: # 10 minutos
    #    num_workers = 4
#
    #else:
    #    num_workers = 1
    sources = apply_model(model, wav[None], device='cpu', progress=True, num_workers=1)[0]
    sources = sources * ref.std() + ref.mean()

    # store the model
    for source, name in zip(sources, model.sources):
        stem = f'{args.o}/{name}.wav'
        save_audio(source, str(stem), samplerate=model.samplerate)


