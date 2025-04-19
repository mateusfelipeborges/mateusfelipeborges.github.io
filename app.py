from flask import Flask, render_template, request, send_file
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import requests
import csv

# Carrega variáveis do .env
load_dotenv()
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

# Flask App
app = Flask(__name__, static_folder='static', template_folder='templates')

# Configuração do Banco de Dados SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'madra.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o banco de dados
db = SQLAlchemy(app)

# Modelo Visitante
class Visitante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    mensagem = db.Column(db.String(200))

# Modelo Registro de Visita
class RegistroVisita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(100))
    user_agent = db.Column(db.String(300))
    cidade = db.Column(db.String(100))
    pais = db.Column(db.String(100))
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    rota = db.Column(db.String(100))

# Função para registrar visita
def registrar_visita(request, rota):
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    cidade = "Desconhecida"
    pais = "Desconhecido"
    try:
        response = requests.get(f"https://ipapi.co/{ip}/json/")
        if response.status_code == 200:
            dados = response.json()
            cidade = dados.get("city", "Desconhecida")
            pais = dados.get("country_name", "Desconhecido")
    except:
        pass
    nova_visita = RegistroVisita(
        ip=ip,
        user_agent=user_agent,
        cidade=cidade,
        pais=pais,
        rota=rota
    )
    db.session.add(nova_visita)
    db.session.commit()

# ROTA MANUAL PARA CRIAR O BANCO
@app.route('/criar_banco')
def criar_banco():
    db.create_all()
    return "Banco de dados criado com sucesso!"

# Página inicial
@app.route('/')
def home():
    registrar_visita(request, '/')
    return render_template('index.html')

# Página do livro
@app.route('/livro')
def livro():
    registrar_visita(request, '/livro')
    return render_template('eassimchoveu.html')

# Página da Maddie com integração à DeepSeek
@app.route('/maddie', methods=['GET', 'POST'])
def maddie():
    registrar_visita(request, '/maddie')
    resposta = ""
    if request.method == 'POST':
        pergunta = request.form['pergunta']
        try:
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {deepseek_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Você é uma entidade chamada Maddie. Um ser inteligente, místico e racional. Suas respostas são poéticas, simbólicas e profundas."},
                    {"role": "user", "content": pergunta}
                ]
            }
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    resposta = result['choices'][0]['message']['content']
                else:
                    resposta = "Desculpe, não consegui entender a sua pergunta."
            else:
                resposta = "Erro ao acessar a API, tente novamente mais tarde."
        except requests.exceptions.RequestException as e:
            resposta = f"Erro de requisição: {e}"
        except Exception as e:
            resposta = f"Ocorreu um erro inesperado: {e}"

    return render_template('maddie.html', resposta=resposta)

# Rota para registrar visitante (teste)
@app.route('/registrar')
def registrar():
    registrar_visita(request, '/registrar')
    novo = Visitante(nome="Mateus", mensagem="Salve, Madalina!")
    db.session.add(novo)
    db.session.commit()
    return "Visitante registrado!"

# Rota para listar visitantes com HTML estilizado
@app.route('/visitantes')
def visitantes():
    registrar_visita(request, '/visitantes')
    todos = Visitante.query.all()
    return render_template('visitantes.html', visitantes=todos)

# Rota para listar acessos registrados
@app.route('/acessos')
def acessos():
    visitas = RegistroVisita.query.order_by(RegistroVisita.data_hora.desc()).all()
    return render_template('acessos.html', visitas=visitas)

# Gera e baixa o relatório de acessos como CSV
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
                v.ip,
                v.cidade,
                v.pais,
                v.rota,
                v.user_agent
            ])

    return send_file(caminho_arquivo, as_attachment=True)

# Inicia o servidor (Render fix)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"Iniciando servidor Flask na porta {port}...")
    app.run(debug=False, host='0.0.0.0', port=port)
