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

# ===============================
# ⚙️ CONFIGURAÇÕES INICIAIS
# ===============================

load_dotenv()
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv('SECRET_KEY', 'madra_secreta')

# Configuração do Flask-Mail
from flask_mail import Mail, Message
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv('mateusfelipeborges845@gmail.com'),
    MAIL_PASSWORD=os.getenv('ssvqppatnrckeine')
)
mail = Mail(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'madra.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# Configuração do SocketIO
socketio = SocketIO(app)

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

# Modelos para o Fórum
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
    usuario = db.relationship('Usuario', backref=db.backref('comunidades_participante', lazy=True))
    comunidade_id = db.Column(db.Integer, db.ForeignKey('comunidade.id'))
    comunidade = db.relationship('Comunidade', backref=db.backref('membros', lazy=True))

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

@app.route('/comunidades')
def comunidades():
    registrar_visita(request, '/comunidades')
    comunidades = Comunidade.query.all()
    return render_template('comunidades.html', comunidades=comunidades)

@app.route('/comunidade/<int:comunidade_id>')
def comunidade(comunidade_id):
    registrar_visita(request, '/comunidade')
    comunidade = Comunidade.query.get_or_404(comunidade_id)
    return render_template('comunidade.html', comunidade=comunidade)

@app.route('/comunidade/<int:comunidade_id>/topico/<int:topico_id>', methods=['GET', 'POST'])
def topico(comunidade_id, topico_id):
    registrar_visita(request, '/comunidade/<int:comunidade_id>/topico')
    topico = Topico.query.get_or_404(topico_id)
    if request.method == 'POST':
        mensagem = request.form.get('mensagem')
        if mensagem:
            nova_mensagem = Mensagem(
                usuario_id=session['usuario_id'],
                topico_id=topico_id,
                conteudo=mensagem
            )
            db.session.add(nova_mensagem)
            db.session.commit()
            emit('nova_mensagem', {'mensagem': mensagem}, room=topico_id)
    return render_template('topico.html', topico=topico)

# ===============================
# 💬 ROTA DE CHAT ONLINE
# ===============================

@app.route('/chat/<int:topico_id>', methods=['GET', 'POST'])
def chat_online(topico_id):
    registrar_visita(request, '/chat')
    topico = Topico.query.get_or_404(topico_id)
    return render_template('chat.html', topico=topico)

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
            nova_interacao = InteracaoMaddie(
                ip=request.remote_addr,
                pergunta=pergunta,
                resposta=resposta
            )
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

    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        conteudo = request.form.get('conteudo', '').strip()
        imagem_arquivo = request.files.get('imagem')

        nome_imagem = None
        if imagem_arquivo and imagem_arquivo.filename:
            nome_imagem = imagem_arquivo.filename
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem)
            imagem_arquivo.save(caminho)

        if titulo and conteudo:
            nova_postagem = Postagem(
                titulo=titulo,
                conteudo=conteudo,
                imagem=nome_imagem
            )
            db.session.add(nova_postagem)
            db.session.commit()
            return redirect(url_for('blog'))

    return render_template('escrever.html')


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome_completo = request.form.get('nome_completo', '').strip()
        idade = request.form.get('idade', '').strip()
        apelido = request.form.get('apelido', '').strip()
        pronomes = request.form.get('pronomes', '').strip()
        nome_artistico = request.form.get('nome_artistico', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()

        if Usuario.query.filter_by(email=email).first():
            return "⚠️ Email já registrado. Faça login ou use outro email."

        nova_conta = Usuario(
            nome_completo=nome_completo,
            idade=int(idade) if idade.isdigit() else None,
            apelido=apelido,
            pronomes=pronomes,
            nome_artistico=nome_artistico,
            email=email,
            senha=generate_password_hash(senha)
        )
        db.session.add(nova_conta)
        db.session.commit()

        # Enviar notificação por e-mail
       msg = Message(
    subject='📝 Novo Cadastro no Madra Mada',
    sender=os.getenv('MAIL_DEFAULT_SENDER'),  # 👈 ESSA LINHA AQUI
    recipients=[os.getenv('MAIL_USERNAME')],
    body=f'''
📬 Novo usuário se cadastrou!

Nome: {nome_completo}
Email: {email}
Idade: {idade}
Apelido: {apelido}
Pronomes: {pronomes}
Nome artístico: {nome_artistico}
'''
)

        mail.send(msg)

        return redirect(url_for('login'))

    return render_template('cadastro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()

        try:
            usuario = Usuario.query.filter_by(email=email).first()
            if usuario and check_password_hash(usuario.senha, senha):
                session['usuario_id'] = usuario.id
                session['usuario_nome'] = usuario.nome_completo
                session['is_admin'] = usuario.admin  # Adiciona a informação de admin na sessão
                return redirect(url_for('home'))
            return render_template('login.html', error="❌ Email ou senha inválidos.")
        except Exception as e:
            print(f"Erro ao processar o login: {e}")
            return render_template('login.html', error="⚠️ Ocorreu um erro durante o login. Tente novamente mais tarde.")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

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
# ===============================@app.route('/cadastro', methods=['GET', 'POST'])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"Iniciando servidor Flask com SocketIO na porta {port}...")
    socketio.run(app, debug=True, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
