from flask import Flask, render_template, request, redirect, url_for, send_file, session
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import requests
import csv
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit

# 🌿 Integrações internas
from maddie_core import gerar_resposta_local, buscar_termo_em_livro

load_dotenv()
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv('SECRET_KEY', 'madra_secreta')

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'madra.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
socketio = SocketIO(app)

class Visitante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    mensagem = db.Column(db.String(200))

class RegistroVisita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(100))
    user_agent = db.Column(db.String(300))
    cidade = db.Column(db.String(100))
    pais = db.Column(db.String(100))
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    rota = db.Column(db.String(100))

class InteracaoMaddie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(100))
    pergunta = db.Column(db.Text)
    resposta = db.Column(db.Text)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)

class Postagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200))
    conteudo = db.Column(db.Text)
    imagem = db.Column(db.String(300))
    data_publicacao = db.Column(db.DateTime, default=datetime.utcnow)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(150), nullable=False)
    idade = db.Column(db.Integer)
    apelido = db.Column(db.String(100))
    pronomes = db.Column(db.String(50))
    nome_artistico = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    admin = db.Column(db.Boolean, default=False)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)

class Comunidade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    descricao = db.Column(db.String(300))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    participantes = db.relationship('Usuario', secondary='participante')

class Topico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200))
    conteudo = db.Column(db.Text)
    comunidade_id = db.Column(db.Integer, db.ForeignKey('comunidade.id'))
    comunidade = db.relationship('Comunidade', backref=db.backref('topicos', lazy=True))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

class Mensagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    usuario = db.relationship('Usuario', backref=db.backref('mensagens', lazy=True))
    topico_id = db.Column(db.Integer, db.ForeignKey('topico.id'))
    topico = db.relationship('Topico', backref=db.backref('mensagens', lazy=True))
    conteudo = db.Column(db.Text)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)

class Participante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    comunidade_id = db.Column(db.Integer, db.ForeignKey('comunidade.id'))

# Função auxiliar

def registrar_visita(request, rota):
    ip = request.remote_addr or '0.0.0.0'
    user_agent = request.headers.get('User-Agent', 'Desconhecido')
    cidade, pais = "Desconhecida", "Desconhecido"
    try:
        dados = requests.get(f"https://ipapi.co/{ip}/json/").json()
        cidade = dados.get("city", cidade)
        pais = dados.get("country_name", pais)
    except Exception as e:
        print("Erro localização:", e)
    db.session.add(RegistroVisita(ip=ip, user_agent=user_agent, cidade=cidade, pais=pais, rota=rota))
    db.session.commit()

@app.route('/')
def home():
    registrar_visita(request, '/')
    return render_template('index.html')

# (Demais rotas mantidas como no seu último código)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
