from model.item import Item
from model.item import ArmazenamentoDiversos
from model.item import Eletronico
from model.bancodedados import BancoDados

class ControladorItem:
    def __init__(self):
        self.banco = BancoDados()

    def cadastrar_item(self, nome, sabor, valor_compra, valor_venda, quantidade, freezer_id, validade, codigo_barras):
        """Tenta cadastrar o item e retorna sucesso ou erro"""
        item = Item(nome=nome, sabor=sabor, valor_compra=valor_compra,valor_venda=valor_venda, quantidade=quantidade,validade=validade,codigo_barras=codigo_barras)
        sucesso, mensagem = self.banco.adicionar_item(item, freezer_id)
        return sucesso, mensagem

    def listar_itens(self):
        """Lista todos os itens cadastrados"""
        return self.banco.listar_itens()
    
    def obter_estoque(self):
        """Obtém o resumo do estoque"""
        return self.banco.calcular_estoque()
    
    def obter_total_armazenamento(self):
        """Retorna SOMENTE o custo total de armazenamento"""
        return self.banco.calcular_total_armazenamento()
    
    def adicionar_custo_armazenamento(self, nome, valor, quantidade, categoria):
        """Adiciona um custo de armazenamento"""
        armazenamento = ArmazenamentoDiversos(nome=nome,valor=valor, quantidade=quantidade,categoria=categoria)
        self.banco.adicionar_custo_armazenamento(nome, valor, quantidade, categoria)
    
    def cadastrar_eletronico(self, nome, kw_por_dia,quantidade,ambiente,capacidade_total):
        """Cadastra um novo eletrônico"""
        eletronico = Eletronico(nome=nome, kw_por_dia=kw_por_dia,quantidade=quantidade,ambiente=ambiente,capacidade_total=capacidade_total)
        self.banco.adicionar_freezer(eletronico.nome, eletronico.kw_por_dia,eletronico.quantidade ,eletronico.ambiente,eletronico.capacidade_total)

    def obter_consumo_energia(self, preco_kwh, ambiente):
        """Obtém o consumo mensal de energia e o custo total para um ambiente específico"""
        return self.banco.calcular_consumo_energia(preco_kwh, ambiente)
    
    def obter_top_produtos(self, ambiente="aberto"):
        """Obtém os 3 produtos mais estocados no Estoque Aberto ou Fechado"""
        return self.banco.top_produtos(ambiente=ambiente)

    def buscar_produto(self, nome=None, ambiente="aberto"):
        """Busca um produto no Estoque Aberto ou Fechado"""
        return self.banco.buscar_produto(nome, ambiente=ambiente)

    def listar_status_freezers(self, ambiente):
        """Retorna o status de ocupação de cada freezer de um ambiente específico"""
        return self.banco.listar_status_freezers(ambiente)
    
    def calcular_estoque_por_ambiente(self,ambiente_selecionando):
        """Calcula o Estoque por Ambiente"""
        return self.banco.calcular_estoque_por_ambiente(ambiente_selecionando)
    
    def mover_picole(self,sabor, freezer_origem, freezer_destino, quantidade):
        """Mover os Picoles"""
        return self.banco.mover_picole(sabor, freezer_origem, freezer_destino, quantidade)
    
    def listar_freezers(self):
        """Listar Freezers"""
        return self.banco.listar_freezers()
    
    def obter_quantidade_por_sabor(self):
        """Obter Quantidade por sabor"""
        return self.banco.obter_quantidade_por_sabor()
    
    def lancar_financeiro(self, tipo, categoria, descricao, valor, data,operador):
        """Lança uma nova receita ou despesa no financeiro"""
        return self.banco.lancar_financeiro(tipo, categoria, descricao, valor, data,operador)

    def excluir_lancamento_financeiro(self, id_lancamento):
        """Exclui um lançamento do financeiro pelo ID"""
        return self.banco.excluir_lancamento_financeiro(id_lancamento)

    def listar_lancamentos(self, data_inicio, data_fim):
        """Lista os lançamentos financeiros por período"""
        return self.banco.listar_lancamentos(data_inicio, data_fim)
    
    def finalizar_venda_com_carrinho(self, carrinho, operador, forma_pagamento):
        """Lançar os lançamentos financeiros por carrinho"""
        return self.banco.finalizar_venda_com_carrinho(carrinho, operador, forma_pagamento)
    
    def cadastrar_cupom(self, codigo, percentual_desconto, validade, limite_uso):
        return self.banco.cadastrar_cupom(codigo, percentual_desconto, validade, limite_uso)

    def listar_cupons(self):
        return self.banco.listar_cupons()

    def excluir_cupom(self, codigo):
        return self.banco.excluir_cupom(codigo)


