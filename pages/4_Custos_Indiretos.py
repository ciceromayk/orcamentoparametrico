# pages/3_Custos_Indiretos.py
import streamlit as st
import pandas as pd
from utils import (
    fmt_br, render_metric_card, render_sidebar, DEFAULT_CUSTOS_INDIRETOS_OBRA,
    DEFAULT_CUSTOS_INDIRETOS, ETAPAS_OBRA, DEFAULT_PAVIMENTO,
    list_projects, save_project, load_project, delete_project,
    JSON_PATH, HISTORICO_DIRETO_PATH, HISTORICO_INDIRETO_PATH,
    load_json, save_to_historico
)
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

st.set_page_config(page_title="Custos Indiretos", layout="wide", page_icon="💸")

# Injeta CSS para aumentar o tamanho da fonte da tabela AgGrid
st.markdown("""
<style>
    /* Aumenta a fonte do cabeçalho da tabela */
    .ag-theme-streamlit .ag-header-cell-text {
        font-size: 18px !important;
    }
    /* Aumenta a fonte das células da tabela */
    .ag-theme-streamlit .ag-cell {
        font-size: 18px !important;
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
        padding: 15px;
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

render_sidebar(form_key="sidebar_custos_indiretos")

info = st.session_state.projeto_info
st.title("💸 Custos Indiretos")
st.subheader("Análise e Detalhamento de Custos Indiretos do Projeto")


# Cálculos Preliminares
custos_config = info.get('custos_config', {})
preco_medio_venda_m2 = custos_config.get('preco_medio_venda_m2', 10000.0)
vgv_total = info.get('area_privativa', 0) * preco_medio_venda_m2

# Bloco principal com a nova tabela AgGrid e Gráficos
with st.expander("Detalhamento de Custos Indiretos", expanded=True):
    st.subheader("Configuração de Custos Indiretos (calculados sobre o VGV)")

    # Inicialização do session_state
    if 'custos_indiretos_percentuais' not in st.session_state:
        custos_salvos = info.get('custos_indiretos_percentuais', {})
        
        if custos_salvos and isinstance(list(custos_salvos.values())[0], (int, float)):
            st.session_state.custos_indiretos_percentuais = {item: {"percentual": val, "fonte": "Manual"} for item, val in custos_salvos.items()}
        else:
            st.session_state.custos_indiretos_percentuais = {item: custos_salvos.get(item, {"percentual": vals[1], "fonte": "Manual"}) for item, vals in DEFAULT_CUSTOS_INDIRETOS.items()}

    # Preparar os Dados para o AgGrid
    dados_tabela = []
    for item, (min_val, default_val, max_val) in DEFAULT_CUSTOS_INDIRETOS.items():
        percentual_atual = st.session_state.custos_indiretos_percentuais.get(item, {"percentual": default_val})['percentual']
        custo_calculado = vgv_total * (percentual_atual / 100)
        
        dados_tabela.append({
            "Item": item,
            "Percentual (%)": percentual_atual,
            "Custo (R$)": custo_calculado,
        })

    df = pd.DataFrame(dados_tabela)

    # Configurar o AgGrid
    gb = GridOptionsBuilder.from_dataframe(df)
    
    jscode_formatador_moeda = JsCode("""
        function(params) {
            if (params.value === null || params.value === undefined) { return ''; }
            return 'R$ ' + params.value.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        }
    """)

    gb.configure_column("Item", headerName="Item", flex=5, resizable=True)
    gb.configure_column("Percentual (%)",
        headerName="Percentual (%)",
        editable=True,
        flex=1,
        resizable=False,
        type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
        precision=2
    )
    gb.configure_column("Custo (R$)",
        headerName="Custo (R$)",
        valueFormatter=jscode_formatador_moeda,
        flex=1,
        resizable=False,
        type=["numericColumn", "numberColumnFilter"]
    )
    
    gridOptions = gb.build()

    col1, col2 = st.columns([0.6, 0.4])

    with col1:
        st.write("### Ajuste os Percentuais")
        grid_response = AgGrid(
            df,
            gridOptions=gridOptions,
            height=450,
            width='100%',
            update_mode='MODEL_CHANGED',
            allow_unsafe_jscode=True,
            try_convert_numeric_dtypes=True,
            theme='streamlit'
        )
        
    with col2:
        st.write("### Resumo Financeiro")
        st.write("<br>", unsafe_allow_html=True)
        
        card_metric_pro(
            label="VGV Total",
            value=f"R$ {fmt_br(vgv_total)}",
            icon_name="building-fill-up",
            bg_color="linear-gradient(145deg, #e6f2ff, #cce5ff)",
            text_color="#0056b3"
        )
        st.write("<br>", unsafe_allow_html=True)
        
        # Recalcula o custo indireto total para exibir no card
        edited_df = grid_response['data']
        edited_df["Custo (R$)"] = vgv_total * (pd.to_numeric(edited_df["Percentual (%)"], errors='coerce').fillna(0) / 100)
        custo_indireto_calculado = edited_df["Custo (R$)"].sum()

        card_metric_pro(
            label="Custo Indireto Total",
            value=f"R$ {fmt_br(custo_indireto_calculado)}",
            icon_name="cash-coin",
            bg_color="linear-gradient(145deg, #f0fff0, #d9f7d9)",
            text_color="#28a745"
        )
        st.write("<br>", unsafe_allow_html=True)
        
        card_metric_pro(
            label="% do Custo Indireto",
            value=f"{((custo_indireto_calculado / vgv_total) * 100):.2f}%",
            icon_name="percent",
            bg_color="linear-gradient(145deg, #fff5e6, #ffe0b3)",
            text_color="#ff7f00"
        )
        
    # Usa os Dados Editados
    edited_df = grid_response['data']
    
    # Recalcular "Custo (R$)" baseado no percentual editado
    edited_df["Custo (R$)"] = vgv_total * (pd.to_numeric(edited_df["Percentual (%)"], errors='coerce').fillna(0) / 100)
    custo_indireto_calculado = edited_df["Custo (R$)"].sum()
    
    for index, row in edited_df.iterrows():
        item_nome = row["Item"]
        novo_percentual = row["Percentual (%)"]
        st.session_state.custos_indiretos_percentuais[item_nome]['percentual'] = novo_percentual
        
    # Atualiza o estado da sessão
    info['custos_indiretos_percentuais'] = st.session_state.custos_indiretos_percentuais
