import streamlit as st
import pandas as pd
from utils import (
    fmt_br, render_metric_card, render_sidebar,
    DEFAULT_PAVIMENTO, TIPOS_PAVIMENTO, save_project
)

st.set_page_config(page_title="Dados do Projeto", layout="wide")

if "projeto_info" not in st.session_state:
    st.error("Nenhum projeto carregado. Por favor, selecione um projeto na página inicial.")
    if st.button("Voltar para a seleção de projetos"):
        st.switch_page("Início.py")
    st.stop()
    
# Dialog de confirmação de exclusão
@st.dialog("Confirmar Exclusão")
def confirm_delete_dialog():
    index_to_delete = st.session_state.deleting_pav_index
    if index_to_delete is not None:
        pav_name = st.session_state.pavimentos[index_to_delete]['nome']
        st.write(f"Tem certeza que deseja excluir o pavimento **{pav_name}**?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sim, Excluir", use_container_width=True, type="primary"):
                del st.session_state.pavimentos[index_to_delete]
                st.session_state.deleting_pav_index = None
                st.success(f"Pavimento '{pav_name}' excluído com sucesso!")
                st.rerun()
        with col2:
            if st.button("Cancelar", use_container_width=True):
                st.session_state.deleting_pav_index = None
                st.rerun()

# Passamos uma chave única para a sidebar para evitar erros de chave duplicada
render_sidebar(form_key="sidebar_dados_projeto")

info = st.session_state.projeto_info
st.title("📝 Dados do Projeto")
st.subheader("Configuração e Detalhamento do Empreendimento")

if 'pavimentos' not in st.session_state:
    st.session_state.pavimentos = [p.copy() for p in info.get('pavimentos', [DEFAULT_PAVIMENTO.copy()])]
if 'deleting_pav_index' not in st.session_state:
    st.session_state.deleting_pav_index = None

# --- Exibição e Edição dos dados gerais ---
with st.expander("📝 Dados Gerais do Projeto", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    cores = ["#31708f", "#3c763d", "#8a6d3b", "#a94442"]
    c1.markdown(render_metric_card("Nome", info["nome"], cores[0]), unsafe_allow_html=True)
    c2.markdown(render_metric_card("Área Terreno", f"{fmt_br(info['area_terreno'])} m²", cores[1]), unsafe_allow_html=True)
    c3.markdown(render_metric_card("Área Privativa", f"{fmt_br(info['area_privativa'])} m²", cores[2]), unsafe_allow_html=True)
    c4.markdown(render_metric_card("Nº Unidades", str(info["num_unidades"]), cores[3]), unsafe_allow_html=True)

# --- Detalhamento dos Pavimentos ---
with st.expander("🏢 Dados dos Pavimentos", expanded=True):
    b1, _ = st.columns([0.2, 0.8])
    if b1.button("➕ Adicionar Pavimento"):
        st.session_state.pavimentos.append(DEFAULT_PAVIMENTO.copy())
        st.rerun()

    col_widths = [3, 3, 1, 1.5, 1.5, 1.5, 1.5, 0.8, 0.8]  # Corrigido: 9 valores para 9 colunas
    headers = ["Nome", "Tipo", "Rep.", "Coef.", "Área (m²)", "Área Eq. Total", "Área Constr.", "Considerar A.C?", "Ação"]
    header_cols = st.columns(col_widths)
    for hc, title in zip(header_cols, headers):
        hc.markdown(f'**{title}**')

    for i, pav in enumerate(st.session_state.pavimentos):
        cols = st.columns(col_widths)
        pav['nome'] = cols[0].text_input("nome", pav['nome'], key=f"nome_{i}", label_visibility="collapsed")
        pav['tipo'] = cols[1].selectbox("tipo", list(TIPOS_PAVIMENTO.keys()), list(TIPOS_PAVIMENTO.keys()).index(pav.get('tipo', next(iter(TIPOS_PAVIMENTO)))), key=f"tipo_{i}", label_visibility="collapsed")
        pav['rep'] = cols[2].number_input("rep", min_value=1, value=pav['rep'], step=1, key=f"rep_{i}", label_visibility="collapsed")
        
        # Lógica para o campo de texto com validação e dica
        min_c, max_c = TIPOS_PAVIMENTO[pav['tipo']]
        help_text = f"Intervalo: {min_c:.2f} - {max_c:.2f}"
        
        # Correção do erro: Garante que o valor do coeficiente esteja dentro do intervalo válido
        if float(pav.get('coef', min_c)) > max_c:
            pav['coef'] = max_c
        elif float(pav.get('coef', min_c)) < min_c:
            pav['coef'] = min_c

        if min_c == max_c:
            cols[3].markdown(f"<div style='text-align:center; padding-top: 8px;'>{pav['coef']:.2f}</div>", unsafe_allow_html=True)
        else:
            pav['coef'] = cols[3].number_input("coef", min_value=min_c, max_value=max_c, value=float(pav.get('coef', min_c)), step=0.01, format="%.2f", key=f"coef_{i}", label_visibility="collapsed", help=help_text)

        pav['area'] = cols[4].number_input("area", min_value=0.0, value=float(pav['area']), step=10.0, format="%.2f", key=f"area_{i}", label_visibility="collapsed")
        pav['constr'] = cols[7].selectbox("incluir", ["Sim", "Não"], 0 if pav.get('constr', True) else 1, key=f"constr_{i}", label_visibility="collapsed") == "Sim"
        total_i, area_eq_i = pav['area'] * pav['rep'], (pav['area'] * pav['rep']) * pav['coef']
        cols[5].markdown(f"<div style='text-align:center; padding-top: 8px;'>{fmt_br(area_eq_i)}</div>", unsafe_allow_html=True)
        cols[6].markdown(f"<div style='text-align:center; padding-top: 8px;'>{fmt_br(total_i)}</div>", unsafe_allow_html=True)

        if cols[8].button("🗑️", key=f"del_{i}", use_container_width=True):
            st.session_state.deleting_pav_index = i
            st.rerun()

# Lógica de confirmação de exclusão
if st.session_state.deleting_pav_index is not None:
    confirm_delete_dialog()

# Atualiza a sessão
info['pavimentos'] = st.session_state.pavimentos

if st.button("Salvar Dados do Projeto", type="primary"):
    save_project(info)
    st.success("Dados do projeto salvos com sucesso!")
