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
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

st.set_page_config(page_title="Administração da Obra", layout="wide", page_icon="📝")

# Injeta CSS para aumentar o tamanho da fonte da tabela AgGrid
st.markdown("""
<style>
    /* Aumenta a fonte do cabeçalho da tabela */
    .ag-theme-streamlit .ag-header-cell-text {
        font-size: 20px !important;
    }
    /* Aumenta a fonte das células da tabela */
    .ag-theme-streamlit .ag-cell {
        font-size: 20px !important;
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
    col_slider, col_spacer = st.columns([0.6, 0.4])
    with col_slider:
        st.session_state.duracao_obra = st.slider(
            "Duração da Obra (meses):",
            min_value=1,
            max_value=60,
            value=st.session_state.duracao_obra
        )

    # Prepara os dados para o AgGrid
    dados_tabela_obra = []
    
    for item, valor_mensal in st.session_state.custos_indiretos_obra.items():
        dados_tabela_obra.append({
            "Item": item,
            "Custo Mensal (R$)": valor_mensal,
            "Custo Total (R$)": valor_mensal * st.session_state.duracao_obra
        })
    
    df_custos_obra = pd.DataFrame(dados_tabela_obra)

    # Configura o AgGrid
    gb = GridOptionsBuilder.from_dataframe(df_custos_obra)

    jscode_formatador_moeda = JsCode("""
        function(params) {
            if (params.value === null || params.value === undefined) { return ''; }
            return 'R$ ' + params.value.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        }
    """)
    
    gb.configure_column("Item", headerName="Item", flex=5, resizable=True)
    gb.configure_column("Custo Mensal (R$)",
        headerName="Custo Mensal (R$)",
        editable=True,
        valueFormatter=jscode_formatador_moeda,
        flex=1,
        resizable=False,
        type=["numericColumn", "numberColumnFilter", "customNumericFormat"]
    )
    gb.configure_column("Custo Total (R$)",
        headerName="Custo Total (R$)",
        valueFormatter=jscode_formatador_moeda,
        flex=1,
        resizable=False,
        type=["numericColumn", "numberColumnFilter"]
    )
    
    gridOptions = gb.build()

    col_tabela_obra, col_metricas_obra = st.columns([0.6, 0.4])

    with col_tabela_obra:
        st.write("### Ajuste os Custos Mensais")
        grid_response = AgGrid(
            df_custos_obra,
            gridOptions=gridOptions,
            height=450,
            width='100%',
            update_mode='MODEL_CHANGED',
            allow_unsafe_jscode=True,
            try_convert_numeric_dtypes=True,
            theme='streamlit'
        )
    
    # Usa os dados editados
    edited_df_custos_obra = grid_response['data']
    
    # Recalcula o total a partir dos dados editados
    if not edited_df_custos_obra.empty:
        total_mensal = edited_df_custos_obra["Custo Mensal (R$)"].sum()
        custo_indireto_obra_total_recalculado = total_mensal * st.session_state.duracao_obra
        
        # Salva o estado
        st.session_state.custos_indiretos_obra = {
            row["Item"]: row["Custo Mensal (R$)"]
            for index, row in edited_df_custos_obra.iterrows()
        }
        info['custos_indiretos_obra'] = st.session_state.custos_indiretos_obra
        info['duracao_obra'] = st.session_state.duracao_obra
        
        with col_metricas_obra:
            st.subheader("Resumo") # Alterado para subheader

            card_metric_pro(
                label="Custo Mensal Total",
                value=f"R$ {fmt_br(total_mensal)}",
                icon_name="cash-coin",
                bg_color="linear-gradient(145deg, #e6f2ff, #cce5ff)",
                text_color="#0056b3"
            )
            
            card_metric_pro(
                label="Duração da Obra (meses)",
                value=f"{st.session_state.duracao_obra}",
                icon_name="clock",
                bg_color="linear-gradient(145deg, #f0fff0, #d9f7d9)",
                text_color="#28a745"
            )
            
            card_metric_pro(
                label="Custo Indireto de Obra Total",
                value=f"R$ {fmt_br(custo_indireto_obra_total_recalculado)}",
                icon_name="building-fill-up",
                bg_color="linear-gradient(145deg, #fff5e6, #ffe0b3)",
                text_color="#ff7f00"
            )
