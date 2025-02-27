import psycopg2
from model.item import Item

class BancoDados:
    def __init__(self):
        """Inicializa a conexão com o banco PostgreSQL"""
        self.conexao = psycopg2.connect(
            dbname="sorveteria",    
            user="postgres",        
            password="********",   
            host="localhost",      
            port="5432"             
        )
        self.cursor = self.conexao.cursor()
        self._criar_tabela()

    def _criar_tabela(self):
        """Cria a tabela no PostgreSQL se não existir"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS itens (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                sabor TEXT NOT NULL,
                valor REAL NOT NULL,
                quantidade INTEGER NOT NULL
            )
        ''')
        self.conexao.commit()

    def adicionar_item(self, item: Item):
        """Adiciona um novo item ao banco de dados"""
        self.cursor.execute(
            "INSERT INTO itens (nome, sabor, valor, quantidade) VALUES (%s, %s, %s, %s) RETURNING id",
            (item.nome, item.sabor, item.valor, item.quantidade)
        )
        self.conexao.commit()