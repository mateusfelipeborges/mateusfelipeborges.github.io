# treinar_maddie.py

import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

# Carregar variáveis de ambiente (como chave da API)
load_dotenv()

# Caminho da pasta com os arquivos de Jung, Freud, Lacan etc.
CAMINHO_PASTA = "bases_teoricas"
CAMINHO_CHROMA = "maddie_index"

# Inicializar vetor de embeddings
embeddings = OpenAIEmbeddings()

# Utilitário: carregar todos os documentos da pasta

def carregar_documentos(pasta):
    documentos = []
    for nome_arquivo in os.listdir(pasta):
        caminho = os.path.join(pasta, nome_arquivo)
        if nome_arquivo.endswith(".pdf"):
            loader = PyPDFLoader(caminho)
        elif nome_arquivo.endswith(".txt"):
            loader = TextLoader(caminho)
        else:
            print(f"Ignorado: {nome_arquivo}")
            continue
        documentos.extend(loader.load())
    return documentos

# Utilitário: dividir os textos

def fragmentar_documentos(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    return splitter.split_documents(docs)

# Pipeline principal

def treinar():
    print("🔍 Carregando documentos...")
    docs = carregar_documentos(CAMINHO_PASTA)
    print(f"✔️ {len(docs)} documentos carregados")

    print("✂️ Fragmentando...")
    fragmentos = fragmentar_documentos(docs)
    print(f"✔️ {len(fragmentos)} fragmentos gerados")

    print("🔮 Gerando embeddings...")
    Chroma.from_documents(fragmentos, embeddings, persist_directory=CAMINHO_CHROMA)
    print("✅ Base vetorial criada e armazenada em:", CAMINHO_CHROMA)


if __name__ == "__main__":
    treinar()
