import psycopg2
from model.item import Item
from datetime import datetime

class BancoDados:
    def __init__(self):
        """Inicializa a conexão com o banco PostgreSQL"""
        self.conexao = psycopg2.connect(
            dbname="sorveteria",  
            user="postgres",      
            password="xxxxxx",
            host="localhost",     
            port="5432"           
        )
        self.cursor = self.conexao.cursor()

        if not self._tabelas_existem():
            print("Tabelas não encontradas. Criando...")
            self._criar_tabela()
        else:
            print("Tabelas já existem. Nenhuma alteração feita.")

    def _tabelas_existem(self):
        """Verifica se as tabelas já existem no banco de dados"""
        self.cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'itens'
            )
        """)
        return self.cursor.fetchone()[0]

    def _criar_tabela(self):
        """Cria as tabelas no PostgreSQL se não existirem"""
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS eletronicos (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                kw_por_dia REAL NOT NULL,
                quantidade INTEGER NOT NULL,
                ambiente TEXT NOT NULL,
                capacidade_total INTEGER NOT NULL,
                status TEXT DEFAULT 'Disponível',  -- Novo campo para controlar o status do freezer
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS itens (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                sabor TEXT NOT NULL,
                valor_compra REAL NOT NULL,
                valor_venda REAL NOT NULL,
                validade DATE,
                quantidade INTEGER NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                freezer_id INTEGER REFERENCES eletronicos(id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS custos_armazenamento (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                valor REAL NOT NULL,
                quantidade INTEGER NOT NULL,
                categoria TEXT NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS financeiro (
                id SERIAL PRIMARY KEY,
                tipo TEXT NOT NULL CHECK (tipo IN ('Receita', 'Despesa')),
                valor REAL NOT NULL CHECK (valor >= 0),
                descricao TEXT NOT NULL,
                categoria TEXT NOT NULL,
                data_lancamento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.cursor.execute('''
            DROP TRIGGER IF EXISTS trigger_atualizar_status_freezer ON itens;
        ''')

        self.cursor.execute('''
            CREATE OR REPLACE FUNCTION atualizar_status_freezer() RETURNS TRIGGER AS $$
            BEGIN
                UPDATE eletronicos 
                SET status = 
                    CASE 
                        WHEN (SELECT COALESCE(SUM(quantidade), 0) FROM itens WHERE freezer_id = NEW.freezer_id) >= capacidade_total
                        THEN 'Cheio'
                        ELSE 'Disponível'
                    END
                WHERE id = NEW.freezer_id;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        ''')

        self.cursor.execute('''
            CREATE TRIGGER trigger_atualizar_status_freezer
            AFTER INSERT OR UPDATE ON itens
            FOR EACH ROW
            EXECUTE FUNCTION atualizar_status_freezer();
        ''')

        self.conexao.commit()

    def calcular_estoque(self):
        """Calcula a quantidade total de produtos e valor do estoque,
        separando os itens com base no ambiente do freezer (Estoque Aberto ou Fechado)."""

        self.cursor.execute("""
            SELECT 
                SUM(i.quantidade) AS quantidade_total, 
                SUM(i.quantidade * i.valor_venda) AS valor_total,
                SUM(CASE WHEN e.ambiente = 'Estoque Aberto' THEN i.quantidade ELSE 0 END) AS estoque_aberto,
                SUM(CASE WHEN e.ambiente = 'Estoque Fechado' THEN i.quantidade ELSE 0 END) AS estoque_fechado,
                SUM(CASE WHEN e.ambiente = 'Estoque Aberto' THEN i.quantidade * i.valor_venda ELSE 0 END) AS valor_aberto,
                SUM(CASE WHEN e.ambiente = 'Estoque Fechado' THEN i.quantidade * i.valor_venda ELSE 0 END) AS valor_fechado
            FROM itens i
            LEFT JOIN eletronicos e ON i.freezer_id = e.id
        """)

        resultado = self.cursor.fetchone()
        
        return {
            "quantidade_total": resultado[0] if resultado[0] is not None else 0,
            "valor_total": resultado[1] if resultado[1] is not None else 0.0,
            "estoque_aberto": resultado[2] if resultado[2] is not None else 0,
            "estoque_fechado": resultado[3] if resultado[3] is not None else 0,
            "valor_aberto": resultado[4] if resultado[4] is not None else 0.0,
            "valor_fechado": resultado[5] if resultado[5] is not None else 0.0
        }

    def buscar_produto(self, nome=None, ambiente="Estoque Aberto"):
        """Busca um produto pelo nome e filtra apenas os que pertencem ao ambiente especificado."""

        if nome:
            self.cursor.execute("""
                SELECT i.id, i.nome, i.sabor, i.valor_venda, i.quantidade, i.data_criacao,i.validade
                FROM itens i
                LEFT JOIN eletronicos e ON i.freezer_id = e.id
                WHERE e.ambiente = %s AND i.nome ILIKE %s
            """, (ambiente, f"%{nome}%"))
        else:
            self.cursor.execute("""
                SELECT i.id, i.nome, i.sabor, i.valor_venda, i.quantidade, i.data_criacao,i.validade
                FROM itens i
                LEFT JOIN eletronicos e ON i.freezer_id = e.id
                WHERE e.ambiente = %s
            """, (ambiente,))

        itens = self.cursor.fetchall()
        return [
            {
                "id": item[0],
                "nome": item[1],
                "sabor": item[2],
                "valor": item[3],
                "quantidade": item[4],
                "data_criacao": item[5].strftime("%d/%m/%Y %H:%M:%S"),
                "validade": item[6].strftime("%d/%m/%Y %H:%M:%S")
            }
            for item in itens
        ]

    def top_produtos(self, limite=3, ambiente="Estoque Aberto"):
        """Retorna os produtos mais estocados no ambiente especificado (Aberto ou Fechado)."""

        self.cursor.execute("""
            SELECT i.nome, SUM(i.quantidade) AS estoque
            FROM itens i
            LEFT JOIN eletronicos e ON i.freezer_id = e.id
            WHERE e.ambiente = %s
            GROUP BY i.nome
            ORDER BY estoque DESC
            LIMIT %s
        """, (ambiente, limite))
        
        return self.cursor.fetchall()

    def listar_custos_armazenamento(self):
        """Lista os custos de armazenamento"""
        self.cursor.execute("SELECT nome, valor FROM custos_armazenamento")
        return self.cursor.fetchall()
    
    def calcular_total_armazenamento(self):
        """Calcula o custo total de armazenamento SOMENTE da tabela de custos"""
        self.cursor.execute("SELECT SUM(valor) FROM custos_armazenamento")
        total_custos = self.cursor.fetchone()[0]
        return total_custos if total_custos is not None else 0.0 
    
    def adicionar_custo_armazenamento(self, nome, valor, quantidade, categoria):
        """Adiciona um custo de armazenamento ou soma a quantidade e o valor total se já existir"""
        try:
            self.cursor.execute("BEGIN;")

            nome_normalizado = nome.strip().lower()

            self.cursor.execute(
                "SELECT id, quantidade, valor FROM custos_armazenamento WHERE LOWER(nome) = %s AND categoria = %s",
                (nome_normalizado, categoria)
            )
            resultado = self.cursor.fetchone()

            if resultado:
                custo_id, quantidade_atual, valor_atual = resultado
                nova_quantidade = quantidade_atual + quantidade
                novo_valor = valor_atual + (valor * quantidade)

                self.cursor.execute(
                    "UPDATE custos_armazenamento SET quantidade = %s, valor = %s WHERE id = %s",
                    (nova_quantidade, novo_valor, custo_id)
                )
            else:
                self.cursor.execute(
                    "INSERT INTO custos_armazenamento (nome, valor, quantidade, categoria) VALUES (%s, %s, %s, %s)",
                    (nome_normalizado, valor * quantidade, quantidade, categoria)
                )

            self.conexao.commit()
        except Exception as e:
            self.conexao.rollback()
            print(f"Erro ao adicionar custo de armazenamento: {e}")
    

    def adicionar_freezer(self, nome, kw_por_dia,quantidade, ambiente, capacidade_total):
        """Adiciona múltiplos freezers individualmente no banco de dados"""
        try:
            self.cursor.execute("BEGIN;")
            
            for _ in range(quantidade):  
                self.cursor.execute(
                    "INSERT INTO eletronicos (nome, kw_por_dia, quantidade, ambiente, capacidade_total) VALUES (%s, %s, %s, %s, %s)",
                    (nome, kw_por_dia, 1, ambiente, capacidade_total) 
                )

            self.conexao.commit()
            print(f"✅ {quantidade} freezer(s) cadastrado(s) com sucesso!")

        except Exception as e:
            self.conexao.rollback()
            print(f"❌ Erro ao adicionar freezer: {e}")
    
    def calcular_consumo_energia(self, preco_kwh, ambiente):
        """Calcula o consumo total de energia mensal dos eletrônicos para um ambiente específico e o custo total"""
        try:
            self.cursor.execute(
                "SELECT SUM(kw_por_dia * 1) FROM eletronicos WHERE ambiente = %s",
                (ambiente,)
            )
            resultado = self.cursor.fetchone()
            consumo_mensal_kwh = resultado[0] * 30 if resultado[0] is not None else 0 

            custo_total = consumo_mensal_kwh * preco_kwh 

            return {
                "consumo_mensal_kwh": round(consumo_mensal_kwh, 2),
                "custo_total": round(custo_total, 2)
            }
        except Exception as e:
            print(f"Erro ao calcular consumo de energia para {ambiente}: {e}")
            return {"consumo_mensal_kwh": 0, "custo_total": 0}
    
    def listar_itens(self):
        """Retorna todos os itens cadastrados no banco, garantindo que a data seja lida corretamente."""
        self.cursor.execute("""
            SELECT id, nome, sabor, valor_compra, valor_venda, quantidade, data_criacao, freezer_id,validade
            FROM itens
        """)
        itens = self.cursor.fetchall()
        
        return [
            {
                "id": item[0], 
                "nome": item[1], 
                "sabor": item[2], 
                "valor_compra": item[3],  
                "valor_venda": item[4],  
                "quantidade": item[5], 
                "data_criacao": item[6].strftime("%d/%m/%Y %H:%M:%S") if isinstance(item[6], (str, bytes)) else item[6],  
                "freezer_id": item[7],
                "validade": item[8].strftime("%d/%m/%Y %H:%M:%S") if isinstance(item[8], (str, bytes)) else item[8],  
            }
            for item in itens
        ]

    def listar_freezers(self):
        """Retorna todos os freezers cadastrados no banco de dados"""
        self.cursor.execute("SELECT id, nome, kw_por_dia, ambiente, capacidade_total FROM eletronicos")
        freezers = self.cursor.fetchall()

        return [
            {
                "id": freezer[0], 
                "nome": freezer[1], 
                "kw_por_dia": freezer[2],
                "ambiente": freezer[3],  
                "capacidade_total": freezer[4]
            }
            for freezer in freezers
        ]
    
    def listar_status_freezers(self, ambiente, sabor=None):
        """Retorna o uso dos freezers filtrados por ambiente e, opcionalmente, a quantidade de um sabor específico."""
        self.cursor.execute("""
            SELECT 
                e.id,
                e.nome,
                e.ambiente,
                e.capacidade_total,
                COALESCE(SUM(i.quantidade), 0) AS ocupado,
                (e.capacidade_total - COALESCE(SUM(i.quantidade), 0)) AS disponivel,
                ROUND((COALESCE(SUM(i.quantidade), 0) * 100.0) / e.capacidade_total, 2) AS percentual_ocupado,
                COALESCE(SUM(CASE WHEN i.sabor = %s THEN i.quantidade ELSE 0 END), 0) AS quantidade_sabor
            FROM eletronicos e
            LEFT JOIN itens i ON e.id = i.freezer_id
            WHERE e.ambiente = %s AND e.capacidade_total > 1 -- Filtrando pelo ambiente especificado
            GROUP BY e.id, e.nome, e.ambiente, e.capacidade_total
            ORDER BY e.id;
        """, (sabor, ambiente))

        freezers = self.cursor.fetchall()
        return [
            {
                "id": freezer[0],
                "nome": freezer[1],
                "ambiente": freezer[2],
                "capacidade_total": freezer[3],
                "ocupado": freezer[4],
                "disponivel": freezer[5],
                "percentual_ocupado": float(freezer[6]),
                "quantidade_sabor": freezer[7] 
            }
            for freezer in freezers
        ]


    def adicionar_item(self, item: Item, freezer_id):
        """Adiciona um item ao estoque, respeitando a capacidade do freezer selecionado"""
        try:
            self.cursor.execute("BEGIN;")

            self.cursor.execute("""
                SELECT capacidade_total - COALESCE((SELECT SUM(quantidade) FROM itens WHERE freezer_id = e.id), 0) AS espaco_disponivel
                FROM eletronicos e WHERE id = %s
            """, (freezer_id,))
            resultado = self.cursor.fetchone()

            if not resultado:
                raise Exception(f"❌ Erro: Freezer {freezer_id} não encontrado no banco de dados!")

            espaco_disponivel = resultado[0]

            if item.quantidade > espaco_disponivel:
                raise Exception(f"❌ O freezer selecionado só tem espaço para {espaco_disponivel} picolés!")

            self.cursor.execute(
                "SELECT id, quantidade FROM itens WHERE nome = %s AND sabor = %s AND freezer_id = %s",
                (item.nome, item.sabor, freezer_id)
            )
            resultado = self.cursor.fetchone()

            if resultado:
                item_id, quantidade_atual = resultado
                nova_quantidade = quantidade_atual + item.quantidade

                self.cursor.execute(
                    "UPDATE itens SET quantidade = %s WHERE id = %s",
                    (nova_quantidade, item_id)
                )
            else:
                self.cursor.execute('''
                    INSERT INTO itens (nome, sabor, valor_compra, valor_venda, quantidade, validade, freezer_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (item.nome, item.sabor, item.valor_compra, item.valor_venda, item.quantidade, item.validade, freezer_id))

            self.conexao.commit()
            return True, f"✅ Item '{item.nome}' cadastrado corretamente no Freezer {freezer_id}!"

        except Exception as e:
            self.conexao.rollback()
            return False, str(e)
        
    def calcular_estoque_por_ambiente(self, ambiente):
        """Calcula a quantidade e valor do estoque com base no ambiente do freezer (Aberto ou Fechado)."""
        self.cursor.execute("""
            SELECT SUM(i.quantidade), SUM(i.quantidade * i.valor_venda)
            FROM itens i
            JOIN eletronicos e ON i.freezer_id = e.id
            WHERE e.ambiente = %s
        """, (ambiente,))
        
        resultado = self.cursor.fetchone()
        
        return {
            "quantidade": resultado[0] if resultado[0] is not None else 0,
            "valor": resultado[1] if resultado[1] is not None else 0.0
        }
    
    def mover_picole(self, sabor, freezer_origem, freezer_destino, quantidade):
        """Move um determinado número de picolés de um freezer para outro"""
        try:
            self.cursor.execute("BEGIN;")

            self.cursor.execute("""
                SELECT id, quantidade FROM itens 
                WHERE sabor = %s AND freezer_id = %s
                ORDER BY id
            """, (sabor, freezer_origem))

            registros_origem = self.cursor.fetchall()

            if not registros_origem:
                raise Exception(f"❌ Nenhum sorvete de sabor {sabor} encontrado no Freezer {freezer_origem}!")

            quantidade_disponivel = sum(item[1] for item in registros_origem)
            if quantidade_disponivel < quantidade:
                raise Exception(f"❌ Apenas {quantidade_disponivel} picolés disponíveis no Freezer {freezer_origem}!")

            self.cursor.execute("""
                SELECT e.capacidade_total - COALESCE(SUM(i.quantidade), 0)
                FROM eletronicos e
                LEFT JOIN itens i ON e.id = i.freezer_id
                WHERE e.id = %s
                GROUP BY e.capacidade_total
            """, (freezer_destino,))

            espaco_disponivel = self.cursor.fetchone()[0]

            if espaco_disponivel < quantidade:
                raise Exception(f"❌ O Freezer {freezer_destino} tem apenas {espaco_disponivel} espaços disponíveis!")

            self.cursor.execute("""
                SELECT id, quantidade FROM itens 
                WHERE sabor = %s AND freezer_id = %s
            """, (sabor, freezer_destino))

            destino_existente = self.cursor.fetchone()

            if destino_existente:
                item_destino_id, quantidade_destino = destino_existente
                nova_quantidade_destino = quantidade_destino + quantidade

                self.cursor.execute("""
                    UPDATE itens SET quantidade = %s WHERE id = %s
                """, (nova_quantidade_destino, item_destino_id))
            else:
                self.cursor.execute("""
                    INSERT INTO itens (nome, sabor, valor_compra, valor_venda, quantidade, freezer_id, validade)
                    SELECT nome, sabor, valor_compra, valor_venda, %s, %s, validade
                    FROM itens WHERE id = %s
                """, (quantidade, freezer_destino, registros_origem[0][0]))

            quantidade_restante = quantidade
            for item_id, qtd in registros_origem:
                if quantidade_restante == 0:
                    break
                if qtd > quantidade_restante:
                    self.cursor.execute("""
                        UPDATE itens SET quantidade = quantidade - %s WHERE id = %s
                    """, (quantidade_restante, item_id))
                    quantidade_restante = 0
                else:
                    self.cursor.execute("DELETE FROM itens WHERE id = %s", (item_id,))
                    quantidade_restante -= qtd

            self.conexao.commit()
            return True, f"✅ {quantidade} picolés de {sabor} movidos do Freezer {freezer_origem} para o Freezer {freezer_destino}!"

        except Exception as e:
            self.conexao.rollback()
            return False, str(e)


    def obter_quantidade_por_sabor(self):
        """Retorna a quantidade de cada sabor dentro de cada freezer"""
        self.cursor.execute("""
            SELECT freezer_id, sabor, SUM(quantidade)
            FROM itens
            GROUP BY freezer_id, sabor
        """)
        
        resultado = self.cursor.fetchall()

        quantidades = {}
        for freezer_id, sabor, quantidade in resultado:
            if freezer_id not in quantidades:
                quantidades[freezer_id] = {}
            quantidades[freezer_id][sabor] = quantidade

        return quantidades

    def lancar_financeiro(self, tipo, categoria, descricao, valor, data=None):
        try:
            if data is None:
                data = datetime.now().date()
            self.cursor.execute("""
                INSERT INTO financeiro (tipo, categoria, descricao, valor, data_lancamento)
                VALUES (%s, %s, %s, %s, %s)
            """, (tipo, categoria, descricao, valor, data))
            self.conexao.commit()
            return True
        except Exception as e:
            print("Erro ao lançar financeiro:", e)
            self.conexao.rollback()
            return False

    def obter_resumo_financeiro(self, data_inicio, data_fim):
        self.cursor.execute("""
            SELECT tipo, SUM(valor)
            FROM financeiro
            WHERE data_lancamento BETWEEN %s AND %s
            GROUP BY tipo
        """, (data_inicio, data_fim))
        return self.cursor.fetchall()
    
    def excluir_lancamento_financeiro(self, id_lancamento):
        self.cursor.execute("DELETE FROM financeiro WHERE id = %s", (id_lancamento,))
        self.conexao.commit()
        return True
    
    def listar_lancamentos(self, data_inicio, data_fim):
        self.cursor.execute("""
            SELECT id, tipo, categoria, descricao, valor, data_lancamento
            FROM financeiro
            WHERE data_lancamento BETWEEN %s AND %s
            ORDER BY data_lancamento DESC
        """, (data_inicio, data_fim))
        resultados = self.cursor.fetchall()
        return [
            {
                "id": r[0], "tipo": r[1], "categoria": r[2], "descricao": r[3],
                "valor": r[4], "data": r[5].strftime("%d/%m/%Y")
            } for r in resultados
        ]



        

