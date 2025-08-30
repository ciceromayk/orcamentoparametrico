import streamlit as st
import pandas as pd
from utils import (
    fmt_br, render_metric_card, render_sidebar,
    DEFAULT_PAVIMENTO, TIPOS_PAVIMENTO, save_project,
    init_session_state_vars, calcular_areas_e_custos
)

st.set_page_config(page_title="Dados do Projeto", layout="wide")

# CSS para diminuir as fontes da tabela e adicionar barra de rolagem
st.markdown("""
<style>
    /* Diminui a fonte dos cabeçalhos das colunas */
    [data-testid="column"] .st-markdown > p {
        font-size: 14px;
        text-align: center;
    }
    /* Diminui a fonte dos inputs e selectboxes */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div {
        font-size: 14px;
    }
    /* Diminui a fonte do checkbox */
    .stCheckbox > label {
        font-size: 14px;
    }
    /* Adiciona barra de rolagem vertical para a seção de pavimentos */
    .pavimentos-scrollable-container {
        max-height: 400px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

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

# Inicializa as variáveis de estado
init_session_state_vars(st.session_state.projeto_info)

# Passamos uma chave única para a sidebar para evitar erros de chave duplicada
render_sidebar(form_key="sidebar_dados_projeto")

info = st.session_state.projeto_info
st.title("📝 Dados do Projeto")
st.subheader("Configuração e Detalhamento do Empreendimento")

# --- Exibição e Edição dos dados gerais ---
with st.expander("📝 Dados Gerais do Projeto", expanded=True):
    # Chamando a função centralizada de cálculo
    area_construida_total, area_equivalente_total, _, _ = calcular_areas_e_custos(st.session_state.pavimentos, info.get('custos_config', {}))
    
    c1, c2, c3, c4, c5 = st.columns(5)
    cores = ["#31708f", "#3c763d", "#8a6d3b", "#a94442", "#5c5c5c"]
    c1.markdown(render_metric_card("Nome", info["nome"], cores[0]), unsafe_allow_html=True)
    c2.markdown(render_metric_card("Área Terreno", f"{fmt_br(info['area_terreno'])} m²", cores[1]), unsafe_allow_html=True)
    c3.markdown(render_metric_card("Área Privativa", f"{fmt_br(info['area_privativa'])} m²", cores[2]), unsafe_allow_html=True)
    c4.markdown(render_metric_card("Área Constr.", f"{fmt_br(area_construida_total)} m²", cores[3]), unsafe_allow_html=True)
    c5.markdown(render_metric_card("Área Eq.", f"{fmt_br(area_equivalente_total)} m²", cores[4]), unsafe_allow_html=True)

# --- Detalhamento dos Pavimentos ---
with st.expander("🏢 Dados dos Pavimentos", expanded=True):
    b1, _ = st.columns([0.2, 0.8])
    if b1.button("➕ Adicionar Pavimento"):
        st.session_state.pavimentos.append(DEFAULT_PAVIMENTO.copy())
        st.rerun()

    # Larguras das colunas ajustadas
    col_widths = [2.5, 4, 1, 1, 1.5, 1.5, 1.5, 0.8, 0.8]
    headers = ["Nome", "Tipo", "Rep.", "Coef.", "Área (m²)", "Área Eq. Total", "Área Constr.", "A.C?", "Ação"]
    header_cols = st.columns(col_widths)
    for hc, title in zip(header_cols, headers):
        hc.markdown(f'<p style="text-align:center; font-size:14px;"><b>{title}</b></p>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="pavimentos-scrollable-container">', unsafe_allow_html=True)
        for i, pav in enumerate(st.session_state.pavimentos):
            cols = st.columns(col_widths)
            pav['nome'] = cols[0].text_input("nome", pav['nome'], key=f"nome_{i}", label_visibility="collapsed")
            pav['tipo'] = cols[1].selectbox("tipo", list(TIPOS_PAVIMENTO.keys()), list(TIPOS_PAVIMENTO.keys()).index(pav.get('tipo', next(iter(TIPOS_PAVIMENTO)))), key=f"tipo_{i}", label_visibility="collapsed")
            pav['rep'] = cols[2].number_input("rep", min_value=1, value=pav['rep'], step=1, key=f"rep_{i}", label_visibility="collapsed")
            
            min_c, max_c = TIPOS_PAVIMENTO[pav['tipo']]
            help_text = f"Intervalo: {min_c:.2f} - {max_c:.2f}"
            
            if float(pav.get('coef', min_c)) > max_c:
                pav['coef'] = max_c
            elif float(pav.get('coef', min_c)) < min_c:
                pav['coef'] = min_c

            if min_c == max_c:
                cols[3].markdown(f"<div style='text-align:center; padding-top: 8px;'>{pav['coef']:.2f}</div>", unsafe_allow_html=True)
            else:
                pav['coef'] = cols[3].number_input("coef", min_value=min_c, max_value=max_c, value=float(pav.get('coef', min_c)), step=0.01, format="%.2f", key=f"coef_{i}", label_visibility="collapsed", help=help_text)

            pav['area'] = cols[4].number_input("area", min_value=0.0, value=float(pav['area']), step=10.0, format="%.2f", key=f"area_{i}", label_visibility="collapsed")
            
            pav['constr'] = cols[7].checkbox(" ", value=pav.get('constr', True), key=f"constr_{i}", label_visibility="collapsed")
            
            total_i, area_eq_i = pav['area'] * pav['rep'], (pav['area'] * pav['rep']) * pav['coef']
            cols[5].markdown(f"<div style='text-align:center; padding-top: 8px;'>{fmt_br(area_eq_i)}</div>", unsafe_allow_html=True)
            cols[6].markdown(f"<div style='text-align:center; padding-top: 8px;'>{fmt_br(total_i)}</div>", unsafe_allow_html=True)

            if cols[8].button("🗑️", key=f"del_{i}", use_container_width=True):
                st.session_state.deleting_pav_index = i
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


    if st.session_state.deleting_pav_index is not None:
        confirm_delete_dialog()

# --- Nova Tabela de Dados de Unidades ---
with st.expander("📝 Dados de Unidades", expanded=True):
    st.write("### Detalhamento por Tipo de Unidade")
    
    # Agrupar os dados por tipo de unidade
    unidades_df = pd.DataFrame(st.session_state.pavimentos)
    
    # Remove colunas que não são relevantes para a tabela de unidades
    unidades_df = unidades_df[unidades_df['tipo'] == 'Área Privativa (Autônoma)']
    
    # Agrupar e somar os valores
    unidades_agrupadas = unidades_df.groupby('nome').agg(
        quantidade=('rep', 'sum'),
        area_privativa=('area', 'first') # Pega a primeira área, pois são iguais por nome de unidade
    ).reset_index()

    # Calcular a área privativa total
    unidades_agrupadas['area_privativa_total'] = unidades_agrupadas['quantidade'] * unidades_agrupadas['area_privativa']

    # Definir as colunas da tabela
    col_widths = [3, 1.5, 2, 2.5]
    headers = ["Tipo de Unidade", "Quantidade", "Área Privativa (m²)", "Área Privativa Total (m²)"]
    header_cols = st.columns(col_widths)
    for hc, title in zip(header_cols, headers):
        hc.markdown(f'<p style="text-align:center; font-size:14px;"><b>{title}</b></p>', unsafe_allow_html=True)

    # Exibir a tabela
    total_quantidade = 0
    total_area_privativa_total = 0
    if not unidades_agrupadas.empty:
        for index, row in unidades_agrupadas.iterrows():
            cols = st.columns(col_widths)
            cols[0].markdown(f"<div style='padding-top: 8px;'>{row['nome']}</div>", unsafe_allow_html=True)
            cols[1].markdown(f"<div style='text-align:center; padding-top: 8px;'>{row['quantidade']}</div>", unsafe_allow_html=True)
            cols[2].markdown(f"<div style='text-align:center; padding-top: 8px;'>{fmt_br(row['area_privativa'])}</div>", unsafe_allow_html=True)
            cols[3].markdown(f"<div style='text-align:center; padding-top: 8px;'>{fmt_br(row['area_privativa_total'])}</div>", unsafe_allow_html=True)
            total_quantidade += row['quantidade']
            total_area_privativa_total += row['area_privativa_total']

    # Linha de totais
    if not unidades_agrupadas.empty:
        st.markdown("---")
        total_cols = st.columns(col_widths)
        total_cols[0].markdown(f"<div style='font-weight: bold; padding-top: 8px;'>Total</div>", unsafe_allow_html=True)
        total_cols[1].markdown(f"<div style='font-weight: bold; text-align:center; padding-top: 8px;'>{total_quantidade}</div>", unsafe_allow_html=True)
        total_cols[2].empty() # Área privativa individual não tem total
        total_cols[3].markdown(f"<div style='font-weight: bold; text-align:center; padding-top: 8px;'>{fmt_br(total_area_privativa_total)}</div>", unsafe_allow_html=True)


info['pavimentos'] = st.session_state.pavimentos

if st.button("Salvar Dados do Projeto", type="primary"):
    save_project(info)
    st.success("Dados do projeto salvos com sucesso!")
