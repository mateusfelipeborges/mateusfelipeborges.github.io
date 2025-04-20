from flask import Flask, render_template, request, redirect, url_for, send_file
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import requests
import csv

# Importações da IA Maddie
from maddie_core import gerar_resposta_local, buscar_termo_em_livro

# ===============================
# ⚙️ CONFIGURAÇÕES INICIAIS
# ===============================

load_dotenv()
app = Flask(__name__, static_folder='static', template_folder='templates')

# Banco de dados SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'madra.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ===============================
# 📦 MODELOS DO BANCO DE DADOS
# ===============================

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
    data_publicacao = db.Column(db.DateTime, default=datetime.utcnow)

# ===============================
# 🛠 FUNÇÕES AUXILIARES
# ===============================

def registrar_visita(request, rota):
    ip = request.remote_addr or '0.0.0.0'
    user_agent = request.headers.get('User-Agent', 'Desconhecido')
    cidade, pais = "Desconhecida", "Desconhecido"
    try:
        response = requests.get(f"https://ipapi.co/{ip}/json/")
        if response.status_code == 200:
            dados = response.json()
            cidade = dados.get("city", cidade)
            pais = dados.get("country_name", pais)
    except Exception as e:
        print("Erro ao buscar localização:", e)

    nova_visita = RegistroVisita(ip=ip, user_agent=user_agent, cidade=cidade, pais=pais, rota=rota)
    db.session.add(nova_visita)
    db.session.commit()

# ===============================
# 🌐 ROTAS DO FLASK
# ===============================

@app.route('/criar_banco')
def criar_banco():
    db.create_all()
    return "Banco de dados criado com sucesso!"

@app.route('/')
def home():
    registrar_visita(request, '/')
    return render_template('index.html')

@app.route('/livros')
def listar_livros():
    registrar_visita(request, '/livros')
    livros = [arquivo.replace(".db", "") for arquivo in os.listdir("bases_teoricas") if arquivo.endswith(".db")]
    return render_template("livros.html", livros=livros)

@app.route('/livro')
def consultar_livro():
    registrar_visita(request, '/livro')
    nome = request.args.get("nome")
    termo = request.args.get("termo")
    if not nome or not termo:
        return "Uso correto: /livro?nome=kozen&termo=autômato"
    resultado = buscar_termo_em_livro(nome, termo)
    return f"<pre>{resultado}</pre>"

@app.route('/maddie', methods=['GET', 'POST'])
def maddie():
    registrar_visita(request, '/maddie')
    resposta = ""
    historico = InteracaoMaddie.query.filter_by(ip=request.remote_addr).order_by(
        InteracaoMaddie.data_hora.desc()).limit(10).all()

    if request.method == 'POST':
        if 'apagar_historico' in request.form:
            InteracaoMaddie.query.filter_by(ip=request.remote_addr).delete()
            db.session.commit()
            return redirect(url_for('maddie'))

        pergunta = request.form.get('pergunta', '').strip()

        if pergunta:
            resposta = gerar_resposta_local(pergunta)
            nova_interacao = InteracaoMaddie(ip=request.remote_addr, pergunta=pergunta, resposta=resposta)
            db.session.add(nova_interacao)
            db.session.commit()
            historico = InteracaoMaddie.query.filter_by(ip=request.remote_addr).order_by(
                InteracaoMaddie.data_hora.desc()).limit(10).all()

    return render_template('maddie.html', resposta=resposta, historico=historico)

@app.route('/blog')
def blog():
    registrar_visita(request, '/blog')
    posts = Postagem.query.order_by(Postagem.data_publicacao.desc()).all()
    return render_template('blog.html', posts=posts)

@app.route('/escrever', methods=['GET', 'POST'])
def escrever():
    registrar_visita(request, '/escrever')
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        conteudo = request.form.get('conteudo', '').strip()
        if titulo and conteudo:
            nova_postagem = Postagem(titulo=titulo, conteudo=conteudo)
            db.session.add(nova_postagem)
            db.session.commit()
            return redirect(url_for('blog'))
    return render_template('escrever.html')

@app.route('/acessos')
def acessos():
    visitas = RegistroVisita.query.order_by(RegistroVisita.data_hora.desc()).all()
    return render_template('acessos.html', visitas=visitas)

@app.route('/relatorio_csv')
def relatorio_csv():
    visitas = RegistroVisita.query.order_by(RegistroVisita.data_hora.desc()).all()
    caminho_arquivo = os.path.join(basedir, 'relatorio_acessos.csv')
    with open(caminho_arquivo, mode='w', newline='', encoding='utf-8') as arquivo_csv:
        writer = csv.writer(arquivo_csv)
        writer.writerow(['Data/Hora', 'IP', 'Cidade', 'País', 'Rota', 'User-Agent'])
        for v in visitas:
            writer.writerow([
                v.data_hora.strftime('%d/%m/%Y %H:%M:%S'),
                v.ip, v.cidade, v.pais, v.rota, v.user_agent
            ])
    return send_file(caminho_arquivo, as_attachment=True)

# ===============================
# 🚀 INÍCIO DO SERVIDOR
# ===============================

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"Iniciando servidor Flask na porta {port}...")
    app.run(debug=False, host='0.0.0.0', port=port)