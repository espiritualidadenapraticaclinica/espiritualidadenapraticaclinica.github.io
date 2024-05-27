import requests
from bs4 import BeautifulSoup
import os
from github import Github
import base64

# Chamando variáveis secretas
GITHUB_TOKEN = os.environ["TOKEN_GITHUB"]
REPO_NAME = "espiritualidadenapraticaclinica/espiritualidadenapraticaclinica.github.io"
FILE_PATH = "conteudo/index.html"

# Função para descriptografar o conteúdo do arquivo
def descriptografar_conteudo(conteudo_criptografado):
    conteudo_descriptografado = base64.b64decode(conteudo_criptografado).decode("utf-8")
    return conteudo_descriptografado

# Função para buscar o conteúdo do arquivo no GitHub
def buscar_conteudo_arquivo(repo, file_path):
    file_content = repo.get_contents(file_path)
    conteudo_bytes = file_content.content
    
    # Decodifica o conteúdo em Base64, se necessário
    try:
        conteudo_bytes = base64.b64decode(conteudo_bytes)
    except base64.binascii.Error:
        pass  # O conteúdo não está codificado em Base64

    # Verifica se o conteúdo está criptografado
    if isinstance(conteudo_bytes, bytes) and conteudo_bytes.startswith(b"ENCRYPTED:"):
        conteudo_bytes = descriptografar_conteudo(conteudo_bytes[len(b"ENCRYPTED:"):])

    # Decodifica o conteúdo para string
    conteudo = conteudo_bytes.decode('utf-8') if isinstance(conteudo_bytes, bytes) else conteudo_bytes
    
    return conteudo, file_content.sha

# Função para atualizar o conteúdo do arquivo no GitHub
def atualizar_arquivo_github(repo, file_path, conteudo, sha, mensagem_commit):
    # Usando a API do GitHub para fazer upload do arquivo
    repo.update_file(file_path, mensagem_commit, conteudo, sha)

    print("Arquivo atualizado no GitHub com sucesso!")

# Função para extrair informações do artigo do PubMed
def extrair_artigo_pubmed(termo_pesquisa):
    url = 'https://pubmed.ncbi.nlm.nih.gov/'
    params = {'term': termo_pesquisa, 'sort': 'date'}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        artigo = soup.find('a', class_='docsum-title')
        if artigo:
            link_ultimo_artigo = artigo['href']
            titulo = artigo.text.strip()
            url_artigo = 'https://pubmed.ncbi.nlm.nih.gov' + link_ultimo_artigo
            return titulo, url_artigo
    else:
        print(f'Erro na pesquisa PubMed: {response.status_code}')
        return None, None

# Função para extrair autores do artigo
def extrair_autores(url_artigo):
    response_artigo = requests.get(url_artigo)
    if response_artigo.status_code == 200:
        soup_artigo = BeautifulSoup(response_artigo.text, 'html.parser')
        autores = soup_artigo.find('div', class_='authors-list').text.strip()
        return autores
    else:
        print(f'Erro ao acessar o artigo: {response_artigo.status_code}')
        return None

# Função para publicar o artigo no site
def publicar_artigo(titulo, autores, url_artigo):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    
    # Busca o conteúdo atual do arquivo index.html
    conteudo_atual, sha = buscar_conteudo_arquivo(repo, FILE_PATH)

    # Cria um objeto BeautifulSoup
    soup = BeautifulSoup(conteudo_atual, "html.parser")

    # Verifica se a seção principal existe
    main_content = soup.find("main", id="main")
    if not main_content:
        print("Erro: não foi possível encontrar a seção principal no arquivo HTML.")
        return

    # Localiza a seção "ARTIGOS E TESES"
    artigos_teses = main_content.find("strong", string="ARTIGOS E TESES:")
    if not artigos_teses:
        print("Erro: não foi possível encontrar a seção 'ARTIGOS E TESES' no arquivo HTML.")
        return

    # Verifica se a seção "ARTIGOS PUBMED" já existe
    artigos_pubmed_section = main_content.find("strong", string="ARTIGOS PUBMED:")
    if not artigos_pubmed_section:
        # Cria o subtítulo "ARTIGOS PUBMED" antes da seção "ARTIGOS E TESES"
        artigos_pubmed_section = soup.new_tag("p")
        strong_tag = soup.new_tag("strong")
        strong_tag.string = "ARTIGOS PUBMED:"
        artigos_pubmed_section.append(strong_tag)
        artigos_teses.parent.insert_before(artigos_pubmed_section)

    # Cria um novo elemento de artigo
    new_article = soup.new_tag("article")
    new_article["id"] = "post-new"
    new_article["class"] = "post-new page type-page status-publish hentry"

    # Cria o cabeçalho do artigo
    header = soup.new_tag("header", class_="entry-header")
    title_tag = soup.new_tag("h2", class_="entry-title")
    title_tag.string = titulo
    header.append(title_tag)
    new_article.append(header)

    # Cria o conteúdo do artigo
    content = soup.new_tag("div", class_="entry-content")
    autores_tag = soup.new_tag("p")
    autores_tag.string = "Autores: " + autores
    link_tag = soup.new_tag("a", href=url_artigo)
    link_tag.string = "Leia mais"
    content.append(autores_tag)
    content.append(link_tag)
    new_article.append(content)

    # Insere o novo artigo após a seção "ARTIGOS PUBMED"
    artigos_pubmed_section.insert_after(new_article)

    # Atualiza o conteúdo do arquivo
    conteudo_atualizado = str(soup)

    # Atualiza o arquivo no GitHub
    atualizar_arquivo_github(repo, FILE_PATH, conteudo_atualizado, sha, "Adicionando novo artigo")

    print("Artigo publicado no site com sucesso!")

# Termo de pesquisa para o PubMed
termo_pesquisa = '(spirituality OR religiosity) AND (medical practice OR medical education)'

# Pesquisar no PubMed
titulo, url_artigo_pubmed = extrair_artigo_pubmed(termo_pesquisa)

# Extrair informações do artigo
if titulo and url_artigo_pubmed:
    autores = extrair_autores(url_artigo_pubmed)
    if autores:
        # Publica o artigo no site
        publicar_artigo(titulo, autores, url_artigo_pubmed)
    else:
        print("Não foi possível extrair informações do artigo.")
else:
    print("Nenhum artigo encontrado para os termos de pesquisa fornecidos.")
