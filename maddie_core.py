import os
import requests
import sqlite3
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# ===============================
# 🌟 CLASSE MADDIE
# ===============================

class Maddie:
    def __init__(self, estilo="poetica"):
        self.estilo = estilo
        self.memoria = []  # Memória futura para contextualização

    def definir_estilo(self, novo_estilo):
        if novo_estilo in ["poetica", "direta"]:
            self.estilo = novo_estilo

    def gerar_prompt(self, pergunta):
        estilo_prompt = {
            "poetica": "Você é Maddie, uma entidade mística, intuitiva e simbólica. Responda de forma poética, misteriosa e sábia.",
            "direta": "Você é Maddie, uma assistente clara e objetiva. Responda com empatia e clareza."
        }
        prompt = estilo_prompt.get(self.estilo, estilo_prompt["poetica"])
        return [{"parts": [{"text": prompt}, {"text": pergunta}]}]

    def responder_com_gemini(self, pergunta):
        conteudo = self.gerar_prompt(pergunta)

        if not gemini_api_key:
            return "Erro: Chave da API Gemini não encontrada."

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": conteudo}

        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                resultado = response.json()
                resposta = resultado['candidates'][0]['content']['parts'][0]['text']
                self.memoria.append((pergunta, resposta))  # Salva na memória
                return resposta
            else:
                return f"Erro {response.status_code}: {response.text}"
        except Exception as e:
            return f"Erro inesperado: {e}"

    def responder_com_modelo_local(self, pergunta):
        # Lógica temporária para resposta local
        if self.estilo == "direta":
            return f"[Maddie direta] Ainda estou aprendendo, mas entendi sua pergunta: '{pergunta}'."
        else:
            return f"[Maddie poética] Sob os véus do invisível, tua dúvida ecoa: '{pergunta}'... e mesmo sem saber, ressoo contigo."


# ===============================
# 💬 INTERFACE PARA O APP
# ===============================

def gerar_resposta_local(pergunta, estilo):
    maddie = Maddie(estilo=estilo)
    resposta = maddie.responder_com_modelo_local(pergunta)

    # Em caso de limitação da IA local, usar fallback Gemini
    if "ainda não" in resposta.lower() or "erro" in resposta.lower():
        resposta = maddie.responder_com_gemini(pergunta)

    return resposta


# ===============================
# 📖 BUSCA EM LIVROS PROCESSADOS
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
        return f"Erro ao acessar o livro: {e}"

    if not resultados:
        return f"🔍 Nenhum resultado encontrado para '{termo}' em '{nome_livro}'."

    resposta = f"🔎 Resultados para **'{termo}'** em *{nome_livro}*:\n"
    for pagina, conteudo in resultados[:5]:  # limita a 5 trechos
        trecho = conteudo[:300] + "..." if len(conteudo) > 300 else conteudo
        resposta += f"\n📄 Página {pagina}:\n{trecho}\n"
    
    return resposta
