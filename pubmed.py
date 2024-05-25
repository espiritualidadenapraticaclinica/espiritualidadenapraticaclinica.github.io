import requests
from bs4 import BeautifulSoup
import os
from github import Github
import google.generativeai as genai

# Chamando variáveis secretas
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
GITHUB_TOKEN = os.environ["TOKEN_GITHUB"]
REPO_NAME = "espiritualidadenapraticaclinica/espiritualidadenapraticaclinica.github.io"
FILE_PATH = "conteudo/index.html"

# Configuração da chave da API GenAI
genai.configure(api_key=GOOGLE_API_KEY)

# Função para buscar o conteúdo do arquivo no GitHub
def buscar_conteudo_arquivo(repo, file_path):
    file_content = repo.get_contents(file_path)
    return file_content.content, file_content.sha

# Função para atualizar o conteúdo do arquivo no GitHub
def atualizar_arquivo_github(repo, file_path, conteudo, sha, mensagem_commit):
    repo.update_file(file_path, mensagem_commit, conteudo, sha)

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

# Função para publicar o artigo no site
def publicar_artigo(titulo, abstract, url_artigo):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    
    # Busca o conteúdo atual do arquivo index.html
    conteudo_atual, sha = buscar_conteudo_arquivo(repo, FILE_PATH)

    # Cria um objeto BeautifulSoup
    soup = BeautifulSoup(conteudo_atual, "html.parser")

    # Cria um novo elemento de artigo
    new_article = soup.new_tag("article")
    new_article["id"] = "post-new"
    new_article["class"] = "post-new page type-page status-publish hentry"

    # Cria o cabeçalho do artigo
    header = soup.new_tag("header", class_="entry-header")
    title_tag = soup.new_tag("h1", class_="entry-title")
    title_tag.string = titulo
    header.append(title_tag)
    new_article.append(header)

    # Cria o conteúdo do artigo
    content = soup.new_tag("div", class_="entry-content")
    abstract_tag = soup.new_tag("p")
    abstract_tag.string = abstract
    content.append(abstract_tag)
    new_article.append(content)

    # Insere o novo artigo no início da lista de artigos
    main_content = soup.find("main", id="main")
    if main_content:
        main_content.insert(0, new_article)
    else:
        print("Erro: não foi possível encontrar a seção principal no arquivo HTML.")

    # Atualiza o conteúdo do arquivo
    conteudo_atualizado = str(soup)

    # Atualiza o arquivo no GitHub
    atualizar_arquivo_github(repo, FILE_PATH, conteudo_atualizado, sha, "Adicionando novo artigo")

    print("Artigo publicado no site com sucesso!")

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
