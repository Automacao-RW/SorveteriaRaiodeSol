import streamlit as st
import os 
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from controller.controlador_item import ControladorItem
import pandas as pd
from datetime import datetime, timedelta


# Configuração da página
st.set_page_config(page_title="App-Sorveteria-Raio-de-Sol")

# Instanciando a Classe do Controlador
controlador = ControladorItem()

def interface():
    st.title("🍦 Sorveteria Raio de Sol")
    menu = st.sidebar.selectbox("Escolha uma opção:", ["Cadastrar Sorvete","Cadastrar Despesas Gerais","Cadastrar Eletrônico","Estoque Aberto", "Estoque Fechado","Transferencia de Produtos"])

    #Cadastrar Item
    if menu == "Cadastrar Sorvete":
        st.header("Cadastrar Novo Sorvete")

        nome = st.text_input("Nome do sorvete:")
        sabor = st.text_input("Sabor:")
        valor_compra = st.number_input("Valor de Compra (R$):", min_value=0.0, step=0.01)
        valor_venda = st.number_input("Valor de Venda (R$):", min_value=0.0, step=0.01)
        quantidade = st.number_input("Quantidade:", min_value=0, step=1)
        validade = st.date_input("Data de Validade:")


        freezers = controlador.listar_status_freezers("Estoque Aberto") + controlador.listar_status_freezers("Estoque Fechado")
        freezer_options = {
            f"Freezer {f['id']} - {f['ambiente']} (Capacidade: {f['capacidade_total']} | Disponível: {f['disponivel']})": f["id"]
            for f in freezers
        }

        if freezer_options:
            freezer_selecionado = st.selectbox("Escolha o Freezer:", list(freezer_options.keys()))

            if st.button("Cadastrar"):
                freezer_id = freezer_options[freezer_selecionado]
                sucesso, mensagem = controlador.cadastrar_item(nome, sabor, valor_compra, valor_venda, quantidade, freezer_id,validade)
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


if __name__ == "__main__":
    interface()