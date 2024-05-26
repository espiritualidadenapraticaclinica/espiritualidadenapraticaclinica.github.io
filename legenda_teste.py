# Caminho para o arquivo de texto onde a legenda será salva
legenda_arquivo = 'legenda.txt'

# Verifica se a legenda atual é diferente da legenda anterior
with open(legenda_arquivo, 'r') as file:
    print(file)
# Salva a legenda original no arquivo de texto
with open(legenda_arquivo, 'w') as file:
    file.write("testando se isso vai estar criptografado")
