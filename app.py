from flask import Flask, render_template, request, redirect, url_for, send_file
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import requests
import csv

# Importações da Maddie
from maddie_core import gerar_resposta_local, buscar_termo_em_livro

# Carrega variáveis do .env
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Define se a lógica será local ou via API
MODO_LOCAL = True

# Flask App
app = Flask(__name__, static_folder='static', template_folder='templates')

# Banco de Dados
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'madra.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ===============================
# 📦 MODELOS
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
    estilo = db.Column(db.String(50))
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)

# ===============================
# 📍 FUNÇÕES AUXILIARES
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

def gerar_resposta_gemini(pergunta, estilo):
    prompt_inicial = {
        "poetica": "Você é Maddie, uma entidade mística, inteligente e profunda. Responda de forma simbólica e poética.",
        "direta": "Você é Maddie, uma assistente objetiva e clara. Responda de forma direta, mas com empatia."
    }
    prompt = prompt_inicial.get(estilo, prompt_inicial["poetica"])
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}, {"text": pergunta}]}]}
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        resultado = response.json()
        return resultado['candidates'][0]['content']['parts'][0]['text']
    except requests.exceptions.RequestException as e:
        return f"Erro de conexão com a API Gemini: {e}"
    except Exception as e:
        return f"Erro inesperado: {e}"

# ===============================
# 🌐 ROTAS
# ===============================

@app.route('/criar_banco')
def criar_banco():
    db.create_all()
    return "Banco de dados criado com sucesso!"

@app.route('/')
def home():
    registrar_visita(request, '/')
    return render_template('index.html')

@app.route('/livro')
def consultar_livro():
    registrar_visita(request, '/livro')
    nome = request.args.get("nome")
    termo = request.args.get("termo")
    if not nome or not termo:
        return "Uso correto: /livro?nome=kozen&termo=autômato"

    resultado = buscar_termo_em_livro(nome, termo)
    return f"<pre>{resultado}</pre>"

@app.route('/livros')
def listar_livros():
    registrar_visita(request, '/livros')
    livros = []
    for arquivo in os.listdir("bases_teoricas"):
        if arquivo.endswith(".db"):
            nome = arquivo.replace(".db", "")
            livros.append(nome)
    return render_template("livros.html", livros=livros)

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
        estilo = request.form.get('estilo', 'poetica')

        if pergunta:
            if MODO_LOCAL:
                resposta = gerar_resposta_local(pergunta, estilo)
                if not resposta or "não implementado" in resposta.lower():
                    resposta = gerar_resposta_gemini(pergunta, estilo)
            else:
                resposta = gerar_resposta_gemini(pergunta, estilo)

            nova_interacao = InteracaoMaddie(
                ip=request.remote_addr,
                pergunta=pergunta,
                resposta=resposta,
                estilo=estilo
            )
            db.session.add(nova_interacao)
            db.session.commit()

            historico = InteracaoMaddie.query.filter_by(ip=request.remote_addr).order_by(
                InteracaoMaddie.data_hora.desc()).limit(10).all()

    return render_template('maddie.html', resposta=resposta, historico=historico)

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
