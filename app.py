import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io
import os
from config_db import load_data
from queries import query_eventos_esocial
import xml.dom.minidom

# Helper functions to pretty-print XML
def formatar_xml(xml_string):
    if not xml_string or not isinstance(xml_string, str) or xml_string.strip() == "":
        return ""
    try:
        dom = xml.dom.minidom.parseString(xml_string.strip())
        pretty_xml = dom.toprettyxml(indent="  ")
        lines = [line for line in pretty_xml.splitlines() if line.strip()]
        return "\n".join(lines)
    except Exception:
        return xml_string

@st.dialog("Visualizador de XML - eSocial", width="large")
def exibir_xml_modal(xml_content, id_evento):
    st.markdown(f"XML do Evento: `{id_evento}`")
    formatted = formatar_xml(xml_content)
    st.code(formatted, language="xml", line_numbers=True)
    if st.button("Fechar", use_container_width=True):
        st.rerun()


# 1. Configuração inicial da página
st.set_page_config(
    page_title="Dashboard eSocial - Portal de Monitoramento", 
    layout="wide", 
    page_icon="📊"
)

# --- ESTILIZAÇÃO PREMIUM (CSS CUSTOMIZADO) ---
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Configurações Globais de Fonte */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Container de Métricas Personalizado */
    .metric-container {
        display: flex;
        gap: 20px;
        margin-bottom: 25px;
    }
    
    .metric-card-premium {
        flex: 1;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 22px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .metric-card-premium:hover {
        transform: translateY(-3px);
        border-color: rgba(28, 131, 225, 0.4);
        box-shadow: 0 8px 24px rgba(28, 131, 225, 0.08);
        background: rgba(28, 131, 225, 0.02);
    }
    
    /* Banner de Alerta Crítico Pulsante */
    @keyframes pulse {
        0% { transform: scale(1); opacity: 0.96; }
        50% { transform: scale(1.005); opacity: 1; }
        100% { transform: scale(1); opacity: 0.96; }
    }
    
    .critical-alert-premium {
        background: linear-gradient(135deg, #ff4b4b 0%, #c0392b 100%);
        color: white;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 25px;
        text-align: center;
        font-weight: 600;
        font-size: 16px;
        box-shadow: 0 6px 20px rgba(255, 75, 75, 0.2);
        animation: pulse 3s infinite ease-in-out;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    
    /* Box de Detalhes do Evento */
    .detail-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        margin-top: 20px;
    }
    
    /* Separador Customizado */
    hr {
        margin: 2rem 0 !important;
        opacity: 0.15 !important;
    }
    
    /* Cursor pointer ao passar por cima das tabelas interativas */
    [data-testid="stDataFrame"] canvas {
        cursor: pointer !important;
    }
    
    /* Estilo do botão de download e de ações como ícone redondo e moderno */
    .stDownloadButton button,
    .st-key-btn_limpar_filtros button,
    .st-key-btn_atualizar_dados button {
        background-color: transparent !important;
        border: 1px solid rgba(30, 144, 255, 0.4) !important;
        color: #1e90ff !important;
        padding: 0 !important;
        width: 38px !important;
        height: 38px !important;
        min-width: 38px !important;
        max-width: 38px !important;
        min-height: 38px !important;
        max-height: 38px !important;
        border-radius: 50% !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    .stDownloadButton button:hover,
    .st-key-btn_limpar_filtros button:hover,
    .st-key-btn_atualizar_dados button:hover {
        background-color: rgba(30, 144, 255, 0.15) !important;
        border-color: #00bfff !important;
        color: #00bfff !important;
        transform: scale(1.08) !important;
    }
    
    /* Remover o espaçamento padrão que o Streamlit coloca dentro do botão de ícone */
    .stDownloadButton button div,
    .st-key-btn_limpar_filtros button div,
    .st-key-btn_atualizar_dados button div {
        margin: 0 !important;
    }
    
    /* Centralizar botões de ações no container */
    .st-key-btn_limpar_filtros,
    .st-key-btn_atualizar_dados {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
    }

    /* Estilo do Card de Filtros Avançados */
    .st-key-filter_card {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 0 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
    }
    
    .st-key-filter_card [data-testid="stVerticalBlock"] {
        gap: 0px !important;
    }
    
    /* Cabeçalho do Card */
    .filter-card-header {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 14px 20px;
        border-bottom: 1px solid #edf2f7;
        background-color: #ffffff;
        font-size: 15px;
        font-weight: 600;
        color: #2c3e50;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }
    
    .filter-header-icon {
        color: #3182ce;
        display: flex;
        align-items: center;
    }
    
    /* Corpo do Card */
    .st-key-filter_card_body {
        padding: 20px 20px 24px 20px !important;
        background-color: #ffffff !important;
    }
    
    .st-key-filter_card_body [data-testid="stVerticalBlock"] {
        gap: 18px !important;
    }
    
    /* Rótulos Customizados */
    .filter-label {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 11px;
        font-weight: 700;
        color: #718096;
        text-transform: uppercase;
        margin-bottom: 8px;
        letter-spacing: 0.5px;
    }
    
    .filter-label svg {
        color: #a0aec0;
    }
    
    /* Estilo dos inputs de texto, data e popovers */
    .st-key-filter_card_body input,
    .st-key-filter_card_body .stPopover button {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 6px !important;
        color: #2d3748 !important;
        font-size: 14px !important;
        height: 38px !important;
    }
    
    .st-key-filter_card_body .stPopover button {
        text-align: left !important;
        justify-content: space-between !important;
        font-weight: 400 !important;
        box-shadow: none !important;
    }
    
    /* Rodapé do Card */
    .st-key-filter_card_footer {
        background-color: #ffffff !important;
        border-top: 1px solid #edf2f7 !important;
        padding: 12px 20px !important;
        border-bottom-left-radius: 8px !important;
        border-bottom-right-radius: 8px !important;
    }
    
    /* Botões do Rodapé */
    .st-key-btn_limpar_filtros_new button {
        background-color: transparent !important;
        border: none !important;
        color: #4a5568 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        box-shadow: none !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        height: 38px !important;
        border-radius: 0 !important;
    }
    
    .st-key-btn_limpar_filtros_new button:hover {
        color: #1a202c !important;
        background-color: transparent !important;
        text-decoration: underline !important;
    }
    
    .st-key-btn_aplicar_buscar_new button {
        background-color: #2b6cb0 !important;
        border: 1px solid #2b6cb0 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        border-radius: 6px !important;
        padding: 0 16px !important;
        height: 38px !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
        transition: all 0.2s !important;
    }
    
    .st-key-btn_aplicar_buscar_new button:hover {
        background-color: #2b6cb0 !important;
        opacity: 0.9 !important;
        color: #ffffff !important;
        transform: translateY(-1px) !important;
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

# --- CABEÇALHO COM LOGOTIPO ---
if os.path.exists("logo_esocial.png"):
    st.image("logo_esocial.png", width=160)

st.title("Portal de Monitoramento - eSocial")
st.markdown("Auditoria inteligente de prazos, controle de SLA e diagnóstico rápido de erros de geração.")
st.divider()

df_eventos = load_data(query_eventos_esocial())

if not df_eventos.empty:
    
    # --- TRATAMENTO BÁSICO DOS DADOS ---
    if 'ID' in df_eventos.columns:
        df_eventos['ID'] = df_eventos['ID'].astype(str)
        
    df_eventos['CHAPA'] = df_eventos['CHAPA'].fillna('S/CHAPA')
    df_eventos['NOME_FUNCIONARIO'] = df_eventos['NOME_FUNCIONARIO'].fillna('NOME NÃO ENCONTRADO')
    df_eventos['DATAEVENTO'] = pd.to_datetime(df_eventos['DATAEVENTO'])
    
    # Tratamento da data de criação para o cálculo do SLA (Aging)
    if 'RECCREATEDON' in df_eventos.columns:
        df_eventos['RECCREATEDON'] = pd.to_datetime(df_eventos['RECCREATEDON'])
        df_eventos['DIAS_PENDENTES'] = (pd.Timestamp.now().normalize() - df_eventos['RECCREATEDON'].dt.normalize()).dt.days
        
        # Criação das faixas de tempo (SLA)
        bins = [-1, 5, 15, 30, 99999]
        labels = ['1. 0 a 5 dias', '2. 6 a 15 dias', '3. 16 a 30 dias', '4. Mais de 30 dias (Crítico)']
        df_eventos['SLA_FAIXA'] = pd.cut(df_eventos['DIAS_PENDENTES'], bins=bins, labels=labels)

    # Tratamento da Competência (MESCOMP/ANOCOMP) para eventos periódicos
    if 'MESCOMP' in df_eventos.columns and 'ANOCOMP' in df_eventos.columns:
        df_eventos['COMPETENCIA'] = df_eventos.apply(
            lambda r: f"{int(r['ANOCOMP'])}-{str(int(r['MESCOMP'])).zfill(2)}"
            if pd.notna(r['ANOCOMP']) and pd.notna(r['MESCOMP']) and int(r['ANOCOMP']) > 0
            else 'N/A',
            axis=1
        )
    else:
        df_eventos['COMPETENCIA'] = 'N/A'

    # Tratamento do Status
    mapa_status = {
        0: "0 - Pendente",
        1: "1 - Gerado",
        2: "2 - Erro na geração",
        3: "3 - Enviado",
        4: "4 - Aceito TAF",
        5: "5 - Erro na integração TAF",
        6: "6 - Rejeitado TAF",
        9: "9 - Rejeitado RET",
        10: "10 - Aceito RET",
        11: "11 - Excluído RET"
    }
    if 'STATUS' in df_eventos.columns:
        df_eventos['STATUS_EXIBICAO'] = df_eventos['STATUS'].map(mapa_status).fillna("Outros (" + df_eventos['STATUS'].astype(str) + ")")

    # Tratamento de Nomes dos Responsáveis
    logins_unicos = df_eventos['RESPONSAVEL'].dropna().unique()
    chapas_rh = []
    codigos_medicos = []
    
    for login in logins_unicos:
        login_str = str(login).strip()
        if login_str.startswith('SM.'):
            codigos_medicos.append(login_str.split('.')[1])
        elif '-' in login_str and login_str.split('-')[0].isdigit():
            coligada = login_str.split('-')[0]
            chapa = login_str.split('-')[1]
            chapas_rh.append(f"(CODCOLIGADA={coligada} AND CHAPA='{chapa}')")

    mapa_responsaveis = {}

    if chapas_rh:
        query_rh = f"SELECT CODCOLIGADA, CHAPA, NOME FROM PFUNC (NOLOCK) WHERE {' OR '.join(chapas_rh)}"
        df_rh = load_data(query_rh)
        if not df_rh.empty:
            for _, row in df_rh.iterrows():
                col = str(int(row['CODCOLIGADA']))
                chp = str(row['CHAPA']).strip()
                mapa_responsaveis[f"{col}-{chp}"] = row['NOME']

    if codigos_medicos:
        cods_formatados = "','".join(codigos_medicos)
        query_med = f"SELECT CODIGO, NOME FROM PPESSOA (NOLOCK) WHERE CODIGO IN ('{cods_formatados}')"
        df_med = load_data(query_med)
        if not df_med.empty:
            mapa_medicos = {str(row['CODIGO']).strip(): row['NOME'] for _, row in df_med.iterrows()}
            for cod in codigos_medicos:
                if cod in mapa_medicos:
                    mapa_responsaveis[f"SM.{cod}"] = mapa_medicos[cod]
                else:
                    try:
                        cod_int = str(int(cod))
                        if cod_int in mapa_medicos:
                            mapa_responsaveis[f"SM.{cod}"] = mapa_medicos[cod_int]
                    except ValueError:
                        pass

    def formatar_responsavel(login):
        if pd.isna(login) or str(login).strip() == "":
            return "NÃO IDENTIFICADO"
        
        login = str(login).strip()
        if login in mapa_responsaveis:
            nome = mapa_responsaveis[login]
            if login.startswith('SM.'):
                return f"Médico: {nome} | {login}"
            else:
                return f"{nome} | {login}" 
        return login

    df_eventos['RESP_EXIBICAO'] = df_eventos['RESPONSAVEL'].apply(formatar_responsavel)

    min_date = df_eventos['DATAEVENTO'].min().date() if not pd.isna(df_eventos['DATAEVENTO'].min()) else datetime.today().date()
    max_date = df_eventos['DATAEVENTO'].max().date() if not pd.isna(df_eventos['DATAEVENTO'].max()) else datetime.today().date()
    
    if "filtro_data_ini" not in st.session_state:
        st.session_state["filtro_data_ini"] = min_date
    if "filtro_data_fim" not in st.session_state:
        st.session_state["filtro_data_fim"] = max_date
    if "search_query_val" not in st.session_state:
        st.session_state["search_query_val"] = ""

    def limpar_filtros_callback():
        for k in list(st.session_state.keys()):
            if k.startswith(("chk_col_", "chk_stat_", "chk_tipo_", "chk_comp_", "chk_sla_", "chk_resp_")):
                st.session_state[k] = False
        st.session_state["filtro_data_ini"] = min_date
        st.session_state["filtro_data_fim"] = max_date
        st.session_state["search_query_val"] = ""

    # =========================================================================
    # --- PAINEL DE FILTROS NA TELA PRINCIPAL (SEM BARRA LATERAL) ---
    # =========================================================================
    header_html = """
    <div class="filter-card-header">
        <svg class="filter-header-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="4" y1="21" x2="4" y2="14"></line>
            <line x1="4" y1="10" x2="4" y2="3"></line>
            <line x1="12" y1="21" x2="12" y2="12"></line>
            <line x1="12" y1="8" x2="12" y2="3"></line>
            <line x1="20" y1="21" x2="20" y2="16"></line>
            <line x1="20" y1="12" x2="20" y2="3"></line>
            <line x1="1" y1="14" x2="7" y2="14"></line>
            <line x1="9" y1="8" x2="15" y2="8"></line>
            <line x1="17" y1="16" x2="23" y2="16"></line>
        </svg>
        <span>Filtros e Pesquisa Avançada</span>
    </div>
    """

    with st.container(border=True, key="filter_card"):
        # Header
        st.markdown(header_html, unsafe_allow_html=True)
        
        # Body
        with st.container(key="filter_card_body"):
            # Row 1: Busca Rápida + Período Analisado
            col_r1_a, col_r1_b = st.columns([1, 1.2])
            
            with col_r1_a:
                st.markdown(
                    """
                    <div class="filter-label">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                        <span>Busca Rápida</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                search_query = st.text_input("", placeholder="Nome, Chapa ou ID...", key="search_query_val", label_visibility="collapsed")
                
            with col_r1_b:
                st.markdown(
                    """
                    <div class="filter-label">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                        <span>Período Analisado</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                col_date1, col_ate, col_date2 = st.columns([10, 1, 10])
                with col_date1:
                    data_ini = st.date_input("", key="filtro_data_ini", min_value=min_date, max_value=max_date, label_visibility="collapsed")
                with col_ate:
                    st.markdown("<div style='text-align: center; line-height: 38px; color: #94a3b8; font-size: 14px;'>até</div>", unsafe_allow_html=True)
                with col_date2:
                    data_fim = st.date_input("", key="filtro_data_fim", min_value=min_date, max_value=max_date, label_visibility="collapsed")

            # Row 2: Coligada, Status, Tipo de Evento, Competência, Idade SLA, Responsável
            col_c1, col_c2, col_c3, col_c4, col_c5, col_c6 = st.columns(6)
            
            with col_c1:
                st.markdown(
                    """
                    <div class="filter-label">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"></rect><line x1="9" y1="22" x2="9" y2="16"></line><line x1="15" y1="22" x2="15" y2="16"></line><line x1="9" y1="16" x2="15" y2="16"></line><circle cx="8" cy="6" r="0.5"></circle><circle cx="16" cy="6" r="0.5"></circle><circle cx="8" cy="10" r="0.5"></circle><circle cx="16" cy="10" r="0.5"></circle><circle cx="12" cy="10" r="0.5"></circle><circle cx="12" cy="6" r="0.5"></circle></svg>
                        <span>Coligada</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                coligadas_opcoes = sorted(df_eventos['NOME_COLIGADA'].dropna().unique())
                sel_coligadas = [op for op in coligadas_opcoes if st.session_state.get(f"chk_col_{op}", False)]
                label_col = f"Coligadas ({len(sel_coligadas)})" if sel_coligadas else "Todas as Coligadas"
                coligadas = []
                with st.popover(label_col, use_container_width=True):
                    for op in coligadas_opcoes:
                        if st.checkbox(op, key=f"chk_col_{op}"):
                            coligadas.append(op)
                            
            with col_c2:
                st.markdown(
                    """
                    <div class="filter-label">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>
                        <span>Status</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                status_opcoes = sorted(df_eventos['STATUS_EXIBICAO'].dropna().unique()) if 'STATUS_EXIBICAO' in df_eventos.columns else []
                sel_status = [op for op in status_opcoes if st.session_state.get(f"chk_stat_{op}", False)]
                label_stat = f"Status ({len(sel_status)})" if sel_status else "Todos os Status"
                status_selecionados = []
                with st.popover(label_stat, use_container_width=True):
                    for op in status_opcoes:
                        if st.checkbox(op, key=f"chk_stat_{op}"):
                            status_selecionados.append(op)
                            
            with col_c3:
                st.markdown(
                    """
                    <div class="filter-label">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><circle cx="7" cy="7" r="0.5"></circle></svg>
                        <span>Tipo de Evento</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                tipos_opcoes = sorted(df_eventos['TIPOEVENTO'].dropna().unique())
                sel_tipos = [op for op in tipos_opcoes if st.session_state.get(f"chk_tipo_{op}", False)]
                label_tipo = f"Tipos ({len(sel_tipos)})" if sel_tipos else "Todos os Tipos"
                tipos_evento = []
                with st.popover(label_tipo, use_container_width=True):
                    for op in tipos_opcoes:
                        if st.checkbox(op, key=f"chk_tipo_{op}"):
                            tipos_evento.append(op)
                            
            with col_c4:
                st.markdown(
                    """
                    <div class="filter-label">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                        <span>Competência</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                comp_opcoes = sorted(df_eventos['COMPETENCIA'].dropna().unique())
                sel_comps = [op for op in comp_opcoes if st.session_state.get(f"chk_comp_{op}", False)]
                label_comp = f"Competências ({len(sel_comps)})" if sel_comps else "Todas as Competências"
                competencias_selecionadas = []
                with st.popover(label_comp, use_container_width=True):
                    for op in comp_opcoes:
                        if st.checkbox(op, key=f"chk_comp_{op}"):
                            competencias_selecionadas.append(op)
                            
            with col_c5:
                st.markdown(
                    """
                    <div class="filter-label">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 2h14"></path><path d="M5 22h14"></path><path d="M19 2v4c0 1.38-.5 2-2 3l-5 3 5 3c1.5 1 2 1.62 2 3v4"></path><path d="M5 2v4c0 1.38.5 2 2 3l5 3-5 3c-1.5 1-2 1.62-2 3v4"></path></svg>
                        <span>Idade SLA</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                sla_opcoes = sorted([str(x) for x in df_eventos['SLA_FAIXA'].dropna().unique()]) if 'SLA_FAIXA' in df_eventos.columns else []
                sel_sla = [op for op in sla_opcoes if st.session_state.get(f"chk_sla_{op}", False)]
                label_sla = f"SLA ({len(sel_sla)})" if sel_sla else "Todas as Faixas"
                sla_selecionados = []
                with st.popover(label_sla, use_container_width=True):
                    for op in sla_opcoes:
                        if st.checkbox(op, key=f"chk_sla_{op}"):
                            sla_selecionados.append(op)

            with col_c6:
                st.markdown(
                    """
                    <div class="filter-label">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                        <span>Responsável</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                resp_opcoes = sorted(df_eventos['RESP_EXIBICAO'].unique())
                sel_resp = [op for op in resp_opcoes if st.session_state.get(f"chk_resp_{op}", False)]
                label_resp = f"Resp. ({len(sel_resp)})" if sel_resp else "Todos os Responsáveis"
                responsaveis = []
                with st.popover(label_resp, use_container_width=True):
                    for op in resp_opcoes:
                        if st.checkbox(op, key=f"chk_resp_{op}"):
                            responsaveis.append(op)


        # Footer
        with st.container(key="filter_card_footer"):
            col_f_left, col_f_clear, col_f_apply = st.columns([5, 1, 1.2])
            with col_f_clear:
                st.button("Limpar Filtros", icon=":material/delete:", key="btn_limpar_filtros_new", on_click=limpar_filtros_callback, use_container_width=True)
            with col_f_apply:
                if st.button("Aplicar e Buscar", icon=":material/sync:", key="btn_aplicar_buscar_new", use_container_width=True):
                    st.rerun()

    # --- APLICAR FILTRAGEM ---
    df_filtrado = df_eventos.copy()
    if data_ini and data_fim:
        df_filtrado = df_filtrado[(df_filtrado['DATAEVENTO'].dt.date >= data_ini) & (df_filtrado['DATAEVENTO'].dt.date <= data_fim)]
    if coligadas:
        df_filtrado = df_filtrado[df_filtrado['NOME_COLIGADA'].isin(coligadas)]
    if 'STATUS_EXIBICAO' in df_filtrado.columns and status_selecionados:
        df_filtrado = df_filtrado[df_filtrado['STATUS_EXIBICAO'].isin(status_selecionados)]
    if tipos_evento:
        df_filtrado = df_filtrado[df_filtrado['TIPOEVENTO'].isin(tipos_evento)]
    if competencias_selecionadas:
        df_filtrado = df_filtrado[df_filtrado['COMPETENCIA'].isin(competencias_selecionadas)]
    if 'SLA_FAIXA' in df_filtrado.columns and sla_selecionados:
        df_filtrado = df_filtrado[df_filtrado['SLA_FAIXA'].isin(sla_selecionados)]
    if responsaveis:
        df_filtrado = df_filtrado[df_filtrado['RESP_EXIBICAO'].isin(responsaveis)]
    if search_query:
        query_s = search_query.strip().lower()
        df_filtrado = df_filtrado[
            df_filtrado['NOME_FUNCIONARIO'].str.lower().str.contains(query_s, na=False) |
            df_filtrado['CHAPA'].str.lower().str.contains(query_s, na=False) |
            df_filtrado['ID'].str.lower().str.contains(query_s, na=False)
        ]

    # =========================================================================
    # --- PAINEL DE ALERTAS CRÍTICOS (ANTIMULTAS) ---
    # =========================================================================
    eventos_criticos = df_filtrado[(df_filtrado['TIPOEVENTO'].isin(['S-2200', 'S-2210'])) & (df_filtrado['FORA_DO_PRAZO'] == 'S')]
    qtd_criticos = len(eventos_criticos)
    
    if qtd_criticos > 0:
        st.markdown(
            f"""
            <div class="critical-alert-premium">
                ⚠️ ATENÇÃO: Existem {qtd_criticos} eventos CRÍTICOS (Admissão / Acidente de Trabalho) em atraso! Risco altíssimo de autuação.
            </div>
            """, 
            unsafe_allow_html=True
        )

    # --- NAVEGAÇÃO POR ABAS (TABS) ---
    tab_metricas, tab_erros = st.tabs([
        "📊 Indicadores e Métricas", 
        "⚠️ Central de Inconsistências (Erros)"
    ])

    # =========================================================================
    # --- ABA 1: INDICADORES E MÉTRICAS ---
    # =========================================================================
    with tab_metricas:
        
        # KPIs Gerais
        total_pendentes = len(df_filtrado)
        total_atrasados = len(df_filtrado[df_filtrado['FORA_DO_PRAZO'] == 'S'])
        taxa_atraso = f"{(total_atrasados/total_pendentes*100):.1f}%" if total_pendentes > 0 else "0%"
        
        cor_borda_atraso = "#ff4b4b" if total_atrasados > 0 else "#21c354"
        cor_fundo_atraso = "rgba(255, 75, 75, 0.08)" if total_atrasados > 0 else "rgba(33, 195, 84, 0.08)"

        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-card-premium" style="border-left: 6px solid #1c83e1;">
                    <p style="margin: 0; font-size: 14px; opacity: 0.7; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">Eventos Pendentes</p>
                    <h2 style="margin: 5px 0 0 0; font-size: 38px; font-weight: 700;">{total_pendentes}</h2>
                </div>
                <div class="metric-card-premium" style="border-left: 6px solid {cor_borda_atraso}; background: {cor_fundo_atraso};">
                    <p style="margin: 0; font-size: 14px; opacity: 0.7; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">Fora do Prazo (Atrasados)</p>
                    <h2 style="margin: 5px 0 0 0; font-size: 38px; font-weight: 700; color: #ff4b4b;">{total_atrasados}</h2>
                </div>
                <div class="metric-card-premium" style="border-left: 6px solid #ffa421;">
                    <p style="margin: 0; font-size: 14px; opacity: 0.7; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">Taxa Geral de Atraso</p>
                    <h2 style="margin: 5px 0 0 0; font-size: 38px; font-weight: 700; color: #ffa421;">{taxa_atraso}</h2>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.divider()

        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.subheader("Top 10 Responsáveis por Pendências")
            if not df_filtrado.empty:
                df_resp = df_filtrado['RESP_EXIBICAO'].value_counts().head(10).reset_index()
                df_resp.columns = ['Responsável', 'Quantidade']
                df_resp = df_resp.sort_values(by='Quantidade', ascending=True)
                fig_resp = px.bar(df_resp, x='Quantidade', y='Responsável', orientation='h', 
                                  color='Quantidade', color_continuous_scale='Reds',
                                  template="plotly_dark")
                fig_resp.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=350)
                st.plotly_chart(fig_resp, use_container_width=True)
            else:
                st.info("Sem dados para exibir gráficos.")

        with col_graf2:
            st.subheader("Pendências por Tipo de Evento")
            if not df_filtrado.empty:
                df_tipo = df_filtrado['TIPOEVENTO'].value_counts().reset_index()
                df_tipo.columns = ['Tipo de Evento', 'Quantidade']
                fig_tipo = px.pie(df_tipo, values='Quantidade', names='Tipo de Evento', hole=0.4,
                                  template="plotly_dark")
                fig_tipo.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=350)
                st.plotly_chart(fig_tipo, use_container_width=True)
            else:
                st.info("Sem dados para exibir gráficos.")

        st.divider()

        # Gráficos Linha 2
        col_graf3, col_graf4 = st.columns(2)
        with col_graf3:
            st.subheader("Mapa de Árvore (Coligada > Status > Evento)")
            if not df_filtrado.empty:
                df_filtrado['CONTAGEM_TREEMAP'] = 1
                fig_tree = px.treemap(
                    df_filtrado, 
                    path=[px.Constant("Empresa"), 'NOME_COLIGADA', 'STATUS_EXIBICAO', 'TIPOEVENTO'], 
                    values='CONTAGEM_TREEMAP',
                    color='NOME_COLIGADA',
                    template="plotly_dark"
                )
                fig_tree.update_traces(root_color="lightgrey")
                fig_tree.update_layout(margin=dict(t=20, l=10, r=10, b=10), height=350)
                st.plotly_chart(fig_tree, use_container_width=True)
            else:
                st.info("Sem dados para exibir.")

        with col_graf4:
            st.subheader("Termômetro de Idade (SLA)")
            if not df_filtrado.empty and 'SLA_FAIXA' in df_filtrado.columns:
                df_sla = df_filtrado['SLA_FAIXA'].value_counts().reset_index()
                df_sla.columns = ['Faixa de Tempo', 'Quantidade']
                df_sla = df_sla.sort_values('Faixa de Tempo')
                
                cores_sla = ['#2ecc71', '#f1c40f', '#e67e22', '#e74c3c']
                fig_sla = px.bar(
                    df_sla, 
                    x='Faixa de Tempo', 
                    y='Quantidade', 
                    color='Faixa de Tempo', 
                    color_discrete_sequence=cores_sla,
                    template="plotly_dark"
                )
                fig_sla.update_layout(showlegend=False, margin=dict(t=20, b=20, l=10, r=10), height=350)
                st.plotly_chart(fig_sla, use_container_width=True)
            else:
                st.info("Sem dados de SLA disponíveis.")

        st.divider()

        # Gráfico Linha 3 (Timeline)
        st.subheader("Evolução Histórica de Pendências")
        if not df_filtrado.empty:
            df_timeline = df_filtrado.groupby(['ANO_EVENTO', 'MES_EVENTO']).size().reset_index(name='Quantidade')
            df_timeline['PERIODO'] = df_timeline['ANO_EVENTO'].astype(str) + '-' + df_timeline['MES_EVENTO'].astype(str).str.zfill(2)
            df_timeline = df_timeline.sort_values(by=['ANO_EVENTO', 'MES_EVENTO'])
            
            fig_time = px.line(df_timeline, x='PERIODO', y='Quantidade', markers=True, 
                               labels={'PERIODO': 'Mês de Referência', 'Quantidade': 'Eventos Pendentes'},
                               template="plotly_dark")
            fig_time.update_traces(line_color='#2E86C1', marker=dict(size=8, color='#E74C3C'))
            fig_time.update_layout(height=280)
            st.plotly_chart(fig_time, use_container_width=True)

        st.divider()

        # --- DETALHAMENTO DOS EVENTOS ---
        colunas_tabela = ['ID', 'NOME_COLIGADA', 'CHAPA', 'NOME_FUNCIONARIO', 'TIPOEVENTO', 'COMPETENCIA', 'DATAEVENTO', 'STATUS_EXIBICAO', 'RESP_EXIBICAO', 'SLA_FAIXA', 'FORA_DO_PRAZO']
        
        # Gerar o buffer do Excel para o download antes da tabela para exibirmos o botão acima dela
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_filtrado[colunas_tabela].to_excel(writer, index=False, sheet_name='Pendencias_eSocial')

        col_tit, col_down = st.columns([15, 1])
        with col_tit:
            st.subheader("📋 Detalhamento dos Eventos")
            st.markdown("Clique na lupa 🔍 para abrir o XML correspondente ou selecione a linha para ver a Ficha Técnica abaixo.")
        with col_down:
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            st.download_button(
                label="",
                data=buffer.getvalue(),
                file_name="relatorio_pendencias_esocial.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Baixar tabela atual filtrada em Excel (.xlsx)",
                key="btn_download_metricas",
                icon=":material/download:"
            )

        df_render = df_filtrado[colunas_tabela].copy()
        df_render.insert(0, '🔍', '🔍')

        # Interatividade via on_select
        event_selection = st.dataframe(
            df_render,
            use_container_width=True,
            hide_index=True,
            selection_mode=["single-row", "single-cell"],
            on_select="rerun",
            key="table_metricas",
            column_config={
                "🔍": st.column_config.TextColumn(" ", width="small"),
                "ID": st.column_config.TextColumn("ID Evento", width="medium"),
                "NOME_COLIGADA": "Coligada",
                "CHAPA": "Chapa",
                "NOME_FUNCIONARIO": "Funcionário",
                "TIPOEVENTO": "Evento",
                "COMPETENCIA": "Competência",
                "DATAEVENTO": st.column_config.DateColumn("Data Evento", format="DD/MM/YYYY"),
                "STATUS_EXIBICAO": "Status",
                "RESP_EXIBICAO": "Responsável",
                "SLA_FAIXA": "Faixa SLA",
                "FORA_DO_PRAZO": st.column_config.TextColumn("Atrasado", width="small")
            }
        )

        # Tratar seleção de linhas e células
        selected_rows = []
        selected_cells = []
        if event_selection:
            if hasattr(event_selection, "selection"):
                selected_rows = event_selection.selection.rows
                selected_cells = event_selection.selection.cells
            elif isinstance(event_selection, dict):
                selection = event_selection.get("selection", {})
                selected_rows = selection.get("rows", [])
                selected_cells = selection.get("cells", [])

        # Para mostrar a Ficha Técnica (ao clicar em qualquer parte da linha ou célula)
        selected_row_idx = None
        if len(selected_rows) > 0:
            selected_row_idx = selected_rows[0]
        elif len(selected_cells) > 0:
            cell = selected_cells[0]
            if isinstance(cell, (tuple, list)) and len(cell) > 0:
                selected_row_idx = cell[0]
            elif isinstance(cell, dict):
                selected_row_idx = cell.get("row")

        # Para abrir o XML (APENAS se clicar na coluna da lupa 🔍)
        should_open_modal = False
        if len(selected_cells) > 0:
            cell = selected_cells[0]
            if isinstance(cell, (tuple, list)) and len(cell) == 2:
                col_identifier = cell[1]
                if col_identifier == "🔍" or col_identifier == 1:
                    should_open_modal = True
            elif isinstance(cell, dict):
                col_identifier = cell.get("column")
                if col_identifier == "🔍" or col_identifier == 1:
                    should_open_modal = True

        if selected_row_idx is not None:
            selected_id = df_render.iloc[selected_row_idx]['ID']
            selected_row = df_filtrado[df_filtrado['ID'] == selected_id].iloc[0]

            # Abrir modal automaticamente se clicar na lupa e ainda não foi aberto para este ID
            if should_open_modal and st.session_state.get("modal_aberto_id_metricas") != selected_id:
                st.session_state["modal_aberto_id_metricas"] = selected_id
                if 'MENSAGEM' in selected_row and pd.notna(selected_row['MENSAGEM']) and str(selected_row['MENSAGEM']).strip() != "":
                    exibir_xml_modal(selected_row['MENSAGEM'], selected_id)
            elif not should_open_modal:
                # Se clicar em outra coluna, reseta o trigger do modal para o ID selecionado
                st.session_state["modal_aberto_id_metricas"] = None

            st.markdown("---")
            st.markdown(f"### 🔍 Ficha Técnica do Evento: `{selected_id}`")
            
            # Detalhamento Visual
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Empresa/Coligada:** {selected_row['NOME_COLIGADA']}")
                st.markdown(f"**Chapa do Funcionário:** `{selected_row['CHAPA']}`")
                st.markdown(f"**Nome do Funcionário:** {selected_row['NOME_FUNCIONARIO']}")
            with col2:
                st.markdown(f"**Tipo de Evento:** `{selected_row['TIPOEVENTO']}`")
                st.markdown(f"**Data do Evento:** {selected_row['DATAEVENTO'].strftime('%d/%m/%Y') if pd.notna(selected_row['DATAEVENTO']) else 'N/A'}")
                st.markdown(f"**Competência:** `{selected_row['COMPETENCIA']}`")
            with col3:
                st.markdown(f"**Status de Integração:** `{selected_row['STATUS_EXIBICAO']}`")
                st.markdown(f"**Criado por:** {selected_row['RESP_EXIBICAO']}")
                st.markdown(f"**Tempo de Pendência:** `{selected_row['DIAS_PENDENTES']} dias` ({selected_row['SLA_FAIXA']})")

            # Erro de geração (LOGGERACAO) formatado
            if 'LOGGERACAO' in selected_row and pd.notna(selected_row['LOGGERACAO']) and str(selected_row['LOGGERACAO']).strip() != "":
                st.markdown("#### ❌ Inconsistências de Geração")
                st.error(selected_row['LOGGERACAO'])
            else:
                st.success("✅ Nenhum erro de validação local registrado na coluna Loggeração.")

            # XML não é mais exibido em botões/expansores abaixo da tabela
            if not ('MENSAGEM' in selected_row and pd.notna(selected_row['MENSAGEM']) and str(selected_row['MENSAGEM']).strip() != ""):
                st.info("ℹ️ XML do evento não disponível.")
            st.markdown("---")
        else:
            st.session_state["modal_aberto_id_metricas"] = None
            st.info("💡 Selecione uma linha na tabela acima para visualizar a ficha técnica e clique em 🔍 para abrir o XML correspondente.")

    # =========================================================================
    # --- ABA 2: CENTRAL DE INCONSISTÊNCIAS ---
    # =========================================================================
    with tab_erros:
        # Filtrar apenas dados com erro em LOGGERACAO
        df_erros = df_filtrado[
            df_filtrado['LOGGERACAO'].notna() & 
            (df_filtrado['LOGGERACAO'].astype(str).str.strip() != "") & 
            (df_filtrado['LOGGERACAO'].astype(str).str.strip().str.lower() != "none")
        ].copy()

        total_erros = len(df_erros)
        taxa_erros = f"{(total_erros/total_pendentes*100):.1f}%" if total_pendentes > 0 else "0%"

        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-card-premium" style="border-left: 6px solid #e74c3c; background: rgba(231, 76, 60, 0.08);">
                    <p style="margin: 0; font-size: 14px; opacity: 0.7; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">Eventos Inconsistentes (Com Erro)</p>
                    <h2 style="margin: 5px 0 0 0; font-size: 38px; font-weight: 700; color: #e74c3c;">{total_erros}</h2>
                </div>
                <div class="metric-card-premium" style="border-left: 6px solid #ffa421;">
                    <p style="margin: 0; font-size: 14px; opacity: 0.7; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">Representação sobre Pendências</p>
                    <h2 style="margin: 5px 0 0 0; font-size: 38px; font-weight: 700; color: #ffa421;">{taxa_erros}</h2>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.divider()

        if total_erros > 0:
            colunas_erros = ['ID', 'NOME_COLIGADA', 'CHAPA', 'NOME_FUNCIONARIO', 'TIPOEVENTO', 'COMPETENCIA', 'LOGGERACAO']
            
            # Gerar buffer para download
            buffer_err = io.BytesIO()
            with pd.ExcelWriter(buffer_err, engine='openpyxl') as writer:
                df_erros[colunas_erros].to_excel(writer, index=False, sheet_name='Inconsistencias_eSocial')

            col_tit_err, col_down_err = st.columns([15, 1])
            with col_tit_err:
                st.markdown("📋 **Lista de Eventos Rejeitados na Geração Local**")
                st.markdown("Clique na lupa 🔍 para abrir o XML correspondente ou selecione a linha para ver o diagnóstico abaixo.")
            with col_down_err:
                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                st.download_button(
                    label="",
                    data=buffer_err.getvalue(),
                    file_name="relatorio_inconsistencias_esocial.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Baixar tabela atual de inconsistências filtrada em Excel (.xlsx)",
                    key="btn_download_erros",
                    icon=":material/download:"
                )

            df_erros_render = df_erros[colunas_erros].copy()
            df_erros_render.insert(0, '🔍', '🔍')
            
            # Tabela de Erros Interativa
            erros_selection = st.dataframe(
                df_erros_render,
                use_container_width=True,
                hide_index=True,
                selection_mode=["single-row", "single-cell"],
                on_select="rerun",
                key="table_erros",
                column_config={
                    "🔍": st.column_config.TextColumn(" ", width="small"),
                    "ID": st.column_config.TextColumn("ID Evento", width="medium"),
                    "NOME_COLIGADA": "Coligada",
                    "CHAPA": "Chapa",
                    "NOME_FUNCIONARIO": "Funcionário",
                    "TIPOEVENTO": "Evento",
                    "COMPETENCIA": "Competência",
                    "LOGGERACAO": st.column_config.TextColumn("Erro de Validação (Loggeração)", width="large")
                }
            )

            # Tratar seleção de erros e células
            selected_error_rows = []
            selected_error_cells = []
            if erros_selection:
                if hasattr(erros_selection, "selection"):
                    selected_error_rows = erros_selection.selection.rows
                    selected_error_cells = erros_selection.selection.cells
                elif isinstance(erros_selection, dict):
                    selection = erros_selection.get("selection", {})
                    selected_error_rows = selection.get("rows", [])
                    selected_error_cells = selection.get("cells", [])

            # Para mostrar o Diagnóstico (ao clicar em qualquer parte da linha ou célula)
            selected_err_row_idx = None
            if len(selected_error_rows) > 0:
                selected_err_row_idx = selected_error_rows[0]
            elif len(selected_error_cells) > 0:
                cell = selected_error_cells[0]
                if isinstance(cell, (tuple, list)) and len(cell) > 0:
                    selected_err_row_idx = cell[0]
                elif isinstance(cell, dict):
                    selected_err_row_idx = cell.get("row")

            # Para abrir o XML (APENAS se clicar na coluna da lupa 🔍)
            should_open_modal_err = False
            if len(selected_error_cells) > 0:
                cell = selected_error_cells[0]
                if isinstance(cell, (tuple, list)) and len(cell) == 2:
                    col_identifier = cell[1]
                    if col_identifier == "🔍" or col_identifier == 1:
                        should_open_modal_err = True
                elif isinstance(cell, dict):
                    col_identifier = cell.get("column")
                    if col_identifier == "🔍" or col_identifier == 1:
                        should_open_modal_err = True

            if selected_err_row_idx is not None:
                selected_err_id = df_erros_render.iloc[selected_err_row_idx]['ID']
                selected_err_row = df_erros[df_erros['ID'] == selected_err_id].iloc[0]

                # Abrir modal automaticamente se clicar na lupa e ainda não foi aberto para este ID
                if should_open_modal_err and st.session_state.get("modal_aberto_id_erros") != selected_err_id:
                    st.session_state["modal_aberto_id_erros"] = selected_err_id
                    if 'MENSAGEM' in selected_err_row and pd.notna(selected_err_row['MENSAGEM']) and str(selected_err_row['MENSAGEM']).strip() != "":
                        exibir_xml_modal(selected_err_row['MENSAGEM'], selected_err_id)
                elif not should_open_modal_err:
                    # Se clicar em outra coluna, reseta o trigger do modal para o ID selecionado
                    st.session_state["modal_aberto_id_erros"] = None

                st.markdown("---")
                st.markdown(f"### 🔍 Diagnóstico do Evento: `{selected_err_id}`")

                # Ficha de Erro
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Funcionário:** {selected_err_row['NOME_FUNCIONARIO']} (Chapa: `{selected_err_row['CHAPA']}`)")
                    st.markdown(f"**Tipo de Evento:** `{selected_err_row['TIPOEVENTO']}` | Competência: `{selected_err_row['COMPETENCIA']}`")
                with col2:
                    st.markdown(f"**Status do RM:** `{selected_err_row['STATUS_EXIBICAO']}`")
                    st.markdown(f"**Data do Evento:** {selected_err_row['DATAEVENTO'].strftime('%d/%m/%Y') if pd.notna(selected_err_row['DATAEVENTO']) else 'N/A'}")

                # Exibição do Erro
                st.markdown("#### ❌ Mensagem de Erro Registrada:")
                st.error(selected_err_row['LOGGERACAO'])

                # XML não é mais exibido em botões/expansores abaixo da tabela
                if not ('MENSAGEM' in selected_err_row and pd.notna(selected_err_row['MENSAGEM']) and str(selected_err_row['MENSAGEM']).strip() != ""):
                    st.info("ℹ️ XML do evento não disponível.")
                st.markdown("---")
            else:
                st.session_state["modal_aberto_id_erros"] = None
                st.info("💡 Selecione uma linha na tabela de inconsistências acima para exibir a ficha técnica e clique em 🔍 para abrir o XML correspondente.")
        else:
            st.success("🎉 Nenhuma inconsistência (com campo Loggeração preenchido) encontrada na seleção atual!")

else:
    st.warning("Nenhum dado encontrado ou erro de conexão com o banco.")