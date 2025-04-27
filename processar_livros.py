import os
import fitz
import sqlite3

# Pasta onde ficam os PDFs
PASTA_PDFS = "bases_teoricas"

def extrair_texto_pdf(caminho_pdf):
    doc = fitz.open(caminho_pdf)
    texto_total = []
    for num_pagina, pagina in enumerate(doc, start=1):
        texto = pagina.get_text()
        texto_limpo = texto.strip().replace('\n', ' ').replace('  ', ' ')
        texto_total.append(f"--- Página {num_pagina} ---\n{texto_limpo}\n")
    doc.close()
    return texto_total

def salvar_txt(texto, caminho_txt):
    with open(caminho_txt, "w", encoding="utf-8") as f:
        f.writelines(texto)

def salvar_em_sqlite(texto_por_pagina, caminho_db):
    conn = sqlite3.connect(caminho_db)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paginas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pagina INTEGER,
            conteudo TEXT
        )
    """)
    for entrada in texto_por_pagina:
        try:
            num = int(entrada.split("--- Página ")[1].split(" ---")[0])
            conteudo = entrada.split("---")[2].strip()
            cursor.execute("INSERT INTO paginas (pagina, conteudo) VALUES (?, ?)", (num, conteudo))
        except Exception as e:
            print(f"Erro ao processar página: {e}")
    conn.commit()
    conn.close()

def processar_todos_os_pdfs():
    for nome_arquivo in os.listdir(PASTA_PDFS):
        if nome_arquivo.endswith(".pdf"):
            nome_base = os.path.splitext(nome_arquivo)[0]
            caminho_pdf = os.path.join(PASTA_PDFS, nome_arquivo)
            print(f"Processando: {nome_arquivo}")

            texto = extrair_texto_pdf(caminho_pdf)

            caminho_txt = os.path.join(PASTA_PDFS, f"{nome_base}.txt")
            caminho_db = os.path.join(PASTA_PDFS, f"{nome_base}.db")

            salvar_txt(texto, caminho_txt)
            salvar_em_sqlite(texto, caminho_db)

            print(f">>> {nome_arquivo} finalizado com sucesso.\n")

if __name__ == "__main__":
    processar_todos_os_pdfs()
