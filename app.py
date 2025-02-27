import streamlit as st
from controller.controlador_item import ControladorItem

# Instanciando a Classe do Controlador e Interface do Programa
controlador = ControladorItem()
st.title("🍦 Sorveteria Raio de Sol")
menu = st.sidebar.selectbox("Escolha uma opção:", ["Cadastrar Item"])

#Cadastrar Sorvete ou Item
if menu == "Cadastrar Item":
    st.header("Cadastrar Novo Item")

    nome = st.text_input("Nome do sorvete:")
    sabor = st.text_input("Sabor:")
    valor = st.number_input("Valor (R$):", min_value=0.0, format="%.2f")
    quantidade = st.number_input("Quantidade:", min_value=0, step=1)

    if st.button("Cadastrar"):
        controlador.cadastrar_item(nome, sabor, valor, quantidade)
        st.success("✅ Item cadastrado com sucesso!")