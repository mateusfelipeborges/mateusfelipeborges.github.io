from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DateTime
from datetime import datetime

# Caminho do banco de dados
engine = create_engine("sqlite:///madra.db", echo=True)
metadata = MetaData()

# Tabela Visitante
visitante = Table(
    'visitante', metadata,
    Column('id', Integer, primary_key=True),
    Column('nome', String(100)),
    Column('mensagem', String(200))
)

# Tabela RegistroVisita
registro_visita = Table(
    'registro_visita', metadata,
    Column('id', Integer, primary_key=True),
    Column('ip', String(100)),
    Column('user_agent', String(300)),
    Column('cidade', String(100)),
    Column('pais', String(100)),
    Column('data_hora', DateTime, default=datetime.utcnow),
    Column('rota', String(100))
)

# Tabela InteracaoMaddie
interacao_maddie = Table(
    'interacao_maddie', metadata,
    Column('id', Integer, primary_key=True),
    Column('ip', String(100)),
    Column('pergunta', Text),
    Column('resposta', Text),
    Column('estilo', String(50)),
    Column('data_hora', DateTime, default=datetime.utcnow)
)

# Criar todas as tabelas
metadata.create_all(engine)
print("Banco de dados criado com sucesso!")
