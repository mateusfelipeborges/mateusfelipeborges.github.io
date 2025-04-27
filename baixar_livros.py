import requests
import os

def baixar_do_drive(file_id, destino_local):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    resposta = requests.get(url)
    if resposta.status_code == 200:
        with open(destino_local, 'wb') as f:
            f.write(resposta.content)
        print(f"✅ Arquivo salvo em: {destino_local}")
    else:
        print(f"❌ Erro ao baixar o arquivo. Status: {resposta.status_code}")

# Cria a pasta se não existir
os.makedirs("bases_teoricas", exist_ok=True)

# Baixar o livro com base no ID fornecido
baixar_do_drive(
    "13yaJGcJvB4H27Opwy7AnejJNoXO87jGf",
    "bases_teoricas/livro_1_freud_jung.pdf"
)
