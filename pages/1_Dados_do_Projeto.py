# utils.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from weasyprint import HTML
import base64
from io import BytesIO
import matplotlib.pyplot as plt

# --- CONSTANTES GLOBAIS ---
JSON_PATH = "projects.json"
HISTORICO_DIRETO_PATH = "historico_direto.json"
HISTORICO_INDIRETO_PATH = "historico_indireto.json"

TIPOS_PAVIMENTO = {
    "Área Privativa (Autônoma)": (1.00, 1.00), "Áreas de lazer ambientadas": (2.00, 4.00), "Varandas": (0.75, 1.00),
    "Terraços / Áreas Descobertas": (0.30, 0.60), "Garagem (Subsolo)": (0.50, 0.75), "Estacionamento (terreno)": (0.05, 0.10),
    "Salas com Acabamento": (1.00, 1.00), "Salas sem Acabamento": (0.75, 0.90), "Loja sem Acabamento": (0.40, 0.60),
    "Serviço (unifam. baixa, aberta)": (0.50, 0.50), "Barrilete / Cx D'água / Casa Máquinas": (0.50, 0.75),
    "Piscinas": (0.50, 0.75), "Quintais / Calçadas / Jardins": (0.10, 0.30), "Projeção Terreno sem Benfeitoria": (0.00, 0.00),
}
DEFAULT_PAVIMENTO = {"nome": "Pavimento Tipo", "tipo": "Área Privativa (Autônoma)", "rep": 1, "coef": 1.00, "area": 100.0, "constr": True}

ETAPAS_OBRA = {
    "Serviços Preliminares e Fundações": (7.0, 8.0, 9.0), "Estrutura (Supraestrutura)": (14.0, 16.0, 22.0),
    "Vedações (Alvenaria)": (8.0, 10.0, 15.0), "Cobertura e Impermeabilização": (4.0, 5.0, 8.0),
    "Revestimentos de Fachada": (5.0, 6.0, 10.0), "Instalações (Elétrica e Hidráulica)": (12.0, 15.0, 18.0),
    "Esquadrias (Portas e Janelas)": (6.0, 8.0, 12.0), "Revestimentos de Piso": (8.0, 10.0, 15.0),
    "Revestimentos de Parede": (6.0, 8.0, 12.0), "Revestimentos de Forro": (3.0, 4.0, 6.0),
    "Pintura": (4.0, 5.0, 8.0), "Serviços Complementares e Externos": (3.0, 5.0, 10.0)
}

DEFAULT_CUSTOS_INDIRETOS = {
    "IRPJ/ CS/ PIS/ COFINS": (3.0, 4.0, 6.0), "Corretagem": (3.0, 3.61, 5.0),
    "Publicidade": (0.5, 0.9, 2.0), "Manutenção": (0.3, 0.5, 1.0), "Custo Fixo da Incorporadora": (3.0, 4.0, 6.0),
    "Assessoria Técnica": (0.5, 0.7, 1.5), "Projetos": (0.4, 0.52, 1.5),
    "Licenças e Incorporação": (0.1, 0.2, 0.5), "Outorga Onerosa": (0.0, 0.0, 10.0), "Condomínio": (0.0, 0.0, 0.5),
    "IPTU": (0.05, 0.07, 0.2), "Preparação do Terreno": (0.2, 0.33, 1.0), "Financiamento Bancário": (1.0, 1.9, 3.0),
}
DEFAULT_CUSTOS_INDIRETOS_FIXOS = {}
DEFAULT_CUSTOS_INDIRETOS_OBRA = {
    "Administração de Obra (Engenheiro/Arquiteto)": 15000.0, "Mestre de Obras e Encarregados": 8000.0,
    "Aluguel de Equipamentos (andaimes, betoneira, etc.)": 5000.0, "Consumo de Energia": 1000.0,
    "Consumo de Água": 500.0, "Telefone e Internet": 300.0, "Seguros e Licenças de Canteiro": 1200.0,
    "Transporte de Materiais e Pessoas": 2500.0, "Despesas de Escritório e Apoio": 800.0,
}

# --- DADOS MOCADOS CUB E SINAPI (para demonstração) ---
# Fonte: Dados fictícios com base em valores de mercado aproximados
CUB_DATA = {
    "AC": {"R-16": 2800, "P-8": 2600, "COMERCIAL": 3100},
    "SP": {"R-16": 4500, "P-8": 4200, "COMERCIAL": 5100},
    "RJ": {"R-16": 4700, "P-8": 4400, "COMERCIAL": 5300},
    "MG": {"R-16": 3900, "P-8": 3700, "COMERCIAL": 4300},
    "RS": {"R-16": 3800, "P-8": 3600, "COMERCIAL": 4200},
}
# --- FIM DADOS MOCADOS ---


# --- FUNÇÕES AUXILIARES ---
def fmt_br(valor):
    """
    Formata um valor numérico para a moeda brasileira (R$) de forma independente do locale.
    """
    if pd.isna(valor) or valor is None: return "0,00"
    s = f"{valor:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def render_metric_card(title, value, color="#31708f"):
    return f"""<div style="background-color:{color}; border-radius:6px; padding:15px; text-align:center; height:100%;"><div style="color:#fff; font-size:16px; margin-bottom:4px;">{title}</div><div style="color:#fff; font-size:24px; font-weight:bold;">{value}</div></div>"""

def init_storage(path):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f: json.dump([], f, ensure_ascii=False, indent=4)

def load_json(path):
    init_storage(path);
    with open(path, "r", encoding="utf-8") as f: return json.load(f)

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

def save_to_historico(info, tipo_custo):
    path = HISTORICO_DIRETO_PATH if tipo_custo == 'direto' else HISTORICO_INDIRETO_PATH
    session_key = 'etapas_percentuais' if tipo_custo == 'direto' else 'custos_indiretos_percentuais'
    historico = load_json(path)
    percentuais = {k: v['percentual'] for k, v in info[session_key].items()}
    nova_entrada = { "id": (max(p["id"] for p in historico) + 1) if historico else 1, "nome": info["nome"],
        "data": datetime.now().strftime("%Y-%m-%d"), "percentuais": percentuais }
    historico.append(nova_entrada)
    save_json(historico, path)
    st.toast(f"Custos {tipo_custo} de '{info['nome']}' arquivados no histórico!", icon="📚")

def handle_percentage_redistribution(session_key, constants_dict):
    previous_key = f"previous_{session_key}"
    if previous_key not in st.session_state: st.session_state[previous_key] = {k: v.copy() for k, v in st.session_state[session_key].items()}
    current, previous = st.session_state[session_key], st.session_state[previous_key]
    if current == previous: return
    changed_item_key = next((k for k, v in current.items() if v['percentual'] != previous.get(k, {}).get('percentual')), None)
    if not changed_item_key: return
    st.session_state.redistribution_occured = True
    delta = current[changed_item_key]['percentual'] - previous[changed_item_key]['percentual']
    total_others = sum(v['percentual'] for k, v in previous.items() if k != changed_item_key)
    if total_others > 0:
        for item, values in current.items():
            if item != changed_item_key:
                min_val, _, max_val = constants_dict[item]
                proportion = previous[item]['percentual'] / total_others
                new_percent = values['percentual'] - (delta * proportion)
                current[item]['percentual'] = max(min_val, min(new_percent, max_val))
    st.session_state[previous_key] = {k: v.copy() for k, v in current.items()}; st.rerun()

def render_sidebar(form_key):
    st.sidebar.title("Estudo de Viabilidade")
    st.sidebar.divider()
    
    # Seção para carregar/editar projetos
    if "projeto_info" in st.session_state:
        info = st.session_state.projeto_info
        st.sidebar.subheader(f"Projeto: {info['nome']}")
        with st.sidebar.expander("📝 Dados Gerais do Projeto"):
            with st.form(key=f"edit_form_sidebar_{form_key}"):
                info['nome'] = st.text_input("Nome", value=info['nome'])
                info['area_terreno'] = st.number_input("Área Terreno (m²)", value=info['area_terreno'], format="%.2f")
                info['area_privativa'] = st.number_input("Área Privativa (m²)", value=info['area_privativa'], format="%.2f")
                info['num_unidades'] = st.number_input("Unidades", value=info['num_unidades'], step=1)
                st.form_submit_button("Atualizar")
        with st.sidebar.expander("📈 Configurações de Mercado"):
                custos_config = info.get('custos_config', {})
                custos_config['preco_medio_venda_m2'] = st.number_input("Preço Médio Venda (R$/m² privativo)", min_value=0.0, value=custos_config.get('preco_medio_venda_m2', 10000.0), format="%.2f")
                info['custos_config'] = custos_config
        
        # --- NOVO PAINEL CUB/SINAPI ---
        with st.sidebar.expander("📊 Custo de Construção (CUB/SINAPI)"):
            st.markdown("<p style='font-size: 14px; text-align: left;'>Selecione uma referência para o custo de construção.</p>", unsafe_allow_html=True)
            
            estado = st.selectbox("Estado:", list(CUB_DATA.keys()), key=f"cub_estado_{form_key}")
            padrao = st.selectbox("Padrão:", list(CUB_DATA.get(estado, {}).keys()), key=f"cub_padrao_{form_key}")

            if estado and padrao:
                cub_value = CUB_DATA[estado][padrao]
                st.info(f"O valor de referência para {estado} ({padrao}) é de R$ {fmt_br(cub_value)}/m².")
                
                # Botão para aplicar o valor
                if st.button(f"Usar R$ {fmt_br(cub_value)}/m²", use_container_width=True, key=f"apply_cub_{form_key}"):
                    info['custos_config']['custo_area_privativa'] = float(cub_value)
                    st.success("Custo de construção atualizado!")
                    st.experimental_rerun()
        # --- FIM NOVO PAINEL ---

        with st.sidebar.expander("💰 Configuração de Custos"):
            custos_config = info.get('custos_config', {})
            custos_config['custo_terreno_m2'] = st.number_input("Custo do Terreno por m² (R$)", min_value=0.0, value=custos_config.get('custo_terreno_m2', 2500.0), format="%.2f")
            
            # Campo de custo de construção agora se alinha com o CUB
            custos_config['custo_area_privativa'] = st.number_input(
                "Custo de Construção (R$/m² privativo)", 
                min_value=0.0, 
                value=custos_config.get('custo_area_privativa', 4500.0), 
                step=100.0, 
                format="%.2f"
            )
            info['custos_config'] = custos_config
        st.sidebar.divider()
        if st.sidebar.button("💾 Salvar Todas as Alterações", use_container_width=True, type="primary"):
            if 'etapas_percentuais' in st.session_state: info['etapas_percentuais'] = st.session_state.etapas_percentuais
            if 'custos_indiretos_percentuais' in st.session_state: info['custos_indiretos_percentuais'] = st.session_state.custos_indiretos_percentuais
            st.session_state.project_manager.save_project(st.session_state.projeto_info); st.sidebar.success("Projeto salvo com sucesso!")
        with st.sidebar.expander("📚 Arquivar no Histórico"):
            if st.button("Arquivar Custos Diretos", use_container_width=True):
                info['etapas_percentuais'] = st.session_state.etapas_percentuais; save_to_historico(info, 'direto')
            if st.button("Arquivar Custos Indiretos", use_container_width=True):
                info['custos_indiretos_percentuais'] = st.session_state.custos_indiretos_percentuais; save_to_historico(info, 'indireto')
        if st.sidebar.button("Mudar de Projeto", use_container_width=True):
            keys_to_delete = ["projeto_info", "pavimentos", "etapas_percentuais", "previous_etapas_percentuais", "custos_indiretos_percentuais", "previous_custos_indiretos_percentuais"]
            for key in keys_to_delete:
                if key in st.session_state: del st.session_state[key]
            st.switch_page("Início.py")

class ProjectManager:
    def __init__(self):
        self._projects_data = self._load_projects()

    def _load_projects(self):
        """Carrega todos os projetos do arquivo JSON."""
        if not os.path.exists(JSON_PATH):
            with open(JSON_PATH, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_projects(self):
        """Retorna a lista de projetos."""
        return self._projects_data

    def save_project(self, info):
        """Salva ou atualiza um projeto."""
        if info.get("id"):
            projs = [p if p["id"] != info["id"] else info for p in self._projects_data]
        else:
            pid = (max(p["id"] for p in self._projects_data) + 1) if self._projects_data else 1
            info["id"] = pid
            info["created_at"] = datetime.utcnow().isoformat()
            projs = self._projects_data + [info]
        self._projects_data = projs
        save_json(self._projects_data, JSON_PATH)

    def load_project(self, pid):
        """Carrega os dados de um projeto específico."""
        project_data = next((p for p in self._projects_data if p["id"] == pid), None)
        if not project_data:
            return None
        # Normaliza a estrutura de dados para o novo formato de dicionário
        if 'etapas_percentuais' in project_data and isinstance(list(project_data['etapas_percentuais'].values())[0], (int, float)):
            project_data['etapas_percentuais'] = {k: {"percentual": v, "fonte": "Manual"} for k, v in project_data['etapas_percentuais'].items()}
        if 'custos_indiretos_percentuais' in project_data and isinstance(list(project_data['custos_indiretos_percentuais'].values())[0], (int, float)):
            project_data['custos_indiretos_percentuais'] = {k: {"percentual": v, "fonte": "Manual"} for k, v in project_data['custos_indiretos_percentuais'].items()}
        if 'unidades' not in project_data:
            project_data['unidades'] = []
        return project_data

    def delete_project(self, pid):
        """Exclui um projeto."""
        self._projects_data = [p for p in self._projects_data if p["id"] != pid]
        save_json(self._projects_data, JSON_PATH)

def init_session_state_vars(info):
    if 'pavimentos' not in st.session_state:
        st.session_state.pavimentos = [p.copy() for p in info.get('pavimentos', [DEFAULT_PAVIMENTO.copy()])]
    if 'unidades' not in st.session_state:
        st.session_state.unidades = [u.copy() for u in info.get('unidades', [])]
    if 'deleting_pav_index' not in st.session_state:
        st.session_state.deleting_pav_index = None
    if 'custos_indiretos_obra' not in st.session_state:
        st.session_state.custos_indiretos_obra = info.get('custos_indiretos_obra', {k: v for k, v in DEFAULT_CUSTOS_INDIRETOS_OBRA.items()})
    if 'duracao_obra' not in st.session_state:
        st.session_state.duracao_obra = info.get('duracao_obra', 12)
    if 'etapas_percentuais' not in st.session_state:
        etapas_salvas = info.get('etapas_percentuais', {})
        if etapas_salvas and isinstance(list(etapas_salvas.values())[0], (int, float)):
            st.session_state.etapas_percentuais = {etapa: {"percentual": val, "fonte": "Manual"} for etapa, val in etapas_salvas.items()}
        else:
            st.session_state.etapas_percentuais = {etapa: etapas_salvas.get(etapa, {"percentual": vals[1], "fonte": "Manual"}) for etapa, vals in ETAPAS_OBRA.items()}
    if 'custos_indiretos_percentuais' not in st.session_state:
        custos_salvos = info.get('custos_indiretos_percentuais', {})
        if custos_salvos and isinstance(list(custos_salvos.values())[0], (int, float)):
            st.session_state.custos_indiretos_percentuais = {item: {"percentual": val, "fonte": "Manual"} for item, val in custos_salvos.items()}
        else:
            st.session_state.custos_indiretos_percentuais = {item: custos_salvos.get(item, {"percentual": vals[1], "fonte": "Manual"}) for item, vals in DEFAULT_CUSTOS_INDIRETOS.items()}

def calcular_areas_e_custos(pavimentos_list, custos_config):
    pavimentos_df = pd.DataFrame(pavimentos_list)
    if pavimentos_df.empty:
        return 0, 0, 0, pd.DataFrame()

    custo_area_privativa = custos_config.get('custo_area_privativa', 4500.0)
    
    pavimentos_df["area_total"] = pavimentos_df["area"] * pavimentos_df["rep"]
    pavimentos_df["area_eq"] = pavimentos_df["area_total"] * pavimentos_df["coef"]
    pavimentos_df["area_constr"] = pavimentos_df.apply(lambda r: r["area_total"] if r["constr"] else 0.0, axis=1)
    pavimentos_df["custo_direto"] = pavimentos_df["area_eq"] * custo_area_privativa
    
    area_construida_total = pavimentos_df["area_constr"].sum()
    area_equivalente_total = pavimentos_df["area_eq"].sum()
    custo_direto_total = pavimentos_df["custo_direto"].sum()
    
    return area_construida_total, area_equivalente_total, custo_direto_total, pavimentos_df
