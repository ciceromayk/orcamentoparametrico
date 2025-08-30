import streamlit as st
import pandas as pd
from utils import (
    fmt_br, render_metric_card, render_sidebar, DEFAULT_CUSTOS_INDIRETOS_OBRA,
    DEFAULT_CUSTOS_INDIRETOS,
    init_session_state_vars
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
    .main-container {
        display: flex;
        flex-direction: row;
        gap: 20px;
        padding: 20px;
    }
    .left-panel {
        flex: 2;
    }
    .right-panel {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 20px;
        padding-top: 50px; /* Alinha os cards com o topo da tabela */
    }
</style>
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

# Recalcula a área privativa total com base nos dados das unidades
total_area_privativa = sum(u['area_privativa_total'] for u in info.get('unidades', []) if 'area_privativa_total' in u)
vgv_total = total_area_privativa * preco_medio_venda_m2

# Recalcula o custo indireto total para exibir no card
custo_indireto_calculado = 0
for item, values in st.session_state.custos_indiretos_percentuais.items():
    percentual = values.get('percentual', 0)
    custo_calculado_item = vgv_total * (float(percentual) / 100)
    custo_indireto_calculado += custo_calculado_item

# Bloco com os cards de métricas
with st.container(border=True):
    card_cols = st.columns(3)
    card_cols[0].markdown(render_metric_card("VGV Total", f"R$ {fmt_br(vgv_total)}", "#007bff"), unsafe_allow_html=True)
    card_cols[1].markdown(render_metric_card("Custo Indireto Total", f"R$ {fmt_br(custo_indireto_calculado)}", "#28a745"), unsafe_allow_html=True)
    card_cols[2].markdown(render_metric_card("% do Custo Indireto", f"{((custo_indireto_calculado / vgv_total) * 100):.2f}%" if vgv_total > 0 else "0.00%", "#ff7f00"), unsafe_allow_html=True)


# Bloco da tabela manual
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
