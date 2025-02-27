from model.item import Item
from model.bancodedados import BancoDados

class ControladorItem:
    def __init__(self):
        self.banco = BancoDados()

    def cadastrar_item(self, nome, sabor, valor, quantidade):
        """Cadastra um novo item no banco de dados"""
        item = Item(nome=nome, sabor=sabor, valor=valor, quantidade=quantidade)
        self.banco.adicionar_item(item)
