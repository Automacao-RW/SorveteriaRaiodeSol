import streamlit as st
import os 
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from controller.controlador_item import ControladorItem
import pandas as pd
from datetime import datetime, timedelta
import tempfile
import pdfkit
from fpdf import FPDF
import os


# Configuração da página
st.set_page_config(page_title="App-Sorveteria-Raio-de-Sol")

# Instanciando a Classe do Controlador
controlador = ControladorItem()

def interface():
    st.title("🍦 Sorveteria Raio de Sol")
    menu = st.sidebar.selectbox("Escolha uma opção:", ["Cadastrar Sorvete","Cadastrar Despesas Gerais","Cadastrar Eletrônico","Estoque Aberto", "Estoque Fechado","Transferencia de Produtos","Financeiro","PDV (Venda)","Cupons"])

    #Cadastrar Item
    if menu == "Cadastrar Sorvete":
        st.header("Cadastrar Novo Sorvete")

        nome = st.text_input("Nome do sorvete:")
        sabor = st.text_input("Sabor:")
        valor_compra = st.number_input("Valor de Compra (R$):", min_value=0.0, step=0.01)
        valor_venda = st.number_input("Valor de Venda (R$):", min_value=0.0, step=0.01)
        quantidade = st.number_input("Quantidade:", min_value=0, step=1)
        validade = st.date_input("Data de Validade:")
        codigo_barras = st.text_input("Código de Barras:")



        freezers = controlador.listar_status_freezers("Estoque Aberto") + controlador.listar_status_freezers("Estoque Fechado")
        freezer_options = {
            f"Freezer {f['id']} - {f['ambiente']} (Capacidade: {f['capacidade_total']} | Disponível: {f['disponivel']})": f["id"]
            for f in freezers
        }

        if freezer_options:
            freezer_selecionado = st.selectbox("Escolha o Freezer:", list(freezer_options.keys()))

            if st.button("Cadastrar"):
                freezer_id = freezer_options[freezer_selecionado]
                sucesso, mensagem = controlador.cadastrar_item(nome, sabor, valor_compra, valor_venda, quantidade, freezer_id, validade, codigo_barras)
                if sucesso:
                    st.success(mensagem)
                else:
                    st.error(mensagem)
        else:          
            st.warning("⚠️ Nenhum freezer disponível para cadastro. Libere espaço antes de adicionar novos itens!")
      
    #Estoque Aberto
    elif menu == "Estoque Aberto":
        st.header("📦 Estoque Aberto - Visão Geral")

        estoque = controlador.obter_estoque()
        custo_armazenamento = controlador.obter_total_armazenamento()
        limite_critico = 10
        estoque_por_sabor_freezer = {}

        for item in controlador.listar_itens():
            chave = (item["sabor"], item["freezer_id"])
            estoque_por_sabor_freezer[chave] = estoque_por_sabor_freezer.get(chave, 0) + item["quantidade"]
        itens_criticos = [
            f"{sabor} - {quantidade} unidade(s) (Freezer {freezer_id})"
            for (sabor, freezer_id), quantidade in estoque_por_sabor_freezer.items()
            if quantidade <= limite_critico
        ]
        if itens_criticos:
            st.warning("⚠️ Atenção! Os seguintes produtos estão com estoque crítico em seus respectivos freezers:\n\n" + "\n".join(itens_criticos))

        hoje = datetime.today().date()
        limite_validade = hoje + timedelta(days=10)
        produtos_promocao = []

        for item in controlador.listar_itens():
            validade = item.get("validade")

            if validade and isinstance(validade, str):
                validade = datetime.strptime(validade, "%d/%m/%Y").date()

            if validade and validade <= limite_validade:  
                preco_original = item["valor_venda"]
                preco_promocional = round(preco_original * 0.7, 2)
                produtos_promocao.append(f"🔔 {item['nome']} ({item['sabor']}) - Validade: {validade.strftime('%d/%m/%Y')} "
                                        f"➡️ Sugestão de Promoção: **R$ {preco_promocional:.2f}** (de R$ {preco_original:.2f})")

        if produtos_promocao:
            st.warning("⚠️ **Atenção! Produtos próximos da validade:**\n\n" + "\n".join(produtos_promocao))
        

        st.markdown("---")
        preco_kwh = st.number_input("💡 Preço do kWh (R$):", min_value=0.0, value=0.90, format="%.2f")
        ambiente = "Estoque Aberto"  
        consumo_energia = controlador.obter_consumo_energia(preco_kwh, ambiente)
        freezers = controlador.listar_status_freezers(ambiente)
        estoque_ambiente = controlador.calcular_estoque_por_ambiente(ambiente)

        st.markdown("---")
        st.write(f"📦 {ambiente}: **{estoque_ambiente['quantidade']}** — 💰 Valor: **R$ {estoque_ambiente['valor']:.2f}**")
        st.write(f"⚡ Consumo de Energia Mês ({ambiente}): **{consumo_energia['consumo_mensal_kwh']} kWh**")
        st.write(f"⚡  Custo Total de Energia ({ambiente}): **R$ {consumo_energia['custo_total']:.2f}**")  
        st.write(f"📋 Custos com Armazenamento: **R$ {custo_armazenamento:.2f}**")

        st.markdown("---")
        st.subheader(f"🏆 Principais Produtos no Estoque")
        top_produtos = controlador.obter_top_produtos(ambiente=ambiente)
        for i, (nome, quantidade) in enumerate(top_produtos, start=1):
            st.write(f"**{i}. {nome}** - {quantidade} unidades")

        
        for freezer in freezers:
            st.subheader(f"🏠 {freezer['ambiente']} - {freezer['nome']}")
            st.write(f"📏 Capacidade Total: **{freezer['capacidade_total']}** picolés")
            st.write(f"📦 Ocupado: **{freezer['ocupado']}** picolés")
            st.write(f"⬜ Disponível: **{freezer['disponivel']}** picolés")
            st.progress(freezer['percentual_ocupado'] / 100) 
            st.write(f"📊 **{freezer['percentual_ocupado']}%** ocupado")

        st.markdown("---")
        st.subheader(f"🔍 Buscar Produto no Estoque")
        nome_produto = st.text_input(f"Digite o nome do produto no Estoque")

        if st.button("Buscar") or nome_produto == "":
            resultados = controlador.buscar_produto(nome_produto if nome_produto else None, ambiente=ambiente)
            if resultados:
                df_resultados = pd.DataFrame(resultados)
                df_resultados["valor"] = df_resultados["valor"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                df_resultados = df_resultados.rename(columns={
                    "id": "ID",
                    "nome": "Nome",
                    "sabor": "Sabor",
                    "valor": "Valor",
                    "estoque": "Quantidade",
                    "data_criacao": "Data de Criação",
                    "validade" : "Validade"
                })
                st.write("📋 **Produtos encontrados:**")
                st.dataframe(df_resultados, use_container_width=True)
            else:
                st.warning(f"Nenhum produto encontrado no Estoque.")

    
    #Cadastrar Custo de Armazenamento
    elif menu == "Cadastrar Despesas Gerais":
        st.header("📋 Cadastrar Despesas Gerais")

        st.subheader("➕ Adicionar Despesas Gerais")
        nome_custo = st.text_input("Nome do item:")
        valor_custo = st.number_input("Valor (R$):", min_value=0.0, format="%.2f")
        quantidade_armezenamento = st.number_input("Quantidade:", min_value=0, step=1)
        categoria_armazenamento = st.text_input("Categoria:")

        if st.button("Cadastrar"):
            controlador.adicionar_custo_armazenamento(nome_custo, valor_custo,quantidade_armezenamento,categoria_armazenamento)
            st.success("✅ Item de Armezenamento cadastrado com sucesso!")

    #Cadastrar Eletrônico
    elif menu == "Cadastrar Eletrônico":
        st.header("⚡ Cadastrar Eletrônico")

        nome = st.text_input("Nome do eletrônico:")
        kw_por_dia = st.number_input("Consumo de Energia (kW/dia):", min_value=0.0, format="%.2f")
        quantidade = st.number_input("Quantidade:", min_value=1, step=1)
        ambiente = st.selectbox("Ambiente:", ["Estoque Aberto", "Estoque Fechado","Loja"])
        capacidade_total = st.number_input("Capacidade Total:", min_value=1, step=1)

        if st.button("Cadastrar"):
            controlador.cadastrar_eletronico(nome, kw_por_dia, quantidade,ambiente,capacidade_total)
            st.success("✅ Eletrônico cadastrado com sucesso!")

    #Estoque Fechado
    elif menu == "Estoque Fechado":
        st.header("🔒 Estoque Fechado - Visão Geral")

        estoque = controlador.obter_estoque()
        custo_armazenamento = controlador.obter_total_armazenamento()
        limite_critico = 10
        estoque_por_sabor_freezer = {}

        for item in controlador.listar_itens():
            chave = (item["sabor"], item["freezer_id"])
            estoque_por_sabor_freezer[chave] = estoque_por_sabor_freezer.get(chave, 0) + item["quantidade"]
        itens_criticos = [
            f"{sabor} - {quantidade} unidade(s) (Freezer {freezer_id})"
            for (sabor, freezer_id), quantidade in estoque_por_sabor_freezer.items()
            if quantidade <= limite_critico
        ]
        if itens_criticos:
            st.warning("⚠️ Atenção! Os seguintes produtos estão com estoque crítico em seus respectivos freezers:\n\n" + "\n".join(itens_criticos))
        
        hoje = datetime.today().date()
        limite_validade = hoje + timedelta(days=10)
        produtos_promocao = []

        for item in controlador.listar_itens():
            validade = item.get("validade")

            if validade and isinstance(validade, str):
                validade = datetime.strptime(validade, "%d/%m/%Y").date()

            if validade and validade <= limite_validade:  
                preco_original = item["valor_venda"]
                preco_promocional = round(preco_original * 0.7, 2)
                produtos_promocao.append(f"🔔 {item['nome']} ({item['sabor']}) - Validade: {validade.strftime('%d/%m/%Y')} "
                                        f"➡️ Sugestão de Promoção: **R$ {preco_promocional:.2f}** (de R$ {preco_original:.2f})")

        if produtos_promocao:
            st.warning("⚠️ **Atenção! Produtos próximos da validade:**\n\n" + "\n".join(produtos_promocao))

        st.markdown("---")
        preco_kwh = st.number_input("💡 Preço do kWh (R$):", min_value=0.0, value=0.90, format="%.2f")
        ambiente = "Estoque Fechado"  
        consumo_energia = controlador.obter_consumo_energia(preco_kwh, ambiente)
        freezers = controlador.listar_status_freezers(ambiente)
        estoque_ambiente = controlador.calcular_estoque_por_ambiente(ambiente)

        st.markdown("---")
        st.write(f"📦 {ambiente}: **{estoque_ambiente['quantidade']}** — 💰 Valor: **R$ {estoque_ambiente['valor']:.2f}**")
        st.write(f"⚡ Consumo de Energia Mês ({ambiente}): **{consumo_energia['consumo_mensal_kwh']} kWh**")
        st.write(f"⚡  Custo Total de Energia ({ambiente}): **R$ {consumo_energia['custo_total']:.2f}**")  
        st.write(f"📋 Custos com Armazenamento: **R$ {custo_armazenamento:.2f}**")

        st.markdown("---")
        st.subheader(f"🏆 Principais Produtos no Estoque")
        top_produtos = controlador.obter_top_produtos(ambiente=ambiente)
        for i, (nome, quantidade) in enumerate(top_produtos, start=1):
            st.write(f"**{i}. {nome}** - {quantidade} unidades")

        st.markdown("---")
        for freezer in freezers:
            st.subheader(f"🏠 {freezer['ambiente']} - {freezer['nome']}")
            st.write(f"📏 Capacidade Total: **{freezer['capacidade_total']}** picolés")
            st.write(f"📦 Ocupado: **{freezer['ocupado']}** picolés")
            st.write(f"⬜ Disponível: **{freezer['disponivel']}** picolés")
            st.progress(freezer['percentual_ocupado'] / 100) 
            st.write(f"📊 **{freezer['percentual_ocupado']}%** ocupado")

        st.markdown("---")
        st.subheader(f"🔍 Buscar Produto no Estoque")
        nome_produto = st.text_input(f"Digite o nome do produto no Estoque")

        if st.button("Buscar") or nome_produto == "":
            resultados = controlador.buscar_produto(nome_produto if nome_produto else None, ambiente=ambiente)
            if resultados:
                df_resultados = pd.DataFrame(resultados)
                df_resultados["valor"] = df_resultados["valor"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                df_resultados = df_resultados.rename(columns={
                    "id": "ID",
                    "nome": "Nome",
                    "sabor": "Sabor",
                    "valor": "Valor",
                    "estoque": "Quantidade",
                    "data_criacao": "Data de Criação",
                    "validade" : "Validade"
                })
                st.write("📋 **Produtos encontrados:**")
                st.dataframe(df_resultados, use_container_width=True)
            else:
                st.warning(f"Nenhum produto encontrado no Estoque.")
    
    elif menu == "Transferencia de Produtos":
        st.subheader("📦 Transferencia de Produtos")

        sabores = {item["sabor"] for item in controlador.listar_itens()}
        sabor = st.selectbox("Escolha o sabor:", list(sabores))

        freezers_disponiveis = controlador.banco.listar_status_freezers("Estoque Aberto") + controlador.banco.listar_status_freezers("Estoque Fechado")
        quantidades_por_freezer = controlador.banco.obter_quantidade_por_sabor()

        freezers_info = {
            freezer["id"]: {
                "nome": f"Freezer {freezer['id']} - {freezer['ambiente']}",
                "capacidade_total": freezer["capacidade_total"],
                "ocupado": freezer["ocupado"],
                "disponivel": freezer["disponivel"],
                "quantidade_sabor": quantidades_por_freezer.get(freezer["id"], {}).get(sabor, 0)  # Agora 'sabor' está definido!
            }
            for freezer in freezers_disponiveis
        }

        freezers_com_sabor = {
            f_id: f for f_id, f in freezers_info.items()
            if quantidades_por_freezer.get(f_id, {}).get(sabor, 0) > 0
        }

        if not freezers_com_sabor:
            st.warning(f"⚠️ Nenhum freezer possui picolés do sabor '{sabor}' disponíveis para movimentação.")
        else:
            freezer_origem = st.selectbox(
                "Selecione o Freezer de Origem:",
                list(freezers_com_sabor.keys()),
                format_func=lambda x: f"{freezers_com_sabor[x]['nome']} "
                                    f"(Ocupado: {freezers_com_sabor[x]['ocupado']} | "
                                    f"{quantidades_por_freezer[x].get(sabor, 0)} do sabor)"
            )

            freezers_destino_disponiveis = {
                f_id: f for f_id, f in freezers_info.items()
                if f_id != freezer_origem and f["disponivel"] > 0
            }

            if not freezers_destino_disponiveis:
                st.warning("⚠️ Nenhum freezer tem espaço disponível para receber os picolés.")
            else:
                freezer_destino = st.selectbox(
                    "Selecione o Freezer de Destino:",
                    list(freezers_destino_disponiveis.keys()),
                    format_func=lambda x: f"{freezers_destino_disponiveis[x]['nome']} "
                                        f"(Disponível: {freezers_destino_disponiveis[x]['disponivel']})"
                )

                quantidade_origem = quantidades_por_freezer.get(freezer_origem, {}).get(sabor, 0)
                quantidade_destino = freezers_destino_disponiveis[freezer_destino]["disponivel"]
                quantidade_maxima = min(quantidade_origem, quantidade_destino)

                if quantidade_maxima > 0:
                    quantidade = st.number_input("Quantidade a ser movida:", min_value=1, max_value=quantidade_maxima, step=1)

                    if st.button("Mover"):
                        sucesso, mensagem = controlador.mover_picole(sabor, freezer_origem, freezer_destino, quantidade)
                        if sucesso:
                            st.success(mensagem)
                        else:
                            st.error(mensagem)
                else:
                    st.warning("⚠️ Não há picolés suficientes para mover ou o freezer de destino está cheio.")
        
    elif menu == "Financeiro":
        st.subheader("💰 Lançar Receita ou Despesa")

        tipo = st.selectbox("Tipo de lançamento:", ["Receita", "Despesa"])
        categoria = st.text_input("Categoria:")
        descricao = st.text_input("Descrição:")
        valor = st.number_input("Valor:", min_value=0.0, step=0.01)
        data = st.date_input("Data do lançamento:", value=datetime.today())
        operador = st.text_input("👤 Operador Responsável:", value="admin")


        if st.button("Lançar"):
            sucesso = controlador.lancar_financeiro(tipo,categoria,descricao,valor,data,operador)
            if sucesso:
                st.success("✅ Lançamento realizado com sucesso!")
            else:
                st.error("❌ Erro ao lançar no financeiro.")


        st.divider()
        st.subheader("📋 Lançamentos Recentes")

        data_inicio = st.date_input("Data Inicial:", value=datetime.today().replace(day=1), key="data_inicio")
        data_fim = st.date_input("Data Final:", value=datetime.today(), key="data_fim")

        if data_inicio > data_fim:
            st.warning("⚠️ A data inicial não pode ser maior que a final.")
            return

        resultados = controlador.listar_lancamentos(data_inicio, data_fim)

        receitas = sum(l["valor"] for l in resultados if l["tipo"] == "Receita")
        despesas = sum(l["valor"] for l in resultados if l["tipo"] == "Despesa")
        saldo = receitas - despesas

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Total de Receitas", f"R$ {receitas:.2f}")
        col2.metric("📉 Total de Despesas", f"R$ {despesas:.2f}")
        col3.metric("💼 Saldo Líquido", f"R$ {saldo:.2f}", delta_color="normal" if saldo >= 0 else "inverse")

        
        st.divider()
        st.subheader("📂 Filtros e Tabela Completa de Lançamentos")

        tipos_disponiveis = list(set(l["tipo"] for l in resultados))
        categorias_disponiveis = list(set(l["categoria"] for l in resultados))
        operadores_disponiveis = list(set(l["operador"] for l in resultados))

        tipo_filtro = st.multiselect("Filtrar por Tipo:", tipos_disponiveis, default=tipos_disponiveis)
        categoria_filtro = st.multiselect("Filtrar por Categoria:", categorias_disponiveis, default=categorias_disponiveis)
        operador_filtro = st.multiselect("Filtrar por Operador:", operadores_disponiveis, default=operadores_disponiveis)

        filtrados = [
            l for l in resultados
            if l["tipo"] in tipo_filtro and l["categoria"] in categoria_filtro and l["operador"] in operador_filtro
        ]

        # Cria DataFrame e exibe
        df_filtrado = pd.DataFrame(filtrados)
        if not df_filtrado.empty:
            df_filtrado["valor"] = df_filtrado["valor"].map(lambda x: f"R$ {x:.2f}")
            st.dataframe(df_filtrado.rename(columns={
                "data": "Data",
                "tipo": "Tipo",
                "categoria": "Categoria",
                "descricao": "Descrição",
                "valor": "Valor",
                "operador": "Operador"

            }), use_container_width=True)
        else:
            st.info("⚠️ Nenhum lançamento encontrado com os filtros aplicados.")
        
        st.divider()
        st.subheader("📊 Gráfico de Receita vs Despesa por Data")

        df = pd.DataFrame(resultados)
        if not df.empty:
            df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")  # aplica o formato correto

            resumo = df.groupby(["data", "tipo"])["valor"].sum().reset_index()
            pivotado = resumo.pivot(index="data", columns="tipo", values="valor").fillna(0)

            st.line_chart(pivotado)
        else:
            st.info("Sem dados suficientes para gerar o gráfico.")
        
        st.divider()

        with st.expander("📄 Ver todos os lançamentos detalhados"):
            for lancamento in resultados:
                col1, col2 = st.columns([6, 1])
                with col1:
                    st.markdown(
                        f"**{lancamento['data']} - {lancamento['tipo']} - {lancamento['categoria']}**"
                    )
                    st.caption(f"{lancamento['descricao']} | R$ {lancamento['valor']:.2f} | 👤 {lancamento['operador']}")
                with col2:
                    if st.button("🗑️", key=f"del_{lancamento['id']}"):
                        controlador.excluir_lancamento_financeiro(lancamento['id'])
                        st.rerun()
    
    elif menu == "PDV (Venda)":
        st.subheader("🛒 Ponto de Venda (PDV)")

        if "carrinho" not in st.session_state:
            st.session_state.carrinho = []
        if "cupom_aplicado" not in st.session_state:
            st.session_state.cupom_aplicado = None

        with st.form(key="form_venda"):
            col1, col2 = st.columns([3, 1])
            with col1:
                codigo = st.text_input("📦 Código de Barras")
            with col2:
                quantidade = st.number_input("Qtd", min_value=1, value=1)

            operador = st.text_input("👤 Operador", value="Operador 1")

            submitted = st.form_submit_button("Adicionar ao Carrinho")

            if submitted:
                if not codigo:
                    st.warning("⚠️ Código de barras não informado.")
                else:
                    item = controlador.banco.buscar_item_por_codigo(codigo)
                    if item:
                        if item["quantidade"] < quantidade:
                            st.error(f"❌ Apenas {item['quantidade']} unidade(s) disponíveis em estoque.")
                        else:
                            item["vendendo"] = quantidade
                            st.session_state.carrinho.append(item)
                            st.success(f"✅ Produto '{item['nome']} - {item['sabor']}' adicionado ao carrinho.")
                    else:
                        # Se não achou pelo código, permite selecionar manualmente
                        todos = controlador.listar_itens()
                        lista_produtos = [f"{i['nome']} - {i['sabor']} | Estoque: {i['quantidade']}" for i in todos if i['quantidade'] > 0]
                        escolhido = st.selectbox("🔎 Produto não encontrado. Selecione manualmente:", lista_produtos)
                        if escolhido:
                            i = todos[lista_produtos.index(escolhido)]
                            if i["quantidade"] < quantidade:
                                st.error(f"❌ Apenas {i['quantidade']} unidade(s) disponíveis.")
                            else:
                                i["vendendo"] = quantidade
                                st.session_state.carrinho.append(i)
                                st.success(f"✅ Produto '{i['nome']} - {i['sabor']}' adicionado ao carrinho.")

        if st.session_state.carrinho:
            st.divider()
            st.subheader("🛍️ Carrinho de Compras")

            total = 0
            for idx, item in enumerate(st.session_state.carrinho):
                col1, col2, col3, col4, col5 = st.columns([4, 2, 2, 2, 1])
                with col1:
                    st.write(f"**{item['nome']} - {item['sabor']}**")
                with col2:
                    st.write(f"R$ {item['valor_venda']:.2f}")
                with col3:
                    st.write(f"Qtd. vendida: {item['vendendo']}")
                with col4:
                    st.write(f"Estoque: {item['quantidade']}")
                with col5:
                    if st.button("❌", key=f"del_{idx}"):
                        st.session_state.carrinho.pop(idx)
                        st.rerun()
                total += item["valor_venda"] * item["vendendo"]

            st.markdown(f"**💵 Subtotal:** R$ {total:.2f}")

            # Cupom
            with st.form("form_cupom"):
                cupom_input = st.text_input("🎟️ Cupom de Desconto")
                aplicar = st.form_submit_button("Aplicar Cupom")
                if aplicar and cupom_input:
                    sucesso, mensagem, valor_desconto = controlador.banco.aplicar_cupom(cupom_input, total)
                    if valor_desconto > 0:
                        st.session_state.cupom_aplicado = {"codigo": cupom_input, "valor": valor_desconto}
                        st.success(f"✅ Cupom '{cupom_input}' aplicado! Desconto de R$ {valor_desconto:.2f}")
                    else:
                        st.error("❌ Cupom inválido, expirado, esgotado ou não aplicável.")
            
            valor_desconto = 0.0 

            if "cupom_input" in st.session_state and st.session_state.cupom_input_aplicado:
                sucesso, mensagem, valor_desconto = controlador.banco.aplicar_cupom(
                    st.session_state.cupom_input, total
                )
                if sucesso:
                    st.success(mensagem)
                else:
                    st.warning(mensagem)
                    valor_desconto = 0.0

            desconto = st.session_state.cupom_aplicado["valor"] if st.session_state.cupom_aplicado else 0
            total_final = total - valor_desconto

            forma_pagamento = st.selectbox("💳 Forma de Pagamento", ["Dinheiro", "Cartão", "Pix", "Outros"])

            st.markdown(f"**🧾 Total com Desconto:** R$ {total_final:.2f}")

            if st.button("Finalizar Venda"):
                sucesso = True
                descricao_itens = []
                for item in st.session_state.carrinho:
                    for _ in range(item["vendendo"]):
                        ok, msg = controlador.banco.baixar_estoque(item["id"])
                        if not ok:
                            st.error(msg)
                            sucesso = False
                            break
                    if not sucesso:
                        break
                    descricao_itens.append(f"{item['vendendo']}x {item['nome']} - {item['sabor']}")

                if sucesso:
                    descricao_venda = f"{operador} | " + " | ".join(descricao_itens)
                    data_venda = datetime.now().date()

                    categoria = f"Venda - {forma_pagamento}"
                    controlador.banco.lancar_financeiro(
                        tipo="Receita",
                        categoria=categoria,
                        descricao=descricao_venda,
                        valor=total_final,
                        data=data_venda,
                        operador=operador
                    )

                    st.success("✅ Venda finalizada com sucesso!")

                    with st.expander("🧾 Recibo da Venda", expanded=True):
                        recibo = f"Recibo - {data_venda.strftime('%d/%m/%Y %H:%M:%S')}\nOperador: {operador}\n\n"
                        for i in st.session_state.carrinho:
                            linha = f"{i['vendendo']}x {i['nome']} - {i['sabor']} @ R$ {i['valor_venda']:.2f}"
                            st.markdown(f"- {linha}")
                            recibo += linha + "\n"
                        recibo += f"\nSubtotal: R$ {total:.2f}\n"
                        if desconto > 0:
                            recibo += f"Desconto ({st.session_state.cupom_aplicado['codigo']}): -R$ {desconto:.2f}\n"
                        recibo += f"Total Final: R$ {total_final:.2f}\nForma de Pagamento: {forma_pagamento}"

                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Arial", size=12)
                        for linha in recibo.strip().split("\n"):
                            pdf.cell(200, 10, txt=linha, ln=True)
                        nome_arquivo = f"recibo_{data_venda.strftime('%Y%m%d_%H%M%S')}.pdf"
                        caminho = f"recibos/{nome_arquivo}"
                        os.makedirs("recibos", exist_ok=True)
                        pdf.output(caminho)

                        with open(caminho, "rb") as f:
                            st.download_button("📥 Baixar Recibo em PDF", f, file_name=nome_arquivo)

                    st.session_state.carrinho.clear()
                    st.session_state.cupom_aplicado = None
        else:
            st.info("🧺 O carrinho está vazio.")
        
    elif menu == "Cupons":
        st.subheader("🎟️ Gerenciar Cupons de Desconto")

        with st.form("form_cupom"):
            codigo = st.text_input("Código do Cupom")
            valor = st.number_input("Percentual de Desconto", min_value=0.01, step=0.01)
            validade = st.date_input("Validade do Cupom")
            limite_uso = st.number_input("Limite de uso", min_value=1, step=1)

            if st.form_submit_button("Cadastrar Cupom"):
                sucesso, mensagem = controlador.cadastrar_cupom(codigo, valor, validade, limite_uso)
                if sucesso:
                    st.success(mensagem)
                else:
                    st.error(mensagem)

        st.divider()
        st.subheader("📋 Cupons Cadastrados")

        cupons = controlador.listar_cupons()
        if not cupons:
            st.info("Nenhum cupom cadastrado.")
        else:
            for cupom in cupons:
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"**{cupom['codigo']}** | "
                        f"Desconto: {cupom['percentual_desconto']}% | "
                        f"Validade: {cupom['validade']} | "
                        f"Usos restantes: {cupom['usos_restantes']}/{cupom['limite_uso']}")
                with col2:
                    if st.button("🗑️", key=f"del_{cupom['codigo']}"):
                        controlador.excluir_cupom(cupom['codigo'])
                        st.success(f"Cupom {cupom['codigo']} excluído com sucesso!")
                        st.rerun()

        

if __name__ == "__main__":
    interface()