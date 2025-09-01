# pages/2_Custos_Diretos.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils import (
    fmt_br, render_metric_card, render_sidebar, handle_percentage_redistribution,
    ETAPAS_OBRA,
    init_session_state_vars, calcular_areas_e_custos, ProjectManager, save_to_historico,
    HISTORICO_DIRETO_PATH # Adicionado o import do caminho
)

st.set_page_config(page_title="Custos Diretos", layout="wide")

if "projeto_info" not in st.session_state:
    st.error("Nenhum projeto carregado. Por favor, selecione um projeto na página inicial.")
    if st.button("Voltar para a seleção de projetos"):
        st.switch_page("Início.py")
    st.stop()

# Inicializa as variáveis de estado
init_session_state_vars(st.session_state.projeto_info)

render_sidebar(form_key="sidebar_custos_diretos")

info = st.session_state.projeto_info
st.title("🏗️ Custos Diretos")
st.subheader("Análise e Detalhamento de Custos da Obra")

# Chamando a função centralizada de cálculo
area_construida_total, _, custo_direto_base, pavimentos_df = calcular_areas_e_custos(st.session_state.pavimentos, info.get('custos_config', {}))

# Recalcula o custo direto total com base nos percentuais ajustados
custo_direto_ajustado = 0
for etapa, values in st.session_state.etapas_percentuais.items():
    percentual = values.get('percentual', 0)
    custo_ajustado_etapa = custo_direto_base * (float(percentual) / 100)
    custo_direto_ajustado += custo_ajustado_etapa

# Salva o valor ajustado no estado da sessão
st.session_state.custo_direto_ajustado = custo_direto_ajustado

if not pavimentos_df.empty:
    with st.expander("📊 Análise e Resumo Financeiro", expanded=True):
        total_constr = area_construida_total
        custo_por_ac = custo_direto_ajustado / total_constr if total_constr > 0 else 0.0
        custo_med_unit = custo_direto_ajustado / info["num_unidades"] if info["num_unidades"] > 0 else 0.0
        card_cols = st.columns(4)
        cores = ["#31708f", "#3c763d", "#8a6d3b", "#a94442"]
        card_cols[0].markdown(render_metric_card("Custo Direto do Projeto", f"R$ {fmt_br(custo_direto_ajustado)}", cores[3]), unsafe_allow_html=True)
        card_cols[1].markdown(render_metric_card("Custo Médio / Unidade", f"R$ {fmt_br(custo_med_unit)}", "#337ab7"), unsafe_allow_html=True)
        card_cols[2].markdown(render_metric_card("Custo / m² (Área Constr.)", f"R$ {fmt_br(custo_por_ac)}", cores[1]), unsafe_allow_html=True)
        card_cols[3].markdown(render_metric_card("Área Construída Total", f"{fmt_br(total_constr)} m²", cores[2]), unsafe_allow_html=True)
        
        custo_por_tipo = pavimentos_df.groupby("tipo")["custo_direto"].sum().reset_index()
        fig = px.bar(custo_por_tipo, x='tipo', y='custo_direto', text_auto='.2s', title="Custo Direto por Tipo de Pavimento")
        fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False); fig.update_layout(xaxis_title=None, yaxis_title="Custo (R$)")
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("💸 Custo Direto por Etapa da Obra", expanded=True):
        st.markdown("##### Comparativo com Histórico de Obras")
        # CORRIGIDO: Usa o método load_json da instância de ProjectManager
        obras_historicas = st.session_state.project_manager.load_json(HISTORICO_DIRETO_PATH)
        obra_ref_selecionada = st.selectbox("Usar como Referência:", ["Nenhuma"] + [f"{o['id']} – {o['nome']}" for o in obras_historicas], index=0, key="ref_direto")
        
        ref_percentuais, ref_nome = {}, None
        if obra_ref_selecionada != "Nenhuma":
            ref_id = int(obra_ref_selecionada.split("–")[0].strip())
            ref_nome = obra_ref_selecionada.split("–")[1].strip()
            obra_ref_data = next((o for o in obras_historicas if o['id'] == ref_id), None)
            if obra_ref_data: ref_percentuais = obra_ref_data['percentuais']
        
        st.divider()
        cols = st.columns([2.5, 1.5, 1, 1.5, 1, 1.5, 1])
        cols[0].markdown("**Etapa**"); cols[1].markdown("**Fonte**"); cols[2].markdown("**Ref. (%)**")
        cols[3].markdown("**Seu Projeto (%)**"); cols[5].markdown("<p style='text-align: center;'>Custo (R$)</p>", unsafe_allow_html=True); cols[6].markdown("<p style='text-align: center;'>Ação</p>", unsafe_allow_html=True)

        for etapa, (min_val, default_val, max_val) in ETAPAS_OBRA.items():
            c = st.columns([2.5, 1.5, 1, 1.5, 1, 1.5, 1])
            c[0].container(height=38, border=False).write(etapa)
            etapa_info = st.session_state.etapas_percentuais.get(etapa, {"percentual": default_val, "fonte": "Manual"})
            c[1].container(height=38, border=False).write(etapa_info['fonte'])
            ref_val = ref_percentuais.get(etapa, 0)
            c[2].container(height=38, border=False).write(f"{ref_val:.2f}%" if obra_ref_selecionada != "Nenhuma" else "-")
            
            slider_col, input_col = c[3], c[4]
            current_percent = etapa_info['percentual']
            
            percent_slider = slider_col.slider("slider", min_val, max_val, float(current_percent), 0.1, key=f"slider_etapa_{etapa}", label_visibility="collapsed")
            percent_input = input_col.number_input("input", min_val, max_val, percent_slider, 0.1, key=f"input_etapa_{etapa}", label_visibility="collapsed")

            if percent_input != current_percent:
                st.session_state.etapas_percentuais[etapa]['percentual'] = percent_input
                st.session_state.etapas_percentuais[etapa]['fonte'] = "Manual"
                handle_percentage_redistribution('etapas_percentuais', ETAPAS_OBRA)
                st.rerun()

            custo_etapa = custo_direto_base * (percent_input / 100)
            c[5].markdown(f"<p style='text-align: center;'>R$ {fmt_br(custo_etapa)}</p>", unsafe_allow_html=True)
            
            if c[6].button("⬅️", key=f"apply_{etapa}", help=f"Aplicar percentual de referência ({ref_val:.2f}%)", use_container_width=True):
                if ref_nome:
                    st.session_state.etapas_percentuais[etapa]['percentual'] = ref_val
                    st.session_state.etapas_percentuais[etapa]['fonte'] = ref_nome
                    handle_percentage_redistribution('etapas_percentuais', ETAPAS_OBRA)
                    st.rerun()
