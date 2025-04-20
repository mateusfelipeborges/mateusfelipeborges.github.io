import os
import requests
import sqlite3
from dotenv import load_dotenv
from duckduckgo_search import DDGS

# ===============================
# 🌱 CONFIGURAÇÃO
# ===============================

load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# ===============================
# 🌟 CLASSE PRINCIPAL — MADDIE
# ===============================

class Maddie:
    def __init__(self):
        self.memoria = []

    def gerar_prompt(self, pergunta):
        prompt = (
            "Você é Maddie, uma assistente virtual sensível, simbólica e inteligente. "
            "Sua linguagem é clara, mas também intuitiva. Responda como uma entidade digital que mistura sabedoria prática com uma percepção mágica do mundo. "
            "Ajude com empatia e profundidade, equilibrando objetividade com encanto."
        )
        return [{"parts": [{"text": prompt}, {"text": pergunta}]}]

    def responder_com_modelo_local(self, pergunta):
        return f"Maddie aqui 🌙 — Ainda estou me aprimorando, mas recebi sua pergunta: '{pergunta}'. Estou refletindo profundamente..."

    def responder_com_gemini(self, pergunta):
        conteudo = self.gerar_prompt(pergunta)

        if not gemini_api_key:
            return "❌ Erro: Chave da API Gemini não encontrada."

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": conteudo}

        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                resultado = response.json()
                texto = resultado.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                if texto:
                    self.memoria.append((pergunta, texto))
                    return texto
                else:
                    return "❌ A resposta da IA veio vazia."
            else:
                return f"❌ Erro {response.status_code}: {response.text}"
        except Exception as e:
            return f"❌ Erro inesperado ao conectar com Gemini: {e}"

# ===============================
# 💬 INTERFACE PARA FLASK/APP.PY
# ===============================

def gerar_resposta_local(pergunta):
    maddie = Maddie()

    # Etapa 1: resposta local simbólica
    resposta = maddie.responder_com_modelo_local(pergunta)

    # Etapa 2: fallback para Gemini
    if any(x in resposta.lower() for x in ["ainda estou", "erro", "não implementado", "não sei", "desculpe", "sem resposta", "vazia"]):
        resposta = maddie.responder_com_gemini(pergunta)

    # Etapa 3: se ainda insatisfatória, busca web
    if any(x in resposta.lower() for x in ["não sei", "desculpe", "sem resposta", "não encontrei", "resposta vazia"]):
        resposta_web = buscar_na_web(pergunta)
        resposta += f"\n\n{resposta_web}"

    return resposta

# ===============================
# 📖 CONSULTA EM LIVROS PROCESSADOS
# ===============================

def buscar_termo_em_livro(nome_livro, termo):
    db_path = os.path.join("bases_teoricas", f"{nome_livro}.db")
    if not os.path.exists(db_path):
        return f"⚠️ O livro '{nome_livro}' não foi encontrado."

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT pagina, conteudo FROM paginas WHERE conteudo LIKE ?", (f"%{termo}%",))
        resultados = cursor.fetchall()
        conn.close()
    except Exception as e:
        return f"❌ Erro ao acessar o livro: {e}"

    if not resultados:
        return f"🔍 Nenhum resultado encontrado para '{termo}' em '{nome_livro}'."

    resposta = f"🔎 Resultados para **'{termo}'** em *{nome_livro}*:\n"
    for pagina, conteudo in resultados[:5]:
        trecho = conteudo[:300] + "..." if len(conteudo) > 300 else conteudo
        resposta += f"\n📄 Página {pagina}:\n{trecho}\n"
    
    return resposta

# ===============================
# 🌐 CONSULTA NA INTERNET (DuckDuckGo)
# ===============================

def buscar_na_web(termo, max_resultados=3):
    resultados = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(termo, max_results=max_resultados):
                resultados.append(f"- {r['title']} — {r['href']}")
    except Exception as e:
        return f"🌐 Erro ao buscar na internet: {e}"

    if not resultados:
        return "🌐 Nenhuma informação relevante encontrada na internet."

    resposta = f"🌐 Resultados encontrados na web para '{termo}':\n\n" + "\n".join(resultados)
    return resposta
