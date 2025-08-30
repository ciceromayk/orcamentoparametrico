# pages/2_Administracao_da_Obra.py
import streamlit as st
import pandas as pd
from utils import (
    fmt_br, render_metric_card, render_sidebar, DEFAULT_CUSTOS_INDIRETOS_OBRA,
    DEFAULT_CUSTOS_INDIRETOS, ETAPAS_OBRA, DEFAULT_PAVIMENTO,
    list_projects, save_project, load_project, delete_project,
    JSON_PATH, HISTORICO_DIRETO_PATH, HISTORICO_INDIRETO_PATH,
    load_json, save_to_historico
)

st.set_page_config(page_title="Administração da Obra", layout="wide", page_icon="📝")

# Injeta CSS para aumentar o tamanho da fonte da tabela e adicionar barra de rolagem
st.markdown("""
<style>
    /* Aumenta a fonte dos cabeçalhos das colunas e centraliza */
    [data-testid="column"] .st-markdown > p {
        font-size: 14px;
        text-align: center;
    }
    /* Aumenta a fonte dos inputs e selectboxes */
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


# Funcao de cartão de métrica profissional com design moderno
def card_metric_pro(label, value, delta=None, icon_name="cash-coin", bg_color="linear-gradient(145deg, #f9f9f9, #ffffff)", text_color="#007bff"):
    st.markdown(f"""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <div style="
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 15px; /* Reduz o padding para diminuir a altura */
        text-align: center;
        background: {bg_color};
        box-shadow: 5px 5px 15px rgba(0,0,0,0.05);
        transition: transform 0.3s ease;
    "
    onmouseover="this.style.transform='scale(1.03)'"
    onmouseout="this.style.transform='scale(1)'"
    >
        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 5px;">
            <i class="bi bi-{icon_name}" style="font-size: 1.2em; margin-right: 8px; color: {text_color};"></i>
            <h3 style="margin: 0; color: #333; font-size: 1.0em;">{label}</h3>
        </div>
        <p style="font-size: 1.8em; font-weight: bold; margin: 0; color: {text_color};">{value}</p>
        {f'<p style="color: {"green" if delta and delta > 0 else "red"}; font-size: 0.8em;">{f"+{delta}%" if delta else ""}</p>' if delta is not None else ''}
    </div>
    """, unsafe_allow_html=True)


if "projeto_info" not in st.session_state:
    st.error("Nenhum projeto carregado. Por favor, selecione um projeto na página inicial.")
    if st.button("Voltar para a seleção de projetos"):
        st.switch_page("Início.py")
    st.stop()

render_sidebar(form_key="sidebar_administracao_obra")

info = st.session_state.projeto_info
st.title("📝 Administração da Obra")
st.subheader("Custos Mensais e Duração do Projeto")

if 'custos_indiretos_obra' not in st.session_state:
    st.session_state.custos_indiretos_obra = info.get('custos_indiretos_obra', {k: v for k, v in DEFAULT_CUSTOS_INDIRETOS_OBRA.items()})
if 'duracao_obra' not in st.session_state:
    st.session_state.duracao_obra = info.get('duracao_obra', 12)

# Colocando os cards no topo, alinhados horizontalmente
with st.container(border=True):
    total_mensal = sum(st.session_state.custos_indiretos_obra.values())
    custo_indireto_obra_total_recalculado = total_mensal * st.session_state.duracao_obra

    card_cols = st.columns(3)
    
    card_cols[0].markdown(render_metric_card(
        "Custo Mensal Total",
        f"R$ {fmt_br(total_mensal)}",
        "#007bff"
    ), unsafe_allow_html=True)

    card_cols[1].markdown(render_metric_card(
        "Duração da Obra (meses)",
        f"{st.session_state.duracao_obra}",
        "#28a745"
    ), unsafe_allow_html=True)

    card_cols[2].markdown(render_metric_card(
        "Custo Indireto de Obra Total",
        f"R$ {fmt_br(custo_indireto_obra_total_recalculado)}",
        "#ff7f00"
    ), unsafe_allow_html=True)


with st.expander("💸 Custos Indiretos de Obra (por Período)", expanded=True):
    st.session_state.duracao_obra = st.slider(
        "Duração da Obra (meses):",
        min_value=1,
        max_value=60,
        value=st.session_state.duracao_obra
    )

    st.write("### Ajuste os Custos Mensais")

    # Definindo as colunas da tabela manual
    col_widths = [4, 2, 2]
    headers = ["Item", "Custo Mensal (R$)", "Custo Total (R$)"]
    header_cols = st.columns(col_widths)
    for hc, title in zip(header_cols, headers):
        hc.markdown(f'<p style="text-align:center; font-size:16px;"><b>{title}</b></p>', unsafe_allow_html=True)
    
    # Adicionando barra de rolagem para a tabela
    with st.container(height=450, border=True):
        # Itera sobre os itens para criar as linhas
        for item, valor_mensal in st.session_state.custos_indiretos_obra.items():
            cols = st.columns(col_widths)
            
            # Coluna Item (não editável)
            cols[0].markdown(f"<div style='padding-top: 8px;'>{item}</div>", unsafe_allow_html=True)
            
            # Coluna Custo Mensal (editável)
            novo_valor_mensal = cols[1].number_input(
                "Custo Mensal (R$)",
                min_value=0.0,
                value=float(valor_mensal),
                step=100.0,
                format="%.2f",
                key=f"custo_mensal_{item}",
                label_visibility="collapsed"
            )
            
            # Coluna Custo Total (calculado)
            custo_total_item = novo_valor_mensal * st.session_state.duracao_obra
            cols[2].markdown(f"<div style='text-align:center; padding-top: 8px;'>R$ {fmt_br(custo_total_item)}</div>", unsafe_allow_html=True)
            
            # Atualiza o session_state se o valor foi alterado
            if novo_valor_mensal != valor_mensal:
                st.session_state.custos_indiretos_obra[item] = novo_valor_mensal
                st.rerun()

    # Salvando no estado da sessão
    info['custos_indiretos_obra'] = st.session_state.custos_indiretos_obra
    info['duracao_obra'] = st.session_state.duracao_obra
