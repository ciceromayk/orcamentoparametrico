# pages/4_Custos_Indiretos.py
import streamlit as st
import pandas as pd
from utils import (
    fmt_br, render_metric_card, render_sidebar, DEFAULT_CUSTOS_INDIRETOS_OBRA,
    DEFAULT_CUSTOS_INDIRETOS, ETAPAS_OBRA, DEFAULT_PAVIMENTO,
    list_projects, save_project, load_project, delete_project,
    JSON_PATH, HISTORICO_DIRETO_PATH, HISTORICO_INDIRETO_PATH,
    load_json, save_to_historico, init_session_state_vars
)

st.set_page_config(page_title="Custos Indiretos", layout="wide", page_icon="💸")

# Injeta CSS para a tabela
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
    /* Estilo para centralizar e reduzir a largura do text_input */
    .stTextInput > div > div {
        display: flex;
        justify-content: center;
    }
    .stTextInput > div > div > input {
        width: 100px; /* Largura ajustada para 100px */
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# Função de cartão de métrica profissional com design moderno
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

# Inicializa as variáveis de estado
init_session_state_vars(st.session_state.projeto_info)

# Passamos uma chave única para a sidebar para evitar erros de chave duplicada
render_sidebar(form_key="sidebar_custos_indiretos")

info = st.session_state.projeto_info
st.title("💸 Custos Indiretos")
st.subheader("Análise e Detalhamento de Custos Indiretos do Projeto")


# Cálculos Preliminares
custos_config = info.get('custos_config', {})
preco_medio_venda_m2 = custos_config.get('preco_medio_venda_m2', 10000.0)
vgv_total = info.get('area_privativa', 0) * preco_medio_venda_m2

# Recalcula o custo indireto total para exibir no card
custo_indireto_calculado = 0
for item, values in st.session_state.custos_indiretos_percentuais.items():
    percentual = values.get('percentual', 0)
    custo_calculado_item = vgv_total * (float(percentual) / 100)
    custo_indireto_calculado += custo_calculado_item
    
with st.container(border=True):
    card_cols = st.columns(3)
    
    card_cols[0].markdown(render_metric_card(
        "VGV Total",
        f"R$ {fmt_br(vgv_total)}",
        "#007bff"
    ), unsafe_allow_html=True)

    card_cols[1].markdown(render_metric_card(
        "Custo Indireto Total",
        f"R$ {fmt_br(custo_indireto_calculado)}",
        "#28a745"
    ), unsafe_allow_html=True)

    card_cols[2].markdown(render_metric_card(
        "% do Custo Indireto",
        f"{((custo_indireto_calculado / vgv_total) * 100):.2f}%" if vgv_total > 0 else "0.00%",
        "#ff7f00"
    ), unsafe_allow_html=True)


# Bloco principal com a nova tabela AgGrid e Gráficos
with st.expander("Detalhamento de Custos Indiretos", expanded=True):

    st.write("### Ajuste os Percentuais")

    # Definindo as colunas da tabela manual
    col_widths = [4, 2, 2]
    headers = ["Item", "Percentual (%)", "Custo (R$)"]
    header_cols = st.columns(col_widths)
    for hc, title in zip(header_cols, headers):
        hc.markdown(f'<p style="text-align:center; font-size:16px;"><b>{title}</b></p>', unsafe_allow_html=True)
    
    for item, (min_val, default_val, max_val) in DEFAULT_CUSTOS_INDIRETOS.items():
        cols = st.columns(col_widths)
        
        # Coluna Item (não editável)
        cols[0].markdown(f"<div style='padding-top: 8px;'>{item}</div>", unsafe_allow_html=True)
        
        # Coluna Custo Mensal (editável)
        current_percent = st.session_state.custos_indiretos_percentuais.get(item, {}).get('percentual', default_val)
        
        novo_percentual_str = cols[1].text_input(
            "Percentual (%)",
            value=f"{current_percent:.2f}".replace('.',','),
            key=f"custo_percentual_{item}",
            label_visibility="collapsed"
        )
        
        novo_percentual_float = current_percent
        # Adicionando try-except para validação mais robusta
        try:
            # Substitui a vírgula por ponto para a conversão e remove espaços
            temp_value = novo_percentual_str.strip().replace(',', '.')
            if temp_value:
                novo_percentual_float = float(temp_value)
            else:
                novo_percentual_float = 0.0 # Define 0 se o campo estiver vazio
        except ValueError:
            st.error(f"Valor inválido para '{item}'. Por favor, insira um número.")
            novo_percentual_float = current_percent # Mantém o valor original
            
        # Valida se o novo percentual está dentro do intervalo
        if not (min_val <= novo_percentual_float <= max_val):
            st.warning(f"O percentual para '{item}' deve estar entre {min_val:.2f}% e {max_val:.2f}%.")
            # Força o valor a ficar dentro do intervalo se for editado
            novo_percentual_float = max(min_val, min(novo_percentual_float, max_val))
            
        # Coluna Custo Total (calculado)
        custo_calculado_item = vgv_total * (novo_percentual_float / 100)
        cols[2].markdown(f"<div style='text-align:center; padding-top: 8px;'>R$ {fmt_br(custo_calculado_item)}</div>", unsafe_allow_html=True)
        
        if novo_percentual_float != current_percent:
            st.session_state.custos_indiretos_percentuais[item]['percentual'] = novo_percentual_float
            st.rerun()

    # Atualiza o estado da sessão
    info['custos_indiretos_percentuais'] = st.session_state.custos_indiretos_percentuais
