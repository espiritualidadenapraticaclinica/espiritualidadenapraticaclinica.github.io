import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
import google.generativeai as genai



# Chamando variáveis secretas
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]

# Configuração da chave da API GenAI
genai.configure(api_key=GOOGLE_API_KEY)

# Função para publicar o artigo no site
def publicar_artigo(titulo, abstract, url_artigo):
    # URL da página de conteúdo do seu site
    SITE_URL = "https://espiritualidadenapraticaclinica.github.io/conteudo/"

    # Dados a serem enviados para a página do site
    data = {
        'titulo': titulo,
        'abstract': abstract,
        'url_artigo': url_artigo
    }
    
    # Fazendo uma requisição POST para publicar o artigo
    response = requests.post(SITE_URL, data=data)
    
    # Verifica se a requisição foi bem sucedida
    if response.status_code == 200:
        print("Artigo publicado no site com sucesso!")
    else:
        print(f"Falha ao publicar o artigo. Status code: {response.status_code}")

# Função para extrair informações do artigo do PubMed
def extrair_artigo_pubmed(termo_pesquisa):
    url = 'https://pubmed.ncbi.nlm.nih.gov/'
    params = {'term': termo_pesquisa, 'sort': 'date'}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        link_ultimo_artigo = soup.find('a', class_='docsum-title')['href']
        return 'https://pubmed.ncbi.nlm.nih.gov' + link_ultimo_artigo
    else:
        print(f'Erro na pesquisa PubMed: {response.status_code}')
        return None

# Função para extrair informações do artigo
def extrair_informacoes_artigo(url_artigo):
    response_artigo = requests.get(url_artigo)
    if response_artigo.status_code == 200:
        soup_artigo = BeautifulSoup(response_artigo.text, 'html.parser')
        titulo = soup_artigo.find('h1', class_='heading-title').text.strip()
        abstract = soup_artigo.find('div', class_='abstract-content').text.strip()
        return titulo, abstract
    else:
        print(f'Erro ao acessar o artigo: {response_artigo.status_code}')
        return None, None

# Função para gerar conteúdo traduzido usando o modelo GenAI
def gerar_traducao(prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    if response.candidates and len(response.candidates) > 0:
        if response.candidates[0].content.parts and len(response.candidates[0].content.parts) > 0:
            return response.candidates[0].content.parts[0].text
        else:
            print("Nenhuma parte de conteúdo encontrada na resposta.")
    else:
        print(f"Nenhum candidato válido encontrado, tentando novamente...")

# Termo de pesquisa para o PubMed
termo_pesquisa = '(spirituality OR religiosity) AND (medical practice OR medical education)'

# Pesquisar no PubMed
url_artigo_pubmed = extrair_artigo_pubmed(termo_pesquisa)

# Extrair informações do artigo
if url_artigo_pubmed:
    titulo, abstract = extrair_informacoes_artigo(url_artigo_pubmed)
    if titulo and abstract:
        # Traduzir título e abstract
        titulo_traduzido = gerar_traducao(titulo)
        abstract_traduzido = gerar_traducao(abstract)
        # Publica o artigo no site
        publicar_artigo(titulo_traduzido, abstract_traduzido, url_artigo_pubmed)
    else:
        print("Não foi possível extrair informações do artigo.")
else:
    print("Nenhum artigo encontrado para os termos de pesquisa fornecidos.")
