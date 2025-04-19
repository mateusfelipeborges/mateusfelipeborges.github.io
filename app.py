from flask import Flask, render_template, request
from dotenv import load_dotenv
import os
import requests

# Carrega variáveis do .env
load_dotenv()
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

# Flask App
app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/')
def home():
    return render_template('index.html')  # Aqui estamos usando o arquivo index.html em templates

@app.route('/livro')
def livro():
    return render_template('eassimchoveu.html')  # Página adicional

@app.route('/oraculo', methods=['GET', 'POST'])
def oraculo():
    resposta = ""
    if request.method == 'POST':
        pergunta = request.form['pergunta']
        try:
            # Requisição à API da DeepSeek
            url = "https://api.deepseek.com/chat/completions"
            headers = {
                "Authorization": f"Bearer {deepseek_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Você é um oráculo místico e poético. Responda com sabedoria simbólica e linguagem metafórica."},
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

    return render_template('oraculo.html', resposta=resposta)  # Página oráculo

# 🧪 Inicia o servidor localmente
if __name__ == '__main__':
    print("Iniciando servidor Flask...")
    app.run(debug=True)
