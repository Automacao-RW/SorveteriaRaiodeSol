# 🍦 Sorveteria Raio de Sol

Este é um **Sistema de Cadastro de Itens de Sorveteria** desenvolvido em Python utilizando Streamlit para interface gráfica e PostgreSQL como banco de dados, esse projeto foi desenvolvido para a materia Software Product: Analysis, Specification, Project & Implementation.

---

## Funcionalidades
Cadastro de novos itens (Nome, Sabor, Valor, Quantidade)  

---

## Tecnologias Utilizadas
- **Python 3.12**
- **Streamlit** (Interface gráfica)
- **PostgreSQL (psycopg2 Banco de Dados)**
- **Arquitetura MVC (Model-View-Controller)**

---

## Estrutura do Projeto

sorveteria_mvc/
│── model/
│   ├── item.py
│   ├── banco_dados.py
│── controller/
│   ├── controlador_item.py
│── view/ 
│   ├── app.py
│── main.py  
│── requirements.txt


## Como Instalar e Rodar o Projeto

1.Clonar o Repositório

git clone https://github.com/Automacao-RW/SorveteriaRaiodeSol
cd SORVETERIARAIODESOL

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
