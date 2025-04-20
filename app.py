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
socketio = SocketIO(app, async_mode='threading')

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
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    autor = db.relationship('Usuario', backref=db.backref('postagens', lazy=True))

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

@app.context_processor
def inject_admin():
    return dict(admin=session.get('is_admin', False), usuario_nome=session.get('usuario_nome'))

@app.route('/criar_admin')
def criar_admin():
    if not Usuario.query.filter_by(email="mateusfelipeborges").first():
        admin = Usuario(
            nome_completo="Mateus Borges",
            idade=24,
            apelido="Mateus",
            pronomes="ele/dele",
            nome_artistico="Madra",
            email="mateusfelipeborges",
            senha=generate_password_hash("My16182605*"),
            admin=True
        )
        db.session.add(admin)
        db.session.commit()
        return "Administrador criado com sucesso!"
    return "Administrador já existe."

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        novo = Usuario(
            nome_completo=request.form['nome_completo'],
            idade=int(request.form['idade']),
            apelido=request.form['apelido'],
            pronomes=request.form['pronomes'],
            nome_artistico=request.form['nome_artistico'],
            email=request.form['email'],
            senha=generate_password_hash(request.form['senha'])
        )
        db.session.add(novo)
        db.session.commit()

        # Enviar notificação por e-mail (simples via SMTP)
        import smtplib
        from email.mime.text import MIMEText

        try:
            remetente = os.getenv('SMTP_USER')
            senha = os.getenv('SMTP_PASS')
            destinatario = os.getenv('ADMIN_EMAIL')

            corpo = f"Novo cadastro:

Nome: {novo.nome_completo}
Email: {novo.email}
Pronomes: {novo.pronomes}"
            mensagem = MIMEText(corpo)
            mensagem['Subject'] = 'Novo Cadastro no Site'
            mensagem['From'] = remetente
            mensagem['To'] = destinatario

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(remetente, senha)
                smtp.send_message(mensagem)
        except Exception as e:
            print("Erro ao enviar e-mail:", e)

        return redirect(url_for('login'))
    return render_template('cadastro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and check_password_hash(usuario.senha, senha):
            session['usuario_id'] = usuario.id
            session['usuario_nome'] = usuario.nome_completo
            session['is_admin'] = usuario.admin
            return redirect(url_for('home'))
        return render_template('login.html', error='Email ou senha inválidos.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/')
def home():
    registrar_visita(request, '/')
    return render_template('index.html')

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

@app.route('/livros')
def livros():
    registrar_visita(request, '/livros')
    return render_template('livros.html')

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
        titulo = request.form['titulo']
        conteudo = request.form['conteudo']
        imagem_arquivo = request.files.get('imagem')
        nome_arquivo = None

        if imagem_arquivo and imagem_arquivo.filename != '':
            nome_arquivo = f"{datetime.utcnow().timestamp()}_{imagem_arquivo.filename}"
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
            imagem_arquivo.save(caminho)

        nova_postagem = Postagem(
            titulo=titulo,
            conteudo=conteudo,
            imagem=f"/static/uploads/{nome_arquivo}" if nome_arquivo else None,
            usuario_id=session['usuario_id']
        )
        db.session.add(nova_postagem)
        db.session.commit()
        return redirect(url_for('blog'))
    return render_template('escrever.html')

@app.route('/comunidades')
def comunidades():
    registrar_visita(request, '/comunidades')
    comunidades = Comunidade.query.all()
    return render_template('comunidades.html', comunidades=comunidades)

@app.route('/comunidade/<int:comunidade_id>')
def comunidade(comunidade_id):
    registrar_visita(request, f'/comunidade/{comunidade_id}')
    comunidade = Comunidade.query.get_or_404(comunidade_id)
    return render_template('comunidade.html', comunidade=comunidade)

@app.route('/comunidade/<int:comunidade_id>/topico/<int:topico_id>', methods=['GET', 'POST'])
def topico(comunidade_id, topico_id):
    registrar_visita(request, f'/comunidade/{comunidade_id}/topico/{topico_id}')
    topico = Topico.query.get_or_404(topico_id)
    if request.method == 'POST':
        mensagem = request.form.get('mensagem')
        if mensagem and 'usuario_id' in session:
            nova_mensagem = Mensagem(usuario_id=session['usuario_id'], topico_id=topico_id, conteudo=mensagem)
            db.session.add(nova_mensagem)
            db.session.commit()
            emit('nova_mensagem', {'mensagem': mensagem}, room=topico_id)
    return render_template('topico.html', topico=topico)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), allow_unsafe_werkzeug=True)
