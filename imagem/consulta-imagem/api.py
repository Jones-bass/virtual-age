import requests
import pandas as pd
import json
import base64
from datetime import datetime
import sys
import os
from io import BytesIO
from PIL import Image

# === IMPORTA TOKEN DE AUTH ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# === CONFIGURAÇÕES ===
#URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/image/v2/product/search"
URL = "https://treino.bhan.com.br:9443/api/totvsmoda/image/v2/product/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🖼️ Consultando imagens dos produtos...")

# === FUNÇÃO PARA OBTER PRODUTOS (por lote) ===
def get_products(product_codes):
    total_products = []
    batch_size = 50  
    for i in range(0, len(product_codes), batch_size):
        batch_codes = product_codes[i:i+batch_size]
        
        payload = {
            "filter": {
                "productCodeList": batch_codes,
                "typeImageCodeList": [1]
            },
            "option": {
                "quantityImageResult": 1
            },
        }

        # Faz a requisição
        try:
            response = requests.post(URL, headers=headers, json=payload, timeout=90)
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na conexão com a API: {e}")
            sys.exit(1)

        print(f"📡 Status HTTP: {response.status_code}")
        if response.status_code != 200:
            print("❌ Erro na resposta da API:")
            print(response.text)
            sys.exit(1)

        # === TRATAMENTO DO JSON ===
        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            print("❌ Erro ao decodificar JSON da resposta.")
            sys.exit(1)

        # === PROCESSA RESPOSTA ===
        items = data.get("items", [])
        if items:
            total_products.extend(items)

    return total_products

# === INSERÇÃO DE PRODUTOS QUE VOCÊ QUER BUSCAR ===
# Exemplo de como gerar a lista de produtos: de 1 até 999
product_codes_to_search = list(range(1, 999))

# === OBTÉM OS PRODUTOS ===
produtos_data = get_products(product_codes_to_search)

# === SALVA DEBUG ===
debug_file = f"debug_product_images_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(produtos_data, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === PROCESSA OS PRODUTOS E IMAGENS ===
produtos = []
imagens = []

# === CRIA PASTA DE IMAGENS ===
img_dir = "images-totvs"
os.makedirs(img_dir, exist_ok=True)

print("🧩 Processando e salvando imagens...")

for item in produtos_data:
    product_code = item.get("productCode")

    produtos.append({
        "productCode": product_code,
        "productName": item.get("productName"),
        "referencialCode": item.get("referencialCode"),
        "colorName": item.get("colorName"),
        "sizeName": item.get("sizeName")
    })

    for img in item.get("images", []):
        image_code = img.get("imageCode")
        image_base64 = img.get("imageFile")

        image_filename = f"{product_code}_{image_code}.jpg"
        image_path = os.path.join(img_dir, image_filename)

        try:
            if image_base64:
                # Decodifica e salva imagem original
                image_bytes = base64.b64decode(image_base64)
                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)

                # Reduz imagem para miniatura (para Excel)
                thumbnail_path = image_path.replace(".jpg", "_thumb.jpg")
                image = Image.open(BytesIO(image_bytes))
                image.thumbnail((80, 80))  # tamanho pequeno
                image.save(thumbnail_path, "JPEG")
            else:
                thumbnail_path = None
        except Exception as e:
            print(f"⚠️ Erro ao salvar imagem {image_filename}: {e}")
            thumbnail_path = None

        imagens.append({
            "productCode": product_code,
            "imageCode": image_code,
            "imageName": img.get("imageName"),
            "imageDescription": img.get("imageDescription"),
            "typeImageName": img.get("typeImageName"),
            "imagePath": image_path,
            "thumbnailPath": thumbnail_path
        })

# === CONVERTE PARA DATAFRAMES ===
df_produtos = pd.DataFrame(produtos)
df_imagens = pd.DataFrame(imagens)

# === EXPORTA PARA EXCEL COM IMAGENS ===
excel_file = f"product_images_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_produtos.to_excel(writer, index=False, sheet_name="Produtos")
    df_imagens.to_excel(writer, index=False, sheet_name="Imagens")

    workbook = writer.book
    worksheet = writer.sheets["Imagens"]

    # Ajusta largura das colunas e insere miniaturas
    worksheet.set_column("A:G", 25)
    row = 1  # começa depois do cabeçalho

    for thumb_path in df_imagens["thumbnailPath"]:
        if thumb_path and os.path.exists(thumb_path):
            worksheet.set_row(row, 80)  # altura maior para imagem
            worksheet.insert_image(f"H{row+1}", thumb_path, {"x_scale": 1.2, "y_scale": 1.2})
        row += 1

print(f"✅ Relatório Excel gerado: {excel_file}")
print(f"🗂️ Imagens salvas em: {os.path.abspath(img_dir)}")
