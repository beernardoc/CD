
# CD 2023 Project

Bernardo Pinto - 105926

João Santos - 110555

A firma Advanced Sound Systems (ASS) encontra-se a desenvolver uma aplicação de karaoke para
músicos. Esta aplicação distingue-se por não só remover a voz das músicas, mas também remover
instrumentos individuais, permitindo a um músico substituir a performance do músico original pela
sua. Este novo serviço será disponibilizado online através de um portal web em que o músico pode
fazer upload de um ficheiro de música, analisar os instrumentos que compõem a música, selecionar
vários instrumentos e finalmente receber um ficheiro novo em que a música contém apenas esses
instrumentos.
A tarefa de separar uma música em várias pistas por instrumento é intensiva do ponto de vista
de processamento pelo que a ASS contratou os alunos de Computação Distribuída para desenvolver
um serviço online capaz de atender às necessidades da empresa com uma qualidade de experiência
elevada para o utilizador final (identificação rápida dos instrumentos e construção do novo ficheiro
sem o(s) instrumento(s) seleccionados).
Para esta tarefa deverão desenvolver todo o código necessário para a criação de um serviço Web
que possa servir em paralelo múltiplos clientes de forma rápida e eficiente recorrendo a computação
paralela (aqui conseguido através de paralelização em múltiplos processos/workers independentes
que podem estar no mesmo computador ou não).
Para esta tarefa é fornecido este guião e um conjunto de pistas de música disponíveis em [4].



Here we have a sample code that loads one mp3 file and splits it 
into 4 tracks: vocals, drums, bass and other.

The codes uses one library named [demucs](https://github.com/facebookresearch/demucs),
this library uses a deep learning model to separate the tracks.
This library requires [ffmpeg](https://ffmpeg.org/) to work.
It should be present in most Linux distributions.

## Dependencies

For Ubuntu (and other debian based linux), run the following commands:

```bash
sudo apt install ffmpeg
```

## Setup

Run the following commands to setup the environement:
```bash
mkdir tracks

python3 -m venv venv
source venv/bin/activate

pip install pip --upgrade
pip install -r requirements_torch.txt
pip install -r requirements_demucs.txt
```

It is important to install the requirements following the previous instructions.
By default, PyTorch will install the CUDA version of the library (over 4G simple from the virtual environment).
As such, the current instructions force the installation of the CPU version of PyTorch and then installs Demucs.

## Usage

The sample main code only requires two parameters:
- **i** the mp3 file used for input
- **o** the folder for the output

Two audio tracks are given (download them from [here](https://filesender.fccn.pt/?s=download&token=cd4fcd29-b3f1-4a4d-9da3-50aae00e702d)):
- **test.mp3** a short sample (0:34) that allows for a quick validation
- **mudic.mp3** a long (59:04) sequence of royalty free rock musics that are the target of the work

Both audio files are royalty free.

To run test the sample code simple run:
```bash
python main.py -i test.mp3
```

## Authors

* **Mário Antunes** - [mariolpantunes](https://github.com/mariolpantunes)
* **Diogo Gomes** - [dgomes](https://github.com/dgomes)
* **Nuno Lau** - [nunolau](https://github.com/nunolau)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
