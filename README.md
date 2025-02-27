# 🍦 Sorveteria Raio de Sol

Este é um **Sistema de Cadastro de Itens de Sorveteria** desenvolvido em Python utilizando Streamlit para interface gráfica, esse projeto foi desenvolvido em Conjunto com Rafael Antonio dos Santos para a materia Software Product: Analysis, Specification, Project & Implementation.

---

## Funcionalidades
Cadastro de novos itens (Nome, Sabor, Valor, Quantidade)  

---

## Tecnologias Utilizadas
- **Python 3.12**
- **Streamlit** (Interface gráfica)
- **Arquitetura MVC (Model-View-Controller)**

---

## Estrutura do Projeto

SORVETERIA_WEB/
│️── model/
│   ├── item.py          # Modelo do item
│   ├── banco_dados.py   # Simulação do banco de dados (TXT)
│️── controller/
│   ├── controlador_item.py  # Regras de controle
│️── app.py               # Interface gráfica com Streamlit
│️── requirements.txt      # Dependências do projeto
│️── README.md            # Documentação do projeto

## Como Instalar e Rodar o Projeto

1.Clonar o Repositório

git clone https://github.com/WagnerOliveiraP/sorveteria-web.git
cd sorveteria-web

2.Criar e Ativar o Ambiente Virtual

python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows

3.Instalar Dependências

pip install -r requirements.txt

4.Rodar a Aplicação

streamlit run app.py

Isso abrirá a interface no navegador automaticamente. 

## Contribuição

Sinta-se à vontade para abrir issues e pull requests para contribuir com melhorias no projeto!

Desenvolvido por [Wagner Olivera e Rafael Antonio] 🚀
