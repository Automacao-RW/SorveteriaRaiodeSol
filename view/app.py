import streamlit as st
import os 
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from controller.controlador_item import ControladorItem

# Instanciando a Classe do Controlador
controlador = ControladorItem()

def interface():
    st.title("🍦 Sorveteria Raio de Sol")
    menu = st.sidebar.selectbox("Escolha uma opção:", ["Cadastrar Item"])

    # Cadastrar Sorvete ou Item
    if menu == "Cadastrar Item":
        st.header("Cadastrar Novo Item")

        nome = st.text_input("Nome do sorvete:")
        sabor = st.text_input("Sabor:")
        valor = st.number_input("Valor (R$):", min_value=0.0, format="%.2f")
        quantidade = st.number_input("Quantidade:", min_value=0, step=1)

        if st.button("Cadastrar"):
            controlador.cadastrar_item(nome, sabor, valor, quantidade)
            st.success("✅ Item cadastrado com sucesso!")

if __name__ == "__main__":
    interface()
