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
    return render_template('index.html')

@app.route('/livro')
def livro():
    return render_template('eassimchoveu.html')

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
            result = response.json()
            
            resposta = result['choices'][0]['message']['content']
        except Exception as e:
            resposta = f"Ocorreu um erro: {e}"
    return render_template('oraculo.html', resposta=resposta)

# 🧪 Inicia o servidor localmente
if __name__ == '__main__':
    print("Iniciando servidor Flask...")
    app.run(debug=True)







