import streamlit as st
import pandas as pd
import urllib.parse
from utils import (
    fmt_br, render_metric_card, render_sidebar,
    DEFAULT_PAVIMENTO, TIPOS_PAVIMENTO,
    init_session_state_vars, calcular_areas_e_custos,
    ProjectManager
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
    .total-row {
        background-color: #f0f2f6;
        padding: 10px 0;
        margin-top: 20px;
        font-weight: bold;
        border-top: 2px solid #e0e0e0;
    }
    /* Estilo para alinhar os botões */
    .button-container {
        display: flex;
        justify-content: flex-end; /* Alinha os botões à direita */
        gap: 10px; /* Espaçamento entre os botões */
        margin-top: 20px;
    }
    /* Estilo para o botão customizado */
    .stButton>button {
        width: 180px; /* Largura fixa para os botões */
        height: 40px; /* Altura fixa para os botões */
    }
    .stButton>button:hover {
        filter: brightness(85%);
    }
    .stButton>button[type="submit"] {
        background-color: #ff5252;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Verifica e inicializa o ProjectManager se ele não estiver no estado da sessão
if 'project_manager' not in st.session_state:
    st.session_state.project_manager = ProjectManager("projects.json")

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
    
    # Calcular a área privativa total e o número de unidades a partir dos dados de unidades
    total_area_privativa_unidades = sum(unidade['area_privativa_total'] for unidade in st.session_state.unidades)
    total_unidades = sum(unidade['quantidade'] for unidade in st.session_state.unidades)

    # Use um formulário para atualizar os dados do projeto
    with st.form(key="dados_gerais_form"):
        col1, col2 = st.columns([1, 2])
        info['nome'] = col1.text_input("Nome do Projeto", value=info['nome'])
        info['endereco'] = col2.text_input("Endereço do Projeto", value=info.get('endereco', ''))
        
        col_end1, col_end2, col_end3, col_end_btn = st.columns([1, 1, 1, 1])
        info['bairro'] = col_end1.text_input("Bairro", value=info.get('bairro', ''))
        info['cidade'] = col_end2.text_input("Cidade", value=info.get('cidade', ''))
        info['estado'] = col_end3.text_input("Estado", value=info.get('estado', ''))
        
        with col_end_btn:
            st.markdown('<div style="height: 2.7rem;"></div>', unsafe_allow_html=True) # Espaço para alinhar com os inputs
            full_address = f"{info.get('endereco', '')}, {info.get('bairro', '')}, {info.get('cidade', '')}, {info.get('estado', '')}"
            encoded_address = urllib.parse.quote_plus(full_address)
            maps_url = f"https://www.google.com/maps/place/{encoded_address}"
            st.link_button("🗺️ Ver no Mapa", url=maps_url, help="Clique para ver o endereço no Google Maps", type="secondary")

        # Container para botões de atualização e salvamento
        st.markdown('<div class="button-container">', unsafe_allow_html=True)
        submitted = st.form_submit_button("Atualizar Dados")
        st.markdown('</div>', unsafe_allow_html=True)

        st.write("---")
        
        col3, col4, col5 = st.columns(3)
        info['area_terreno'] = col3.number_input("Área Terreno (m²)", value=info['area_terreno'], format="%.2f")
        info['custos_config']['custo_terreno_m2'] = col4.number_input("Custo do Terreno por m² (R$)", value=info['custos_config'].get('custo_terreno_m2', 0.0), format="%.2f")
        info['custos_config']['custo_area_privativa'] = col5.number_input("Custo de Construção (R$/m² privativo)", value=info['custos_config'].get('custo_area_privativa', 0.0), format="%.2f", step=100.0)
        
        st.write("---")

        info['custos_config']['preco_medio_venda_m2'] = st.number_input("Preço Médio de Venda (R$/m² privativo)", value=info['custos_config'].get('preco_medio_venda_m2', 10000.0), format="%.2f")

    # Cards com os dados do projeto
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    cores = ["#3c763d", "#a94442", "#5c5c5c", "#1f77b4"]
    c1.markdown(render_metric_card("Área Constr.", f"{fmt_br(area_construida_total)} m²", cores[0]), unsafe_allow_html=True)
    c2.markdown(render_metric_card("Área Privativa", f"{fmt_br(total_area_privativa_unidades)} m²", cores[1]), unsafe_allow_html=True)
    c3.markdown(render_metric_card("Área Eq.", f"{fmt_br(area_equivalente_total)} m²", cores[2]), unsafe_allow_html=True)
    
    # Adicionando o novo card de Índice AP/AC
    relacao_ap_ac = total_area_privativa_unidades / area_construida_total if area_construida_total > 0 else 0
    c4.markdown(render_metric_card("Índice AP / AC", f"{relacao_ap_ac:.2f}", cores[3]), unsafe_allow_html=True)


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
    
    total_area_pav = 0
    total_area_eq_pav = 0
    total_area_constr_pav = 0

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
            
            area_total_i, area_eq_i = pav['area'] * pav['rep'], (pav['area'] * pav['rep']) * pav['coef']
            area_constr_i = area_total_i if pav.get('constr', True) else 0.0

            cols[5].markdown(f"<div style='text-align:center; padding-top: 8px;'>{fmt_br(area_eq_i)}</div>", unsafe_allow_html=True)
            cols[6].markdown(f"<div style='text-align:center; padding-top: 8px;'>{fmt_br(area_constr_i)}</div>", unsafe_allow_html=True)

            if cols[8].button("🗑️", key=f"del_{i}", use_container_width=True):
                st.session_state.deleting_pav_index = i
                st.rerun()

            total_area_pav += area_total_i
            total_area_eq_pav += area_eq_i
            if pav.get('constr', True):
                total_area_constr_pav += area_total_i

        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.pavimentos:
            total_pav_cols = st.columns(col_widths)
            total_pav_cols[0].markdown(f"<div style='font-weight: bold; text-align: center;'>Total</div>", unsafe_allow_html=True)
            total_pav_cols[1].empty()
            total_pav_cols[2].empty()
            total_pav_cols[3].empty()
            total_pav_cols[4].markdown(f"<div style='font-weight: bold; text-align: center;'>{fmt_br(total_area_pav)}</div>", unsafe_allow_html=True)
            total_pav_cols[5].markdown(f"<div style='font-weight: bold; text-align: center;'>{fmt_br(total_area_eq_pav)}</div>", unsafe_allow_html=True)
            total_pav_cols[6].markdown(f"<div style='font-weight: bold; text-align: center;'>{fmt_br(total_area_constr_pav)}</div>", unsafe_allow_html=True)
            total_pav_cols[7].empty()
            total_pav_cols[8].empty()


    if st.session_state.deleting_pav_index is not None:
        confirm_delete_dialog()

# --- Nova Tabela de Dados de Unidades ---
with st.expander("📝 Dados de Unidades", expanded=True):
    b1_un, _ = st.columns([0.2, 0.8])
    if b1_un.button("➕ Adicionar Unidade"):
        # Adiciona uma nova unidade ao estado da sessão
        # Inclui a chave 'area_privativa_total' para evitar o KeyError
        new_unit = {"nome": f"Unidade {len(st.session_state.unidades) + 1}", "quantidade": 1, "area_privativa": 100.0}
        new_unit['area_privativa_total'] = new_unit['quantidade'] * new_unit['area_privativa']
        st.session_state.unidades.append(new_unit)
        st.rerun()

    # Definir as colunas da tabela
    col_widths = [3, 1.5, 2, 2.5, 0.8]
    headers = ["Tipo de Unidade", "Quantidade", "Área Privativa (m²)", "Área Privativa Total (m²)", "Ação"]
    header_cols = st.columns(col_widths)
    for hc, title in zip(header_cols, headers):
        hc.markdown(f'<p style="text-align:center; font-size:14px;"><b>{title}</b></p>', unsafe_allow_html=True)

    # Exibir a tabela com campos editáveis
    total_quantidade = 0
    total_area_privativa_total = 0
    if st.session_state.unidades:
        for i, unidade in enumerate(st.session_state.unidades):
            cols = st.columns(col_widths)
            
            unidade['nome'] = cols[0].text_input("nome", unidade['nome'], key=f"unid_nome_{i}", label_visibility="collapsed")
            unidade['quantidade'] = cols[1].number_input("quantidade", min_value=1, value=unidade['quantidade'], step=1, key=f"unid_qtd_{i}", label_visibility="collapsed")
            unidade['area_privativa'] = cols[2].number_input("area_priv", min_value=0.0, value=unidade['area_privativa'], step=1.0, format="%.2f", key=f"unid_area_{i}", label_visibility="collapsed")
            
            unidade['area_privativa_total'] = unidade['quantidade'] * unidade['area_privativa']
            cols[3].markdown(f"<div style='text-align:center; padding-top: 8px;'>{fmt_br(unidade['area_privativa_total'])}</div>", unsafe_allow_html=True)

            if cols[4].button("🗑️", key=f"del_unid_{i}", use_container_width=True):
                del st.session_state.unidades[i]
                st.rerun()

            total_quantidade += unidade['quantidade']
            total_area_privativa_total += unidade['area_privativa_total']

    # Linha de totais com melhorias de estilo
    if st.session_state.unidades:
        st.markdown("<div class='total-row'>", unsafe_allow_html=True)
        total_cols = st.columns(col_widths)
        total_cols[0].markdown(f"<div style='font-weight: bold; text-align:center;'>Total</div>", unsafe_allow_html=True)
        total_cols[1].markdown(f"<div style='font-weight: bold; text-align:center; '>{total_quantidade}</div>", unsafe_allow_html=True)
        total_cols[2].empty()
        total_cols[3].markdown(f"<div style='font-weight: bold; text-align:center;'>{fmt_br(total_area_privativa_total)}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Sincroniza o número total de unidades com o estado da sessão
    info['num_unidades'] = total_quantidade


info['pavimentos'] = st.session_state.pavimentos
info['unidades'] = st.session_state.unidades

if submitted:
    st.session_state.project_manager.save_project(info)
    st.success("Dados do projeto atualizados com sucesso!")

if st.button("Salvar Dados do Projeto", type="primary"):
    st.session_state.project_manager.save_project(info)
    st.success("Dados do projeto salvos com sucesso!")
