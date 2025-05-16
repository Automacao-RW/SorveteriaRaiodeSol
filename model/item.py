class Item:
    def __init__(self, nome, sabor, valor_compra, valor_venda, quantidade, validade, codigo_barras):
        self.nome = nome
        self.sabor = sabor
        self.valor_compra = valor_compra
        self.valor_venda = valor_venda
        self.quantidade = quantidade
        self.validade = validade
        self.codigo_barras = codigo_barras


class ArmazenamentoDiversos:
    def __init__(self, id=None, nome="", sabor="", valor=0.0, quantidade=0,categoria=""):
        self.id = id
        self.nome = nome
        self.sabor = sabor
        self.valor = valor
        self.quantidade = quantidade
        self.categoria = categoria

class Eletronico:
    def __init__(self, id=None, nome="", kw_por_dia="",quantidade=0,ambiente="",capacidade_total=0):
        self.id = id
        self.nome = nome
        self.kw_por_dia = kw_por_dia
        self.quantidade = quantidade
        self.ambiente = ambiente
        self.capacidade_total = capacidade_total