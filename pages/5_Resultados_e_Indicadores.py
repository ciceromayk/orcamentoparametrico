# pages/3_Resultados_e_Indicadores.py
import streamlit as st
import pandas as pd
from utils import (
    fmt_br, render_metric_card, render_sidebar,
    calculate_financial_metrics, calcular_areas_e_custos,
    generate_pdf_report
)
import json
import requests
import time

st.set_page_config(page_title="Resultados e Indicadores", layout="wide")

# CSS para configurar a largura do dialog
st.markdown("""
<style>
    /* Essa classe é usada pelo Streamlit para o contêiner do dialog. */
    /* Você pode precisar inspecionar o elemento para verificar se a classe mudou em versões futuras do Streamlit. */
    .st-emotion-cache-1r651z {
        max-width: 800px;  /* Largura máxima do pop-up */
        width: 90%;       /* Largura responsiva para telas menores */
    }
</style>
""", unsafe_allow_html=True)

if "projeto_info" not in st.session_state:
    st.error("Nenhum projeto carregado. Por favor, selecione um projeto na página inicial.")
    if st.button("Voltar para a seleção de projetos"):
        st.switch_page("Início.py")
    st.stop()

# Passamos uma chave única para a sidebar para evitar erros de chave duplicada
render_sidebar(form_key="sidebar_resultados")

info = st.session_state.projeto_info
st.title("📈 Resultados e Indicadores Chave")

# --- CÁLCULOS GERAIS (agora usando as funções de utils) ---
pavimentos_df = pd.DataFrame(info.get('pavimentos', []))
custos_config = info.get('custos_config', {})
area_construida_total, _, custo_direto_total, pavimentos_df = calcular_areas_e_custos(st.session_state.pavimentos, custos_config)

# Obter o custo indireto de obra da session_state de forma segura
custo_indireto_obra_total = 0
if 'custos_indiretos_obra' in st.session_state and 'duracao_obra' in st.session_state:
    total_mensal = sum(st.session_state.custos_indiretos_obra.values())
    custo_indireto_obra_total = total_mensal * st.session_state.duracao_obra

# Calculando todas as métricas financeiras de uma só vez
finance_metrics = calculate_financial_metrics(info, pavimentos_df, custo_direto_total, custo_indireto_obra_total)
vgv_total = finance_metrics['vgv_total']
valor_total_despesas = finance_metrics['valor_total_despesas']
lucratividade_valor = finance_metrics['lucratividade_valor']
lucratividade_percentual = finance_metrics['lucratividade_percentual']
custo_indireto_calculado = finance_metrics['custo_indireto_calculado']
custo_terreno_total = finance_metrics['custo_terreno_total']
total_area_privativa = finance_metrics['area_privativa_total']

# --- APRESENTAÇÃO DOS RESULTADOS ---

# Adicionando a nova seção de Resumo do Empreendimento
with st.container(border=True):
    st.subheader("Resumo do Empreendimento")
    # Calcula o Índice AC/AP
    relacao_ac_ap = area_construida_total / total_area_privativa if total_area_privativa > 0 else 0
    num_unidades = info.get('num_unidades', 0)
    
    resumo_cols = st.columns(4)
    resumo_cols[0].markdown(render_metric_card("Área Constr.", f"{fmt_br(area_construida_total)} m²", "#3c763d", icon="bi-building"), unsafe_allow_html=True)
    resumo_cols[1].markdown(render_metric_card("Área Privativa", f"{fmt_br(total_area_privativa)} m²", "#a94442", icon="bi-house"), unsafe_allow_html=True)
    resumo_cols[2].markdown(render_metric_card("Índice AC / AP", f"{relacao_ac_ap:.2f}", "#5c5c5c", icon="bi-calculator"), unsafe_allow_html=True)
    resumo_cols[3].markdown(render_metric_card("Nº de Unidades", f"{num_unidades}", "#1f77b4", icon="bi-columns"), unsafe_allow_html=True)
    

with st.container(border=True):
    cores = ["#00829d", "#6a42c1", "#3c763d", "#a94442", "#fd7e14", "#20c997", "#31708f", "#8a6d3b"]
    st.subheader("Resultados Financeiros")
    res_cols = st.columns(4)
    res_cols[0].markdown(render_metric_card("VGV Total", f"R$ {fmt_br(vgv_total)}", cores[0], icon="bi-cash-stack"), unsafe_allow_html=True)
    res_cols[1].markdown(render_metric_card("Custo Total", f"R$ {fmt_br(valor_total_despesas)}", cores[1], icon="bi-currency-dollar"), unsafe_allow_html=True)
    res_cols[2].markdown(render_metric_card("Lucro Bruto", f"R$ {fmt_br(lucratividade_valor)}", cores[2], icon="bi-piggy-bank"), unsafe_allow_html=True)
    res_cols[3].markdown(render_metric_card("Margem de Lucro", f"{lucratividade_percentual:.2f}%", cores[3], icon="bi-percent"), unsafe_allow_html=True)
    st.divider()
    st.subheader("Composição do Custo Total")
    comp_cols = st.columns(4) # Alterado para 4 colunas
    if valor_total_despesas > 0:
        p_direto = (custo_direto_total / valor_total_despesas * 100)
        p_indireto_venda = (custo_indireto_calculado / valor_total_despesas * 100)
        p_indireto_obra = (custo_indireto_obra_total / valor_total_despesas * 100)
        p_terreno = (custo_terreno_total / valor_total_despesas * 100)

        comp_cols[0].markdown(render_metric_card(f"Custo Direto ({p_direto:.2f}%)", f"R$ {fmt_br(custo_direto_total)}", cores[6], icon="bi-hammer"), unsafe_allow_html=True)
        comp_cols[1].markdown(render_metric_card(f"Indiretos Venda ({p_indireto_venda:.2f}%)", f"R$ {fmt_br(custo_indireto_calculado)}", cores[7], icon="bi-megaphone"), unsafe_allow_html=True)
        comp_cols[2].markdown(render_metric_card(f"Indiretos Obra ({p_indireto_obra:.2f}%)", f"R$ {fmt_br(custo_indireto_obra_total)}", "#ff7f0e", icon="bi-wrench"), unsafe_allow_html=True) # Novo card
        comp_cols[3].markdown(render_metric_card(f"Custo do Terreno ({p_terreno:.2f}%)", f"R$ {fmt_br(custo_terreno_total)}", cores[1], icon="bi-map"), unsafe_allow_html=True)
    st.divider()
    st.subheader("Indicadores por Área Construída")
    ind_cols = st.columns(4)
    ind_cols[0].markdown(render_metric_card("Terreno / Custo Total", f"{(custo_terreno_total / valor_total_despesas * 100 if valor_total_despesas > 0 else 0):.2f}%", cores[4], icon="bi-geo-alt"), unsafe_allow_html=True)
    ind_cols[1].markdown(render_metric_card("Custo Direto / m²", f"R$ {fmt_br(custo_direto_total / area_construida_total if area_construida_total > 0 else 0)}", cores[5], icon="bi-rulers"), unsafe_allow_html=True)
    ind_cols[2].markdown(render_metric_card("Custo Indireto / m²", f"R$ {fmt_br((custo_indireto_calculado + custo_indireto_obra_total) / area_construida_total if area_construida_total > 0 else 0)}", cores[6], icon="bi-person-gear"), unsafe_allow_html=True)
    ind_cols[3].markdown(render_metric_card("Custo Total / m²", f"R$ {fmt_br(valor_total_despesas / area_construida_total if area_construida_total > 0 else 0)}", cores[7], icon="bi-clipboard-data"), unsafe_allow_html=True)

st.divider()

# --- DEFINIÇÃO DA LÓGICA DE GERAÇÃO DA ANÁLISE ---
def generate_ai_analysis():
    """Gera a análise de viabilidade com IA e exibe o resultado."""
    # Prepara o prompt com os dados mais importantes
    prompt_data = {
        "nome_projeto": info.get('nome', 'Projeto Sem Nome'),
        "vgv_total": vgv_total,
        "custo_total": valor_total_despesas,
        "lucro_bruto": lucratividade_valor,
        "margem_lucro_percentual": lucratividade_percentual,
        "custo_direto": custo_direto_total,
        "custo_indireto_venda": custo_indireto_calculado,
        "custo_indireto_obra": custo_indireto_obra_total,
        "custo_terreno": custo_terreno_total,
        "area_privativa": total_area_privativa,
        "area_terreno": info.get('area_terreno', 0),
        "area_construida": area_construida_total,
        "composicao_custos": {
            "Custo Direto": p_direto,
            "Custo Indireto de Venda": p_indireto_venda,
            "Custo Indireto de Obra": p_indireto_obra,
            "Custo do Terreno": p_terreno
        }
    }

    prompt = f"""
Você está atuando como um consultor sênior em análise de viabilidade para o setor de desenvolvimento imobiliário. Sua tarefa é gerar um relatório analítico e detalhado em português, utilizando os dados financeiros fornecidos.

Por favor, siga esta estrutura e aborde os seguintes pontos na análise:

1. **Avaliação Financeira do Projeto**
   Faça uma análise da saúde financeira geral do projeto. Comente sobre o VGV Total, o Custo Total, o Lucro Bruto e, principalmente, a Margem de Lucro do projeto. Compare a margem de lucro com os benchmarks de mercado para determinar se o resultado é promissor.

2. **Análise Detalhada dos Custos**
   Analise a composição do Custo Total. Descreva como cada componente (Custo Direto, Custo Indireto de Venda, Custo Indireto de Obra e Custo do Terreno) impacta a rentabilidade do projeto. Interprete as porcentagens para destacar a distribuição dos gastos.

3. **Análise de Desempenho por Área e Custo Unitário**
   Avalie os indicadores por área construída, como o Custo Direto / m², Custo Indireto / m² e Custo Total / m². Explique o significado do Índice AC / AP e como ele se relaciona com a eficiência e o custo do projeto.

4. **Identificação de Riscos e Oportunidades**
   Aponte os principais riscos financeiros com base nos dados. Sugira pelo menos 3 a 5 recomendações estratégicas e acionáveis para otimizar o projeto, focando em oportunidades de redução de custos ou aumento de receita.

5. **Conclusão e Próximos Passos**
   Conclua o relatório com um resumo das descobertas mais importantes e forneça uma perspectiva clara sobre a viabilidade geral do projeto, além de sugerir os próximos passos para a sua execução.

Mantenha um tom formal, técnico e objetivo. Use as métricas e valores fornecidos nos dados para fundamentar sua análise e suas recomendações.

**Dados do Projeto:**
- Nome: {prompt_data['nome_projeto']}
- VGV Total: R$ {prompt_data['vgv_total']:.2f}
- Custo Total: R$ {prompt_data['custo_total']:.2f}
- Lucro Bruto: R$ {prompt_data['lucro_bruto']:.2f}
- Margem de Lucro: {prompt_data['margem_lucro_percentual']:.2f}%
- Custo Direto: R$ {prompt_data['custo_direto']:.2f}
- Custo Indireto de Venda: R$ {prompt_data['custo_indireto_venda']:.2f}
- Custo Indireto de Obra: R$ {prompt_data['custo_indireto_obra']:.2f}
- Custo do Terreno: R$ {prompt_data['custo_terreno']:.2f}
- Área Privativa: {prompt_data['area_privativa']:.2f} m²
- Área Construída: {prompt_data['area_construida']:.2f} m²
- Composição do Custo (%): {prompt_data['composicao_custos']}
"""
    
    # Adiciona a exibição de loading
    with st.spinner("Gerando análise com I.A...."):
        try:
            # Check for API key in st.secrets first, then st.session_state
            if "gemini_api_key" not in st.secrets:
                if "gemini_api_key" not in st.session_state or not st.session_state.gemini_api_key:
                    st.error("Chave da API do Google Gemini não encontrada. Por favor, adicione-a.")
                    return None
                API_KEY = st.session_state.gemini_api_key
            else:
                API_KEY = st.secrets["gemini_api_key"]
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.5,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 2048,
                    "responseMimeType": "text/plain"
                }
            }

            headers = {'Content-Type': 'application/json'}
            
            max_retries = 5
            base_delay = 1.0
            for i in range(max_retries):
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                if response.status_code == 200:
                    break
                elif response.status_code == 429 and i < max_retries - 1:
                    delay = base_delay * (2 ** i)
                    st.warning(f"Limite de taxa atingido. Tentando novamente em {delay:.1f} segundos...")
                    time.sleep(delay)
                else:
                    response.raise_for_status()
            
            if response.status_code == 200:
                result = response.json()
                if result and 'candidates' in result and len(result['candidates']) > 0 and 'content' in result['candidates'][0] and 'parts' in result['candidates'][0]['content'] and len(result['candidates'][0]['content']['parts']) > 0:
                    analysis = result['candidates'][0]['content']['parts'][0]['text']
                    return analysis
                else:
                    st.error("A I.A. não conseguiu gerar uma resposta válida. Por favor, tente novamente com dados diferentes ou ajuste o prompt.")
            else:
                st.error(f"Erro ao se comunicar com a API da I.A.: {response.status_code} - {response.text}. Tente novamente mais tarde.")

        except requests.exceptions.RequestException as e:
            st.error(f"Erro de conexão com a API da I.A.: {e}")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")
    return None

# --- DEFINIÇÃO DO DIALOG (POP-UP) PARA A API KEY ---
@st.dialog("Adicionar Chave da API")
def api_key_dialog():
    st.write("Para usar a análise de I.A., por favor, insira sua chave da API do Google Gemini.")
    st.markdown("Se você não tem uma, pode obtê-la [aqui](https://makersuite.google.com/app/apikey).")
    
    with st.form("api_key_form"):
        api_key = st.text_input("Chave da API", type="password")
        if st.form_submit_button("Salvar Chave e Continuar"):
            if api_key:
                st.session_state.gemini_api_key = api_key
                st.rerun()
            else:
                st.error("Por favor, insira uma chave da API.")

# Adiciona o botão de análise com IA
if st.button("Gerar Análise de Viabilidade com I.A.", type="primary"):
    if "gemini_api_key" not in st.secrets:
        if "gemini_api_key" not in st.session_state or not st.session_state.gemini_api_key:
            api_key_dialog()
            # St.stop()
    else:
        # Tenta gerar a análise e exibe-a no expander
        analysis_text = generate_ai_analysis()
        if analysis_text:
            st.session_state.ai_analysis = analysis_text

# Exibe a análise em um expander se ela existir na session_state
if "ai_analysis" in st.session_state and st.session_state.ai_analysis:
    with st.expander("🤖 Análise de Viabilidade com I.A.", expanded=True):
        # Divide o texto em seções baseadas nos cabeçalhos numerados
        sections = st.session_state.ai_analysis.split('\n\n')
        
        # Itera sobre as seções e formata cada uma individualmente
        for section in sections:
            if section.strip():
                if section.startswith("1. ") or section.startswith("2. ") or section.startswith("3. ") or section.startswith("4. ") or section.startswith("5. "):
                    parts = section.split('\n', 1)
                    header = parts[0].strip()
                    content = parts[1].strip() if len(parts) > 1 else ""
                    st.markdown(f"**{header}**")
                    st.markdown(content)
                else:
                    st.markdown(section.strip())

# Botão de download do relatório PDF
if st.button("Gerar e Baixar Relatório PDF", type="primary"):
    with st.spinner("Gerando seu relatório..."):
        pdf_data = generate_pdf_report(
            info, vgv_total, valor_total_despesas, lucratividade_valor, lucratividade_percentual,
            custo_direto_total, custo_indireto_calculado, custo_terreno_total, area_construida_total,
            custos_config, st.session_state.custos_indiretos_percentuais, pavimentos_df, custo_indireto_obra_total
        )
        st.download_button(
            label="Relatório Concluído! Clique aqui para baixar.",
            data=pdf_data,
            file_name=f"Relatorio_{info['nome']}.pdf",
            mime="application/pdf"
        )
