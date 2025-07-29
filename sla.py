import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuração da página
st.set_page_config(
    page_title="Dashboard Transportes",
    page_icon="📦",
    layout="wide"
)

# Título da aplicação
st.title("📦 Dashboard Transportes")
st.markdown("---")

# Função para ordenar meses cronologicamente
def ordenar_meses(data_series):
    """Ordena uma série de dados por meses na ordem cronológica correta"""
    ordem_meses = ['JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO', 
                   'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO']
    
    meses_presentes = [mes for mes in ordem_meses if mes in data_series.index]
    return data_series.reindex(meses_presentes)

def ordenar_dataframe_por_meses(dataframe):
    """Ordena um DataFrame por meses na ordem cronológica correta"""
    ordem_meses = ['JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO', 
                   'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO']
    
    meses_presentes = [mes for mes in ordem_meses if mes in dataframe.index]
    return dataframe.reindex(meses_presentes)

def ajustar_posicao_texto(valores, threshold_percent=5):
    """
    Determina a posição e cor do texto baseado no tamanho dos valores.
    Valores pequenos (< threshold_percent do máximo) ficam fora da barra em preto.
    """
    max_valor = max(valores) if valores else 1
    threshold = max_valor * (threshold_percent / 100)
    
    posicoes = []
    cores = []
    
    for valor in valores:
        if valor < threshold:
            posicoes.append('outside')
            cores.append('black')
        else:
            posicoes.append('inside')
            cores.append('white')
    
    return posicoes, cores

def calcular_dias_uteis(data_inicio, data_fim):
    """
    Calcula o número de dias úteis entre duas datas
    """
    if pd.isna(data_inicio) or pd.isna(data_fim):
        return None
    
    try:
        # Converter para datetime se necessário
        if isinstance(data_inicio, str):
            data_inicio = pd.to_datetime(data_inicio, errors='coerce')
        if isinstance(data_fim, str):
            data_fim = pd.to_datetime(data_fim, errors='coerce')
        
        if pd.isna(data_inicio) or pd.isna(data_fim):
            return None
        
        # Usar pandas para calcular dias úteis (excluindo sábados e domingos)
        return pd.bdate_range(start=data_inicio, end=data_fim).shape[0] - 1
    except:
        return None

def criar_timeline_entrega(row):
    """
    Cria uma timeline visual estilo correios usando componentes nativos do Streamlit
    """
    # Função para formatar datas
    def format_date_timeline(date_value):
        if pd.isna(date_value) or date_value == '' or str(date_value) == 'N/A':
            return None
        try:
            if isinstance(date_value, str):
                date_obj = pd.to_datetime(date_value, errors='coerce')
            else:
                date_obj = date_value
            
            if pd.isna(date_obj):
                return None
            
            return date_obj.strftime('%d/%m/%Y')
        except:
            return None
    
    # Função para calcular diferença em dias corridos
    def calcular_dias_corridos(data_inicio, data_fim):
        if pd.isna(data_inicio) or pd.isna(data_fim):
            return None
        try:
            if isinstance(data_inicio, str):
                data_inicio = pd.to_datetime(data_inicio, errors='coerce')
            if isinstance(data_fim, str):
                data_fim = pd.to_datetime(data_fim, errors='coerce')
            
            if pd.isna(data_inicio) or pd.isna(data_fim):
                return None
            
            return (data_fim - data_inicio).days
        except:
            return None
    
    # Extrair e formatar as datas
    dt_nota = format_date_timeline(row.get('Dt Nota Fiscal'))
    dt_saida = format_date_timeline(row.get('Data de Saída'))
    dt_previsao = format_date_timeline(row.get('Previsão de Entrega'))
    dt_entrega = format_date_timeline(row.get('Data de Entrega'))
    
    # Extrair datas para cálculos (sem formatação)
    dt_nota_calc = pd.to_datetime(row.get('Dt Nota Fiscal'), errors='coerce')
    dt_saida_calc = pd.to_datetime(row.get('Data de Saída'), errors='coerce')
    dt_entrega_calc = pd.to_datetime(row.get('Data de Entrega'), errors='coerce')
    
    # Calcular durações
    # 1. Nota Fiscal Emitida - usar coluna Dias Faturamento
    dias_faturamento = row.get('Dias Faturamento', None)
    duracao_nota = f"{int(dias_faturamento)} dias" if pd.notna(dias_faturamento) else None
    
    # 2. Mercadoria Despachada - Data da emissão da nota fiscal x data de saída
    if pd.notna(dt_nota_calc) and pd.notna(dt_saida_calc):
        dias_despacho = calcular_dias_corridos(dt_nota_calc, dt_saida_calc)
        duracao_despacho = f"{dias_despacho} dias" if dias_despacho is not None else None
    else:
        duracao_despacho = None
    
    # 3. Previsão de Entrega - usar coluna Lead Time
    lead_time = row.get('Lead Time', None)
    duracao_previsao = f"{int(lead_time)} dias úteis" if pd.notna(lead_time) else None
    
    # 4. Entrega Realizada - Nota Fiscal Emitida até Entrega Realizada (DIAS ÚTEIS)
    if pd.notna(dt_nota_calc) and pd.notna(dt_entrega_calc):
        dias_uteis_total = calcular_dias_uteis(dt_nota_calc, dt_entrega_calc)
        duracao_entrega = f"{dias_uteis_total} dias úteis" if dias_uteis_total is not None else None
        
        # Calcular também em dias corridos para a soma total
        dias_corridos_entrega = calcular_dias_corridos(dt_nota_calc, dt_entrega_calc)
    else:
        duracao_entrega = None
        dias_corridos_entrega = None
    
    # Calcular soma total real (dias corridos)
    soma_real_dias = None
    if pd.notna(dias_faturamento) and dias_despacho is not None and dias_corridos_entrega is not None:
        soma_real_dias = int(dias_faturamento) + dias_despacho + dias_corridos_entrega
    
    # Definir etapas da timeline com durações
    etapas = [
        {
            'titulo': '📋 Nota Fiscal Emitida',
            'data': dt_nota,
            'duracao': duracao_nota,
            'status': 'concluido' if dt_nota else 'pendente',
            'icon': '✅' if dt_nota else '⭕'
        },
        {
            'titulo': '🚚 Mercadoria Despachada',
            'data': dt_saida,
            'duracao': duracao_despacho,
            'status': 'concluido' if dt_saida else 'pendente',
            'icon': '✅' if dt_saida else '⭕'
        },
        {
            'titulo': '🎯 Previsão de Entrega',
            'data': dt_previsao,
            'duracao': duracao_previsao,
            'status': 'concluido' if dt_previsao else 'pendente',
            'icon': '✅' if dt_previsao else '⭕'
        },
        {
            'titulo': '✅ Entrega Realizada',
            'data': dt_entrega,
            'duracao': duracao_entrega,
            'status': 'concluido' if dt_entrega else 'pendente',
            'icon': '✅' if dt_entrega else '⭕'
        }
    ]
    
    return etapas, soma_real_dias

# Função para carregar dados do arquivo carregado
@st.cache_data
def load_data_from_upload(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file, sheet_name='Base')
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
        return None

# ===== SISTEMA DE UPLOAD DE ARQUIVO =====
st.header("📁 Carregamento da Base de Dados")
st.markdown("Faça upload do arquivo Excel com os dados de SLA para análise.")

uploaded_file = st.file_uploader(
    "Selecione o arquivo Excel (.xlsx)",
    type=['xlsx', 'xls'],
    help="Arquivo deve conter uma planilha chamada 'Base' com os dados de SLA"
)

# Inicializar variável sla
sla = None

if uploaded_file is not None:
    # Mostrar informações do arquivo carregado
    st.success(f"✅ Arquivo carregado: **{uploaded_file.name}** ({uploaded_file.size} bytes)")
    
    # Carregar dados com spinner
    with st.spinner("Processando arquivo... Por favor, aguarde."):
        sla = load_data_from_upload(uploaded_file)
    
    if sla is not None:
        st.success(f"🎯 Dados processados com sucesso! Total de **{len(sla):,}** registros encontrados")
        
        # Mostrar preview e validação dos dados
        with st.expander("👀 Visualizar Preview e Validação dos Dados"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Total de Registros", f"{len(sla):,}")
            with col2:
                st.metric("📋 Total de Colunas", len(sla.columns))
            with col3:
                # Verificar período dos dados
                if 'Dt Nota Fiscal' in sla.columns:
                    try:
                        sla_temp = sla.copy()
                        sla_temp['Dt Nota Fiscal'] = pd.to_datetime(sla_temp['Dt Nota Fiscal'], errors='coerce')
                        periodo = f"{sla_temp['Dt Nota Fiscal'].min().strftime('%m/%Y')} - {sla_temp['Dt Nota Fiscal'].max().strftime('%m/%Y')}"
                        st.metric("📅 Período", periodo)
                    except:
                        st.metric("📅 Período", "N/A")
            
            # Validação das colunas essenciais
            st.markdown("### 🔍 Validação das Colunas")
            colunas_essenciais = [
                'Numero', 'Status', 'Transportador', 'Data de Entrega', 
                'Previsão de Entrega', 'Dt Nota Fiscal', 'Unid Negoc'
            ]
            
            col_val1, col_val2 = st.columns(2)
            
            with col_val1:
                st.markdown("**✅ Colunas Encontradas:**")
                colunas_encontradas = [col for col in colunas_essenciais if col in sla.columns]
                for col in colunas_encontradas:
                    st.markdown(f"✅ {col}")
            
            with col_val2:
                st.markdown("**⚠️ Colunas Faltantes:**")
                colunas_faltantes = [col for col in colunas_essenciais if col not in sla.columns]
                if colunas_faltantes:
                    for col in colunas_faltantes:
                        st.markdown(f"⚠️ {col}")
                else:
                    st.markdown("🎯 Todas as colunas essenciais estão presentes!")
            
            # Preview dos dados
            st.markdown("### 📋 Preview dos Dados")
            st.dataframe(sla.head(), use_container_width=True)
            
            # Lista todas as colunas disponíveis
            with st.expander("📋 Todas as Colunas Disponíveis"):
                cols_per_row = 3
                colunas_lista = list(sla.columns)
                for i in range(0, len(colunas_lista), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, col_name in enumerate(colunas_lista[i:i+cols_per_row]):
                        if j < len(cols):
                            cols[j].markdown(f"• **{col_name}**")
        
        st.markdown("---")
    else:
        st.error("❌ Não foi possível processar o arquivo. Verifique se:")
        st.markdown("""
        - O arquivo é um Excel válido (.xlsx ou .xls)
        - Existe uma planilha chamada **'Base'**
        - A planilha contém dados no formato esperado
        """)
        st.stop()
else:
    # Instruções para o usuário
    st.info("👆 Faça upload do arquivo Excel para começar a análise")
   
    st.stop()

if sla is not None:
    # ===== FILTROS GLOBAIS NO SIDEBAR =====
    st.sidebar.header("🔧 Filtros Globais")
    st.sidebar.markdown("Filtros aplicados a todas as análises:")
    
    # Converter coluna de data para datetime se necessário
    try:
        sla['Dt Nota Fiscal'] = pd.to_datetime(sla['Dt Nota Fiscal'], errors='coerce')
    except:
        pass
    
    # Filtro por BU (multiselect)
    if 'Unid Negoc' in sla.columns:
        # Remover BUs específicas da análise (070, 080, 720)
        bus_excluidas = ['070 - CD Shared', '080 - Planta Geral', '720 - SIP2']
        todas_bus = sla['Unid Negoc'].dropna().unique().tolist()
        bus_disponiveis = sorted([bu for bu in todas_bus if str(bu) not in bus_excluidas])
        bus_selecionadas = st.sidebar.multiselect(
            "🏢 Unidade de Negócio (BU):",
            options=bus_disponiveis,
            default=[],  # Todas selecionadas por padrão (exceto as excluídas)
            help="Selecione uma ou mais BUs. Vazio = todas as BUs. BUs 070, 080 e 720 foram excluídas da análise."
        )
        # Se nenhuma selecionada, usar todas
        if not bus_selecionadas:
            bus_selecionadas = bus_disponiveis
    else:
        bus_selecionadas = []
    
    # Filtro por Data de Faturamento
    if 'Dt Nota Fiscal' in sla.columns and sla['Dt Nota Fiscal'].notna().any():
        # Obter datas mínima e máxima
        data_min = sla['Dt Nota Fiscal'].min().date()
        data_max = sla['Dt Nota Fiscal'].max().date()
        
        # Date range picker
        st.sidebar.markdown("📅 **Período de Faturamento:**")
        data_inicio = st.sidebar.date_input(
            "Data inicial:",
            value=data_min,
            min_value=data_min,
            max_value=data_max
        )
        data_fim = st.sidebar.date_input(
            "Data final:",
            value=data_max,
            min_value=data_min,
            max_value=data_max
        )
        
        # Validar se data_inicio <= data_fim
        if data_inicio > data_fim:
            st.sidebar.error("❌ Data inicial deve ser menor ou igual à data final!")
            data_inicio = data_min
            data_fim = data_max
    else:
        data_inicio = None
        data_fim = None
    
    # Filtro por Transportadora (multiselect)
    if 'Transportador' in sla.columns:
        transportadoras_disponiveis = sorted(sla['Transportador'].dropna().unique().tolist())
        transportadoras_selecionadas = st.sidebar.multiselect(
            "🚚 Transportadora:",
            options=transportadoras_disponiveis,
            default=[],  # Todas selecionadas por padrão
            help="Selecione uma ou mais transportadoras. Vazio = todas as transportadoras."
        )
        # Se nenhuma selecionada, usar todas
        if not transportadoras_selecionadas:
            transportadoras_selecionadas = transportadoras_disponiveis
    else:
        transportadoras_selecionadas = []
    
    # Aplicar filtros aos dados
    sla_filtrado = sla.copy()
    
    # Aplicar filtro de BU (multiselect)
    if bus_selecionadas and len(bus_selecionadas) < len(bus_disponiveis if 'Unid Negoc' in sla.columns else []):
        sla_filtrado = sla_filtrado[sla_filtrado['Unid Negoc'].isin(bus_selecionadas)]
    
    # Aplicar filtro de data
    if data_inicio is not None and data_fim is not None:
        sla_filtrado = sla_filtrado[
            (sla_filtrado['Dt Nota Fiscal'].dt.date >= data_inicio) &
            (sla_filtrado['Dt Nota Fiscal'].dt.date <= data_fim)
        ]
    
    # Aplicar filtro de transportadora (multiselect)
    if transportadoras_selecionadas and len(transportadoras_selecionadas) < len(transportadoras_disponiveis if 'Transportador' in sla.columns else []):
        sla_filtrado = sla_filtrado[sla_filtrado['Transportador'].isin(transportadoras_selecionadas)]
    
    # Mostrar informações dos dados filtrados
    registros_filtrados = len(sla_filtrado)
    if registros_filtrados != len(sla):
        st.sidebar.markdown("---")
        st.sidebar.markdown("📊 **Dados Filtrados:**")
        st.sidebar.metric("📋 Registros", f"{registros_filtrados:,}".replace(",", "."))
        st.sidebar.metric("📉 Redução", f"{((len(sla) - registros_filtrados) / len(sla) * 100):.1f}%")
        
        # Mostrar filtros ativos
        st.sidebar.markdown("**🔍 Filtros Ativos:**")
        
        # BUs selecionadas
        if bus_selecionadas and len(bus_selecionadas) < len(bus_disponiveis if 'Unid Negoc' in sla.columns else []):
            if len(bus_selecionadas) <= 3:
                st.sidebar.markdown(f"🏢 **BUs:** {', '.join(bus_selecionadas)}")
            else:
                st.sidebar.markdown(f"🏢 **BUs:** {len(bus_selecionadas)} selecionadas")
        
        # Período selecionado
        if data_inicio and data_fim:
            st.sidebar.markdown(f"📅 **Período:** {data_inicio.strftime('%d/%m/%Y')} - {data_fim.strftime('%d/%m/%Y')}")
        
        # Transportadoras selecionadas
        if transportadoras_selecionadas and len(transportadoras_selecionadas) < len(transportadoras_disponiveis if 'Transportador' in sla.columns else []):
            if len(transportadoras_selecionadas) <= 3:
                st.sidebar.markdown(f"🚚 **Transportadoras:** {', '.join(transportadoras_selecionadas)}")
            else:
                st.sidebar.markdown(f"🚚 **Transportadoras:** {len(transportadoras_selecionadas)} selecionadas")
        
        if registros_filtrados == 0:
            st.warning("⚠️ Nenhum registro encontrado com os filtros aplicados. Ajuste os filtros para visualizar dados.")
            st.stop()
    
    # Substituir sla pelos dados filtrados para uso em todas as abas
    sla = sla_filtrado
    
    # ===== ABAS PRINCIPAIS =====
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard Geral", 
        "🎯 Performance SLA", 
        "🚨 Gestão de Pendências", 
        "📦 Volumetria",
        "🔍 Busca NF"
    ])
    
    # ===== ABA 1: DASHBOARD GERAL =====
    with tab1:
        st.header("📊 Dashboard Geral")
        st.markdown("Visão geral do negócio e principais métricas operacionais.")
        
        if not sla.empty:
            # Calcular métricas principais
            total_nfs = len(sla)
            
            # Taxa de SLA (assumindo que entregas no prazo são as que têm data de entrega <= previsão)
            try:
                sla['Data de Entrega'] = pd.to_datetime(sla['Data de Entrega'], errors='coerce')
                sla['Previsão de Entrega'] = pd.to_datetime(sla['Previsão de Entrega'], errors='coerce')
                
                entregas_realizadas = sla.dropna(subset=['Data de Entrega', 'Previsão de Entrega'])
                entregas_no_prazo = len(entregas_realizadas[entregas_realizadas['Data de Entrega'] <= entregas_realizadas['Previsão de Entrega']])
                taxa_sla = (entregas_no_prazo / len(entregas_realizadas) * 100) if len(entregas_realizadas) > 0 else 0
            except:
                taxa_sla = 0
                
            # Lead Time médio
            try:
                lead_time_medio = sla['Lead Time'].mean() if 'Lead Time' in sla.columns else 0
            except:
                lead_time_medio = 0
                
            # Valor total
            try:
                valor_total = sla['Valor NF'].sum() if 'Valor NF' in sla.columns else 0
            except:
                valor_total = 0
                
            # Nova linha de métricas de peso
            peso_total = sla['Peso Bruto NF'].sum() if 'Peso Bruto NF' in sla.columns else 0
            peso_medio = sla['Peso Bruto NF'].mean() if 'Peso Bruto NF' in sla.columns and sla['Peso Bruto NF'].notna().any() else 0
            
            # Primeira linha - Métricas principais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📦 Total de NFs", f"{total_nfs:,}".replace(",", "."))
                
            with col2:
                st.metric("⚖️ Peso Total", f"{peso_total/1000000:.1f}t" if peso_total > 1000000 else f"{peso_total/1000:.0f}kg")
                
            with col3:
                st.metric("📊 Peso Médio", f"{peso_medio:.1f} kg")
                
            with col4:
                valor_formatado = f"R$ {valor_total/1000000:.1f}M" if valor_total > 1000000 else f"R$ {valor_total/1000:.0f}K"
                st.metric("💰 Valor Total", valor_formatado)
            
            # Segunda linha - Gráfico de SLA
            st.markdown("###")  # Espaçamento
            
            # Gráfico gauge para Taxa de SLA
            fig_sla = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = taxa_sla,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "🎯 Taxa de SLA (%)"},
                delta = {'reference': 95},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 85], 'color': "yellow"},
                        {'range': [85, 95], 'color': "orange"},
                        {'range': [95, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 95
                    }
                }
            ))
            
            # Adicionar anotações com insights
            entregas_atrasadas = 100 - taxa_sla
            
            # Determinar status da performance
            if taxa_sla >= 95:
                status = "EXCELENTE"
                cor_status = "green"
                emoji_status = "🟢"
            elif taxa_sla >= 85:
                status = "BOM"
                cor_status = "orange"
                emoji_status = "🟡"
            elif taxa_sla >= 70:
                status = "ATENÇÃO"
                cor_status = "orange"
                emoji_status = "🟠"
            else:
                status = "CRÍTICO"
                cor_status = "red"
                emoji_status = "🔴"
            
            fig_sla.add_annotation(
                x=0.5, y=0.15,
                text=f"{emoji_status} Status: <b>{status}</b>",
                showarrow=False,
                font=dict(size=14, color=cor_status),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor=cor_status,
                borderwidth=2
            )
            
            fig_sla.add_annotation(
                x=0.5, y=0.05,
                text=f"📊 {entregas_atrasadas:.1f}% das entregas estão atrasadas",
                showarrow=False,
                font=dict(size=11, color="darkred"),
                bgcolor="rgba(255,255,255,0.8)"
            )
            
            fig_sla.update_layout(
                height=350,
                annotations=[
                    dict(
                        x=0.5, y=-0.1,
                        text="Meta: 95% | Crítico: <50% | Atenção: 50-85% | Bom: 85-95% | Excelente: ≥95%",
                        showarrow=False,
                        font=dict(size=10, color="gray"),
                        xref="paper", yref="paper"
                    )
                ]
            )
            
            st.plotly_chart(fig_sla, use_container_width=True, key="sla_gauge_dashboard")
            
            # Insights específicos abaixo do gráfico
            if taxa_sla < 95:
                gap_necessario = 95 - taxa_sla
                entregas_necessarias = int((gap_necessario / 100) * len(entregas_realizadas)) if len(entregas_realizadas) > 0 else 0
                
                st.warning(f"""
                **🚨 Ações Necessárias:**
                - Melhorar **{gap_necessario:.1f} pontos percentuais** para atingir a meta
                - Reduzir aproximadamente **{entregas_necessarias} entregas atrasadas**
                - Foco nas transportadoras com pior performance
                """)
            else:
                st.success(f"""
                **🏆 Parabéns!**
                - Meta de SLA atingida com sucesso!
                - Performance {taxa_sla - 95:.1f} pontos acima da meta
                """)
            
            # Interpretação rápida
            with st.expander("💡 Como interpretar este gráfico"):
                st.markdown(f"""
                **📊 Situação Atual:**
                - **{taxa_sla:.1f}%** das entregas chegam no prazo
                - **{entregas_atrasadas:.1f}%** das entregas estão atrasadas
                - Status: **{status}** {emoji_status}
                
                **🎯 Significado Prático:**
                - De cada 100 entregas → **{int(taxa_sla)} no prazo** e **{int(entregas_atrasadas)} atrasadas**
                - Meta ideal: 95 no prazo e apenas 5 atrasadas
                
                **📈 Faixas de Performance:**
                - 🟢 **Excelente** (≥95%): Meta atingida
                - 🟡 **Bom** (85-94%): Próximo da meta
                - 🟠 **Atenção** (70-84%): Precisa melhorar
                - 🔴 **Crítico** (<70%): Ação urgente necessária
                """)
            
            # Terceira linha - Análise de Volume Reformulada
            st.subheader("📊 Análise de Volume por Transportadora e Estado")
            
            # Criar abas para a análise de volume
            tab_transp, tab_geo = st.tabs(["🚚 Ranking de Transportadores", "🗺️ Distribuição Geográfica"])
            
            with tab_transp:
                st.markdown("### 🚚 Ranking de Transportadores")
                if 'Transportador' in sla.columns:
                    top_transportadores = sla['Transportador'].value_counts().head(8)
                    total_nfs = len(sla)
                    
                    if len(top_transportadores) > 0:
                        # Criar gráfico melhorado
                        fig_transp = go.Figure()
                        
                        # Calcular percentuais
                        percentuais = (top_transportadores.values / total_nfs * 100).round(1)
                        
                        # Cores gradientes personalizadas
                        cores = ['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
                        
                        fig_transp.add_trace(go.Bar(
                            x=top_transportadores.values,
                            y=top_transportadores.index,
                            orientation='h',
                            text=[f'{val:,} ({pct}%)'.replace(',', '.') for val, pct in zip(top_transportadores.values, percentuais)],
                            textposition='inside',
                            textfont=dict(color='white', size=10, family='Arial Black'),
                            marker=dict(
                                color=cores[:len(top_transportadores)],
                                line=dict(color='rgba(50,50,50,0.8)', width=1)
                            ),
                            hovertemplate='<b>%{y}</b><br>' +
                                          'Volume: %{x:,} NFs<br>' +
                                          'Percentual: %{text}<br>' +
                                          '<extra></extra>'
                        ))
                        
                        fig_transp.update_layout(
                            title=dict(
                                text="🏆 Ranking por Volume de NFs",
                                x=0.5,
                                font=dict(size=14, family="Arial Black")
                            ),
                            xaxis_title="Quantidade de NFs",
                            yaxis_title="",
                            height=500,
                            showlegend=False,
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray'),
                            yaxis=dict(showgrid=False),
                            margin=dict(l=20, r=20, t=60, b=20)
                        )
                        
                        st.plotly_chart(fig_transp, use_container_width=True, key="transportadores_ranking_tab")
                        
                        # Insights da transportadora
                        lider = top_transportadores.index[0]
                        vol_lider = top_transportadores.iloc[0]
                        pct_lider = percentuais[0]
                        
                        # Métricas detalhadas
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("🥇 Líder", lider)
                            
                        with col2:
                            st.metric("📦 Volume Líder", f"{vol_lider:,} NFs".replace(",", "."))
                            
                        with col3:
                            st.metric("📊 Participação", f"{pct_lider:.1f}%")
                        
                        # Insights detalhados
                        st.info(f"""
                        **📈 Análise do Líder:**
                        - **{lider}** domina com **{vol_lider:,} NFs** ({pct_lider}% do total)
                        - Representa **1 em cada {int(100/pct_lider)} entregas**
                        - Total de **{len(top_transportadores)} transportadoras** principais
                        """.replace(',', '.'))
                    else:
                        st.warning("Nenhum dado de transportadora disponível")
                else:
                    st.info("Dados de transportador não disponíveis")
                    
            with tab_geo:
                st.markdown("### 🗺️ Distribuição Geográfica")
                if 'Estado Destino' in sla.columns:
                    top_estados = sla['Estado Destino'].value_counts().head(8)
                    total_nfs = len(sla)
                    
                    if len(top_estados) > 0:
                        # Criar gráfico melhorado
                        fig_estados = go.Figure()
                        
                        # Calcular percentuais
                        percentuais_est = (top_estados.values / total_nfs * 100).round(1)
                        
                        # Cores regionais do Brasil (tons mais escuros para legibilidade)
                        cores_estados = ['#006400', '#228B22', '#2E8B57', '#3CB371', '#20B2AA', '#4682B4', '#4169E1', '#6A5ACD']
                        
                        fig_estados.add_trace(go.Bar(
                            x=top_estados.values,
                            y=top_estados.index,
                            orientation='h',
                            text=[f'{val:,} ({pct}%)'.replace(',', '.') for val, pct in zip(top_estados.values, percentuais_est)],
                            textposition='inside',
                            textfont=dict(color='white', size=10, family='Arial Black'),
                            marker=dict(
                                color=cores_estados[:len(top_estados)],
                                line=dict(color='rgba(50,50,50,0.8)', width=1)
                            ),
                            hovertemplate='<b>%{y}</b><br>' +
                                          'Volume: %{x:,} entregas<br>' +
                                          'Percentual: %{text}<br>' +
                                          '<extra></extra>'
                        ))
                        
                        fig_estados.update_layout(
                            title=dict(
                                text="🌎 Distribuição por Estados",
                                x=0.5,
                                font=dict(size=14, family="Arial Black")
                            ),
                            xaxis_title="Quantidade de Entregas",
                            yaxis_title="",
                            height=500,
                            showlegend=False,
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray'),
                            yaxis=dict(showgrid=False),
                            margin=dict(l=20, r=20, t=60, b=20)
                        )
                        
                        st.plotly_chart(fig_estados, use_container_width=True, key="estados_distribuicao_tab")
                        
                        # Insights do estado
                        estado_lider = top_estados.index[0]
                        vol_estado = top_estados.iloc[0]
                        pct_estado = percentuais_est[0]
                        
                        # Calcular concentração (top 3)
                        concentracao_top3 = sum(percentuais_est[:3])
                        
                        # Métricas detalhadas
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("🥇 Estado Líder", estado_lider)
                            
                        with col2:
                            st.metric("📦 Volume Líder", f"{vol_estado:,} entregas".replace(",", "."))
                            
                        with col3:
                            st.metric("📊 Top 3 Estados", f"{concentracao_top3:.1f}%")
                        
                        # Insights detalhados
                        st.info(f"""
                        **🌎 Análise Geográfica:**
                        - **{estado_lider}** lidera com **{vol_estado:,} entregas** ({pct_estado}% do total)
                        - Top 3 estados concentram **{concentracao_top3:.1f}%** das entregas
                        - Cobertura de **{len(top_estados)} estados** principais
                        """.replace(',', '.'))
                    else:
                        st.warning("Nenhum dado de estado disponível")
                else:
                    st.info("Dados de estado não disponíveis")
            
            # Resumo comparativo geral
            if 'Transportador' in sla.columns and 'Estado Destino' in sla.columns:
                st.markdown("### 📊 Resumo Comparativo")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    qtd_transportadores = sla['Transportador'].nunique()
                    st.metric("🚚 Total Transportadores", qtd_transportadores)
                    
                with col2:
                    qtd_estados = sla['Estado Destino'].nunique()
                    st.metric("🗺️ Estados Atendidos", qtd_estados)
                    
                with col3:
                    # Índice de concentração (% do top 1 em cada categoria)
                    top_transportadores_calc = sla['Transportador'].value_counts()
                    top_estados_calc = sla['Estado Destino'].value_counts()
                    if len(top_transportadores_calc) > 0 and len(top_estados_calc) > 0:
                        concentracao = ((top_transportadores_calc.iloc[0] + top_estados_calc.iloc[0]) / (2 * total_nfs) * 100).round(1)
                        st.metric("📊 Índice Concentração", f"{concentracao}%")
            
            # Quarta linha - Status e Ocorrências
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Distribuição por Status")
                if 'Status' in sla.columns:
                    status_counts = sla['Status'].value_counts()
                    
                    # Ajustar posição do texto baseado no tamanho dos valores
                    posicoes, cores_texto = ajustar_posicao_texto(status_counts.values.tolist())
                    
                    # Criar gráfico personalizado para controlar posição de texto individualmente
                    fig_status = go.Figure()
                    
                    # Cores do gradiente Viridis
                    import plotly.colors as pc
                    viridis_colors = pc.sequential.Viridis
                    min_val = min(status_counts.values)
                    max_val = max(status_counts.values)
                    range_val = max_val - min_val if max_val != min_val else 1
                    norm_values = [(v - min_val) / range_val for v in status_counts.values]
                    bar_colors = [viridis_colors[int(norm * (len(viridis_colors) - 1))] for norm in norm_values]
                    
                    fig_status.add_trace(go.Bar(
                        x=status_counts.index,
                        y=status_counts.values,
                        text=[str(v) for v in status_counts.values],
                        textposition=posicoes,
                        textfont=dict(color=cores_texto, size=12, family='Arial Black'),
                        marker_color=bar_colors,
                        hovertemplate='<b>%{x}</b><br>Quantidade: %{y}<extra></extra>'
                    ))
                    
                    fig_status.update_layout(
                        title="Quantidade por Status",
                        xaxis_title="Status",
                        yaxis_title="Quantidade",
                        height=400,
                        showlegend=False
                    )
                    st.plotly_chart(fig_status, use_container_width=True, key="status_distribuicao")
                else:
                    st.info("Dados de status não disponíveis")
                    
            with col2:
                st.subheader("⚠️ Top Ocorrências")
                if 'Ocorrência' in sla.columns:
                    # Filtrar apenas ocorrências não nulas e não vazias
                    ocorrencias_filtradas = sla[sla['Ocorrência'].notna() & (sla['Ocorrência'] != '')]
                    if not ocorrencias_filtradas.empty:
                        top_ocorrencias = ocorrencias_filtradas['Ocorrência'].value_counts().head(8)
                        
                        # Ajustar posição do texto baseado no tamanho dos valores
                        posicoes, cores_texto = ajustar_posicao_texto(top_ocorrencias.values.tolist())
                        
                        fig_ocorr = px.bar(
                            x=top_ocorrencias.values,
                            y=[str(x)[:30] + "..." if len(str(x)) > 30 else str(x) for x in top_ocorrencias.index],
                            orientation='h',
                            title="Principais Ocorrências",
                            labels={'x': 'Quantidade', 'y': 'Ocorrência'},
                            color=top_ocorrencias.values,
                            color_continuous_scale='Reds',
                            text=top_ocorrencias.values
                        )
                        fig_ocorr.update_layout(height=400, showlegend=False, coloraxis_showscale=False)
                        
                        # Aplicar posições de texto inteligentes
                        if len(set(posicoes)) == 1:  # Se todas têm a mesma posição
                            fig_ocorr.update_traces(
                                textposition=posicoes[0],
                                textfont=dict(color=cores_texto[0], size=11, family='Arial Black'),
                                hovertemplate='<b>%{y}</b><br>Quantidade: %{x}<extra></extra>'
                            )
                        else:  # Posições mistas - usar outside para todos valores pequenos
                            fig_ocorr.update_traces(
                                textposition='auto',
                                textfont=dict(color='black', size=11, family='Arial Black'),
                                hovertemplate='<b>%{y}</b><br>Quantidade: %{x}<extra></extra>'
                            )
                        st.plotly_chart(fig_ocorr, use_container_width=True, key="ocorrencias_top")
                    else:
                        st.success("✅ Nenhuma ocorrência registrada!")
                else:
                    st.info("Dados de ocorrência não disponíveis")
            
            # Volume mensal geral
            if 'Mês Nota' in sla.columns:
                st.subheader("📊 Volume Geral de Entregas por Mês")
                
                mensal = sla['Mês Nota'].value_counts()
                mensal_ordenado = ordenar_meses(mensal)
                
                # Ajustar posição do texto baseado no tamanho dos valores
                posicoes, cores_texto = ajustar_posicao_texto(mensal_ordenado.values.tolist())
                
                fig_mensal = px.bar(
                    x=mensal_ordenado.index,
                    y=mensal_ordenado.values,
                    title="Volume Total de NFs por Mês",
                    labels={'x': 'Mês', 'y': 'Quantidade de NFs'},
                    color=mensal_ordenado.values,
                    color_continuous_scale='Blues',
                    text=mensal_ordenado.values
                )
                fig_mensal.update_layout(height=300, showlegend=False, coloraxis_showscale=False)
                
                # Aplicar posições de texto inteligentes
                if len(set(posicoes)) == 1:  # Se todas têm a mesma posição
                    fig_mensal.update_traces(
                        textposition=posicoes[0],
                        textfont=dict(color=cores_texto[0], size=11, family='Arial Black'),
                        hovertemplate='<b>%{x}</b><br>Volume: %{y} NFs<extra></extra>'
                    )
                else:  # Posições mistas - usar auto
                    fig_mensal.update_traces(
                        textposition='auto',
                        textfont=dict(color='black', size=11, family='Arial Black'),
                        hovertemplate='<b>%{x}</b><br>Volume: %{y} NFs<extra></extra>'
                    )
                st.plotly_chart(fig_mensal, use_container_width=True, key="volume_mensal_dashboard")
    
    # ===== ABA 2: PERFORMANCE SLA =====
    with tab2:
        st.header("🎯 Performance de SLA")
        st.markdown("Análise detalhada da performance de entrega por transportadora e status.")
        
        if all(col in sla.columns for col in ['Transportador', 'Data de Entrega', 'Previsão de Entrega']):
            # Filtrar apenas entregas realizadas (com data de entrega)
            entregas_realizadas = sla.dropna(subset=['Data de Entrega', 'Previsão de Entrega', 'Transportador'])
            
            if not entregas_realizadas.empty:
                # Garantir que as datas estão no formato correto
                entregas_realizadas = entregas_realizadas.copy()
                entregas_realizadas['Data de Entrega'] = pd.to_datetime(entregas_realizadas['Data de Entrega'], errors='coerce')
                entregas_realizadas['Previsão de Entrega'] = pd.to_datetime(entregas_realizadas['Previsão de Entrega'], errors='coerce')
                
                # Classificar entregas como no prazo ou atrasadas
                entregas_realizadas['Status_Entrega'] = entregas_realizadas.apply(
                    lambda row: 'Entregue no Prazo' if row['Data de Entrega'] <= row['Previsão de Entrega'] else 'Entregue Atrasada',
                    axis=1
                )
                
                # Agrupar por transportadora e status de entrega
                performance_transp = entregas_realizadas.groupby(['Transportador', 'Status_Entrega']).size().unstack(fill_value=0)
                
                # Calcular percentuais
                performance_transp_pct = performance_transp.div(performance_transp.sum(axis=1), axis=0) * 100
                
                # Filtrar apenas transportadoras com pelo menos 10 entregas para análise consistente
                total_entregas = performance_transp.sum(axis=1)
                transportadoras_relevantes = total_entregas[total_entregas >= 10].index
                performance_filtrada = performance_transp_pct.loc[transportadoras_relevantes]
                
                if not performance_filtrada.empty:
                    # Ordenar por percentual de entregas no prazo (descendente)
                    if 'Entregue no Prazo' in performance_filtrada.columns:
                        performance_filtrada = performance_filtrada.sort_values('Entregue no Prazo', ascending=False)
                    
                    # Preparar dados para o gráfico
                    transportadoras = performance_filtrada.index.tolist()
                    
                    # Criar gráfico de barras simples - apenas entregas no prazo
                    fig_performance = go.Figure()
                    
                    if 'Entregue no Prazo' in performance_filtrada.columns:
                        # Ordenar por performance (do maior para o menor)
                        performance_ordenada = performance_filtrada.sort_values('Entregue no Prazo', ascending=True)
                        
                        # Cores gradientes baseadas na performance
                        cores = []
                        for val in performance_ordenada['Entregue no Prazo']:
                            if val >= 95:
                                cores.append('#008000')  # Verde escuro - Excelente
                            elif val >= 85:
                                cores.append('#32CD32')  # Verde - Bom
                            elif val >= 70:
                                cores.append('#FFA500')  # Laranja - Atenção
                            else:
                                cores.append('#FF4500')  # Vermelho - Crítico
                        
                        fig_performance.add_trace(go.Bar(
                            x=performance_ordenada['Entregue no Prazo'],
                            y=performance_ordenada.index,
                            orientation='h',
                            marker_color=cores,
                            text=[f'{val:.1f}%' for val in performance_ordenada['Entregue no Prazo']],
                            textposition='inside',
                            textfont=dict(color='white', size=11, family='Arial Black'),
                            hovertemplate='<b>%{y}</b><br>Performance: %{x:.1f}%<extra></extra>'
                        ))
                    
                    fig_performance.update_layout(
                        title='🎯 Performance de SLA - % Entregas no Prazo (min. 10 entregas)',
                        xaxis_title='Percentual de Entregas no Prazo (%)',
                        yaxis_title='Transportadora',
                        height=500,
                        showlegend=False,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(
                            showgrid=True, 
                            gridwidth=1, 
                            gridcolor='LightGray',
                            range=[0, 100]
                        ),
                        yaxis=dict(showgrid=False),
                        margin=dict(l=20, r=20, t=60, b=20)
                    )
                    
                    st.plotly_chart(fig_performance, use_container_width=True, key="performance_sla_transportadoras")
                    
                    # Exibir tabela com dados focados na performance
                    with st.expander("📊 Dados Detalhados da Performance"):
                        # Criar tabela com foco nas entregas no prazo
                        tabela_performance = performance_transp.loc[transportadoras_relevantes].copy()
                        tabela_performance['Total Entregas'] = tabela_performance.sum(axis=1)
                        
                        # Focar apenas nas entregas no prazo
                        if 'Entregue no Prazo' in tabela_performance.columns:
                            tabela_performance['% SLA Atingido'] = (tabela_performance['Entregue no Prazo'] / tabela_performance['Total Entregas'] * 100).round(1)
                        
                        # Selecionar e renomear colunas para exibição
                        colunas_exibir = ['Entregue no Prazo', 'Total Entregas', '% SLA Atingido']
                        colunas_disponiveis = [col for col in colunas_exibir if col in tabela_performance.columns]
                        
                        tabela_final = tabela_performance[colunas_disponiveis].copy()
                        tabela_final = tabela_final.rename(columns={
                            'Entregue no Prazo': '✅ Entregas no Prazo',
                            'Total Entregas': '📦 Total de Entregas',
                            '% SLA Atingido': '🎯 % SLA Atingido'
                        })
                        
                        # Ordenar por performance (melhor primeiro)
                        if '🎯 % SLA Atingido' in tabela_final.columns:
                            tabela_final = tabela_final.sort_values('🎯 % SLA Atingido', ascending=False)
                        
                        st.dataframe(tabela_final, use_container_width=True)
                else:
                    st.info("📊 Nenhuma transportadora com volume suficiente (min. 10 entregas) para análise")
            else:
                st.info("📊 Não há dados suficientes de entregas realizadas para análise")
        else:
            st.info("📊 Dados necessários para análise de performance não disponíveis")
    
    # ===== ABA 3: GESTÃO DE PENDÊNCIAS =====
    with tab3:
        st.header("🚨 Gestão de Pendências")
        st.markdown("Análise e gerenciamento de notas fiscais pendentes de entrega.")
        
        if all(col in sla.columns for col in ['Data de Entrega', 'Previsão de Entrega', 'Transportador']):
            # Filtrar notas pendentes (sem data de entrega ou atrasadas)
            # Notas sem data de entrega (pendentes)
            notas_pendentes = sla[sla['Data de Entrega'].isna()].copy()
            
            # Notas com data de entrega mas atrasadas
            sla_temp = sla.copy()
            sla_temp['Data de Entrega'] = pd.to_datetime(sla_temp['Data de Entrega'], errors='coerce')
            sla_temp['Previsão de Entrega'] = pd.to_datetime(sla_temp['Previsão de Entrega'], errors='coerce')
            
            notas_atrasadas = sla_temp[
                (sla_temp['Data de Entrega'].notna()) & 
                (sla_temp['Previsão de Entrega'].notna()) &
                (sla_temp['Data de Entrega'] > sla_temp['Previsão de Entrega'])
            ].copy()
            
            # Combinar pendentes + atrasadas
            todas_pendentes = pd.concat([notas_pendentes, notas_atrasadas], ignore_index=True)
            
            if not todas_pendentes.empty:
                # Filtro por transportadora
                transportadoras_com_pendencias = ['TODAS'] + sorted(todas_pendentes['Transportador'].dropna().unique().tolist())
                
                transportadora_filtro = st.selectbox(
                    "🚚 Filtrar por Transportadora:",
                    options=transportadoras_com_pendencias,
                    index=0,
                    key="filtro_pendentes"
                )
                
                # Aplicar filtro se não for "TODAS"
                if transportadora_filtro != "TODAS":
                    todas_pendentes_filtradas = todas_pendentes[todas_pendentes['Transportador'] == transportadora_filtro].copy()
                    notas_pendentes_filtradas = notas_pendentes[notas_pendentes['Transportador'] == transportadora_filtro].copy()
                    notas_atrasadas_filtradas = notas_atrasadas[notas_atrasadas['Transportador'] == transportadora_filtro].copy()
                else:
                    todas_pendentes_filtradas = todas_pendentes.copy()
                    notas_pendentes_filtradas = notas_pendentes.copy()
                    notas_atrasadas_filtradas = notas_atrasadas.copy()
                
                # Métricas gerais (usando dados filtrados)
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("🔴 Total Pendentes", len(todas_pendentes_filtradas))
                    
                with col2:
                    st.metric("⏰ Sem Data Entrega", len(notas_pendentes_filtradas))
                    
                with col3:
                    st.metric("📅 Entregues Atrasadas", len(notas_atrasadas_filtradas))
                    
                with col4:
                    if transportadora_filtro != "TODAS":
                        # Calcular % baseado no total da transportadora selecionada
                        total_transportadora = len(sla[sla['Transportador'] == transportadora_filtro]) if transportadora_filtro in sla['Transportador'].values else 1
                        pct_pendentes = (len(todas_pendentes_filtradas) / total_transportadora * 100) if total_transportadora > 0 else 0
                        st.metric("📊 % da Transportadora", f"{pct_pendentes:.1f}%")
                    else:
                        pct_pendentes = (len(todas_pendentes_filtradas) / len(sla) * 100) if len(sla) > 0 else 0
                        st.metric("📊 % do Total", f"{pct_pendentes:.1f}%")
                
                # Gráficos de análise
                col1, col2 = st.columns(2)
                
                with col1:
                    if transportadora_filtro != "TODAS":
                        st.markdown(f"**📅 Pendentes por Mês - {transportadora_filtro}**")
                        
                        if 'Mês Nota' in todas_pendentes_filtradas.columns and not todas_pendentes_filtradas.empty:
                            pendentes_mes = todas_pendentes_filtradas['Mês Nota'].value_counts()
                            pendentes_mes_ordenado = ordenar_meses(pendentes_mes)
                            
                            if not pendentes_mes_ordenado.empty:
                                # Ajustar posição do texto baseado no tamanho dos valores
                                posicoes, cores_texto = ajustar_posicao_texto(pendentes_mes_ordenado.values.tolist())
                                
                                fig_pend_mes = px.bar(
                                    x=pendentes_mes_ordenado.index,
                                    y=pendentes_mes_ordenado.values,
                                    title=f"Pendentes por Mês - {transportadora_filtro}",
                                    labels={'x': 'Mês', 'y': 'Quantidade'},
                                    color=pendentes_mes_ordenado.values,
                                    color_continuous_scale='Oranges',
                                    text=pendentes_mes_ordenado.values
                                )
                                fig_pend_mes.update_layout(height=400, showlegend=False, coloraxis_showscale=False)
                                
                                # Aplicar posições de texto inteligentes
                                if len(set(posicoes)) == 1:  # Se todas têm a mesma posição
                                    fig_pend_mes.update_traces(
                                        textposition=posicoes[0],
                                        textfont=dict(color=cores_texto[0], size=11, family='Arial Black'),
                                        hovertemplate='<b>%{x}</b><br>Pendentes: %{y}<extra></extra>'
                                    )
                                else:  # Posições mistas - usar auto
                                    fig_pend_mes.update_traces(
                                        textposition='auto',
                                        textfont=dict(color='black', size=11, family='Arial Black'),
                                        hovertemplate='<b>%{x}</b><br>Pendentes: %{y}<extra></extra>'
                                    )
                                st.plotly_chart(fig_pend_mes, use_container_width=True, key="pendentes_mes_transportadora")
                            else:
                                st.info("✅ Nenhuma pendência nesta transportadora!")
                        else:
                            st.info("✅ Nenhuma pendência nesta transportadora!")
                    else:
                        st.markdown("**🚚 Pendentes por Transportadora**")
                        
                        if 'Transportador' in todas_pendentes_filtradas.columns:
                            pendentes_transp = todas_pendentes_filtradas['Transportador'].value_counts().head(10)
                            
                            # Ajustar posição do texto baseado no tamanho dos valores
                            posicoes, cores_texto = ajustar_posicao_texto(pendentes_transp.values.tolist())
                            
                            fig_pend_transp = px.bar(
                                x=pendentes_transp.values,
                                y=pendentes_transp.index,
                                orientation='h',
                                title="Notas Pendentes por Transportadora",
                                labels={'x': 'Quantidade', 'y': 'Transportadora'},
                                color=pendentes_transp.values,
                                color_continuous_scale='Reds',
                                text=pendentes_transp.values
                            )
                            fig_pend_transp.update_layout(height=400, showlegend=False, coloraxis_showscale=False)
                            
                            # Aplicar posições de texto inteligentes
                            if len(set(posicoes)) == 1:  # Se todas têm a mesma posição
                                fig_pend_transp.update_traces(
                                    textposition=posicoes[0],
                                    textfont=dict(color=cores_texto[0], size=11, family='Arial Black'),
                                    hovertemplate='<b>%{y}</b><br>Pendentes: %{x}<extra></extra>'
                                )
                            else:  # Posições mistas - usar auto
                                fig_pend_transp.update_traces(
                                    textposition='auto',
                                    textfont=dict(color='black', size=11, family='Arial Black'),
                                    hovertemplate='<b>%{y}</b><br>Pendentes: %{x}<extra></extra>'
                                )
                            st.plotly_chart(fig_pend_transp, use_container_width=True, key="pendentes_transportadora")
                        else:
                            st.info("Dados de transportadora não disponíveis")
                
                with col2:
                    st.markdown("**📅 Pendentes por Mês**")
                    
                    if 'Mês Nota' in todas_pendentes_filtradas.columns:
                        pendentes_mes = todas_pendentes_filtradas['Mês Nota'].value_counts()
                        pendentes_mes_ordenado = ordenar_meses(pendentes_mes)
                        
                        if not pendentes_mes_ordenado.empty:
                            # Ajustar posição do texto baseado no tamanho dos valores
                            posicoes, cores_texto = ajustar_posicao_texto(pendentes_mes_ordenado.values.tolist())
                            
                            fig_pend_mes = px.bar(
                                x=pendentes_mes_ordenado.index,
                                y=pendentes_mes_ordenado.values,
                                title="Notas Pendentes por Mês",
                                labels={'x': 'Mês', 'y': 'Quantidade'},
                                color=pendentes_mes_ordenado.values,
                                color_continuous_scale='Oranges',
                                text=pendentes_mes_ordenado.values
                            )
                            fig_pend_mes.update_layout(height=400, showlegend=False, coloraxis_showscale=False)
                            
                            # Aplicar posições de texto inteligentes
                            if len(set(posicoes)) == 1:  # Se todas têm a mesma posição
                                fig_pend_mes.update_traces(
                                    textposition=posicoes[0],
                                    textfont=dict(color=cores_texto[0], size=11, family='Arial Black'),
                                    hovertemplate='<b>%{x}</b><br>Pendentes: %{y}<extra></extra>'
                                )
                            else:  # Posições mistas - usar auto
                                fig_pend_mes.update_traces(
                                    textposition='auto',
                                    textfont=dict(color='black', size=11, family='Arial Black'),
                                    hovertemplate='<b>%{x}</b><br>Pendentes: %{y}<extra></extra>'
                                )
                            st.plotly_chart(fig_pend_mes, use_container_width=True, key="pendentes_mes_geral")
                        else:
                            st.info("✅ Nenhuma pendência encontrada!")
                    else:
                        st.info("Dados de mês não disponíveis")
                
                # Tabela detalhada das pendentes (usando dados filtrados)
                with st.expander(f"📋 Lista Detalhada de Notas Pendentes{' - ' + transportadora_filtro if transportadora_filtro != 'TODAS' else ''}"):
                    colunas_exibir = ['Numero', 'Transportador', 'Mês Nota', 'Previsão de Entrega', 'Data de Entrega', 'Status']
                    colunas_disponiveis = [col for col in colunas_exibir if col in todas_pendentes_filtradas.columns]
                    
                    if colunas_disponiveis and not todas_pendentes_filtradas.empty:
                        tabela_pendentes = todas_pendentes_filtradas[colunas_disponiveis].copy()
                        
                        # Formatar datas se disponíveis
                        if 'Previsão de Entrega' in tabela_pendentes.columns:
                            tabela_pendentes['Previsão de Entrega'] = pd.to_datetime(tabela_pendentes['Previsão de Entrega'], errors='coerce').dt.strftime('%d-%m-%Y')
                        if 'Data de Entrega' in tabela_pendentes.columns:
                            tabela_pendentes['Data de Entrega'] = pd.to_datetime(tabela_pendentes['Data de Entrega'], errors='coerce').dt.strftime('%d-%m-%Y')
                        
                        # Ordenar por transportadora e depois por mês
                        if 'Transportador' in tabela_pendentes.columns:
                            tabela_pendentes = tabela_pendentes.sort_values(['Transportador', 'Mês Nota'] if 'Mês Nota' in tabela_pendentes.columns else ['Transportador'])
                        
                        st.dataframe(
                            tabela_pendentes, 
                            use_container_width=True,
                            hide_index=True,
                            height=400
                        )
                    else:
                        st.info("✅ Nenhuma nota pendente encontrada para os filtros aplicados!")
                
                # Insights e ações (usando dados filtrados)
                st.markdown("### 💡 Insights e Ações Recomendadas")
                
                if not todas_pendentes_filtradas.empty and 'Transportador' in todas_pendentes_filtradas.columns:
                    if transportadora_filtro != "TODAS":
                        # Insights específicos da transportadora selecionada
                        total_transportadora = len(sla[sla['Transportador'] == transportadora_filtro]) if transportadora_filtro in sla['Transportador'].values else 1
                        
                        st.error(f"""
                        **🚨 Situação da Transportadora {transportadora_filtro}:**
                        - **{len(todas_pendentes_filtradas)} notas pendentes** 
                        - **{len(notas_pendentes_filtradas)} sem data de entrega** | **{len(notas_atrasadas_filtradas)} entregues atrasadas**
                        - **{pct_pendentes:.1f}%** das entregas desta transportadora estão pendentes
                        """)
                        
                        st.warning(f"""
                        **⚡ Ações Específicas para {transportadora_filtro}:**
                        - Contato imediato para esclarecimentos sobre as {len(todas_pendentes_filtradas)} pendências
                        - Solicitar cronograma de regularização
                        - Avaliar penalidades contratuais aplicáveis
                        - Considerar suspensão temporária de novos envios
                        """)
                    else:
                        # Insights gerais (quando "TODAS" está selecionado)
                        pior_transportadora = todas_pendentes_filtradas['Transportador'].value_counts().index[0]
                        qtd_pior = todas_pendentes_filtradas['Transportador'].value_counts().iloc[0]
                        
                        st.error(f"""
                        **🚨 Situação Crítica Geral:**
                        - **{pior_transportadora}** tem **{qtd_pior} notas pendentes** (maior volume)
                        - Total de **{len(todas_pendentes_filtradas)} notas** necessitam atenção imediata
                        - **{pct_pendentes:.1f}%** do total de entregas estão pendentes
                        """)
                        
                        st.warning(f"""
                        **⚡ Ações Recomendadas:**
                        - Priorizar contato com a transportadora **{pior_transportadora}**
                        - Revisar contratos e penalidades de SLA
                        - Implementar monitoramento em tempo real
                        - Considerar transportadoras alternativas para novos envios
                        """)
                else:
                    st.success(f"""
                    **🎉 Excelente!**
                    - {'Nenhuma pendência para a transportadora selecionada!' if transportadora_filtro != 'TODAS' else 'Nenhuma nota pendente no momento!'}
                    - Continue o bom trabalho de monitoramento!
                    """)
                
            else:
                st.success("🎉 Parabéns! Não há notas pendentes de entrega no momento!")
        else:
            st.info("📊 Dados necessários para análise de pendências não disponíveis")
    
    # ===== ABA 4: ANÁLISE OPERACIONAL =====
    with tab4:
        st.header("📦 Volumetria")
        st.markdown("Análise detalhada de operações, custos e eficiência.")
        
        if sla is not None:
            # Exibir informações básicas dos dados
            st.success(f"✅ Dados carregados com sucesso! Total de {len(sla)} registros")
            
            # ===== ABAS PRINCIPAIS =====
            tab1, tab2 = st.tabs(["🗺️ Por Estado", "🌎 Por Região"])
            
            with tab1:
                st.markdown("### 📍 Análise por Estado")
                
                if all(col in sla.columns for col in ['Estado Destino', 'Faixa de Peso']):
                    # Filtro por estado (multiselect)
                    estados_disponiveis = sorted(sla['Estado Destino'].dropna().unique().tolist())
                    
                    estados_selecionados = st.multiselect(
                        "🗺️ Selecione os Estados para Análise:",
                        options=estados_disponiveis,
                        default=estados_disponiveis,  # Todos selecionados por padrão
                        key="filtro_peso_estado",
                        help="Selecione um ou mais estados. Vazio = todos os estados."
                    )
                    
                    # Se nenhum selecionado, usar todos
                    if not estados_selecionados:
                        estados_selecionados = estados_disponiveis
                    
                    # Aplicar filtro multiselect
                    if len(estados_selecionados) < len(estados_disponiveis):
                        dados_filtrados = sla[sla['Estado Destino'].isin(estados_selecionados)].copy()
                        titulo_estado = f"Estados: {', '.join(estados_selecionados[:3])}" + ("..." if len(estados_selecionados) > 3 else "")
                    else:
                        dados_filtrados = sla.copy()
                        titulo_estado = "TODOS"
                    
                    if not dados_filtrados.empty and 'Faixa de Peso' in dados_filtrados.columns:
                        # Calcular distribuição por faixa de peso
                        faixa_peso_counts = dados_filtrados['Faixa de Peso'].value_counts()
                        total_entregas = len(dados_filtrados)
                        
                        if not faixa_peso_counts.empty:
                            # Preparar dados para o gráfico de pizza
                            faixas = faixa_peso_counts.index.tolist()
                            percentuais = (faixa_peso_counts.values / total_entregas * 100).round(1)
                            
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                # Criar gráfico de barras horizontais
                                fig_barras = px.bar(
                                    x=faixa_peso_counts.values,
                                    y=faixa_peso_counts.index,
                                    orientation='h',
                                    title=f"🎯 Distribuição por Faixa de Peso - {titulo_estado}",
                                    labels={'x': 'Quantidade de Entregas', 'y': 'Faixa de Peso'},
                                    color=faixa_peso_counts.values,
                                    color_continuous_scale='jet'
                                )
                                
                                fig_barras.update_traces(
                                    text=[f'{val} ({(val/total_entregas*100):.1f}%)' for val in faixa_peso_counts.values],
                                    textposition='outside',
                                    textfont=dict(color='black', size=10, family='Arial Black'),
                                    hovertemplate='<b>%{y}</b><br>' +
                                                  'Quantidade: %{x}<br>' +
                                                  'Percentual: %{text}<br>' +
                                                  '<extra></extra>'
                                )
                                
                                fig_barras.update_layout(
                                    height=500,
                                    showlegend=False,
                                    coloraxis_showscale=False,
                                    title=dict(
                                        x=0.5,
                                        font=dict(size=14, family="Arial Black")
                                    ),
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    xaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray'),
                                    yaxis=dict(showgrid=False),
                                    margin=dict(l=20, r=80, t=60, b=20)
                                )
                                
                                st.plotly_chart(fig_barras, use_container_width=True, key="faixa_peso_estado")
                            
                            with col2:
                                # Métricas complementares
                                st.markdown("### 📊 Estatísticas")
                                
                                # Faixa predominante
                                faixa_principal = faixa_peso_counts.index[0]
                                pct_principal = percentuais[list(faixas).index(faixa_principal)]
                                
                                st.metric("🎯 Faixa Predominante", faixa_principal)
                                st.metric("📊 Participação", f"{pct_principal:.1f}%")
                                st.metric("📦 Total de Entregas", f"{total_entregas:,}".replace(",", "."))
                                
                                # Informações adicionais
                                if 'Peso Bruto NF' in dados_filtrados.columns:
                                    peso_medio = dados_filtrados['Peso Bruto NF'].mean()
                                    if not pd.isna(peso_medio):
                                        st.metric("⚖️ Peso Médio", f"{peso_medio:.1f} kg")
                                
                                # Top 3 faixas
                                st.markdown("#### 🏆 Top 3 Faixas")
                                for i, (faixa, count) in enumerate(faixa_peso_counts.head(3).items(), 1):
                                    pct = (count / total_entregas * 100)
                                    st.write(f"**{i}º** {faixa}: {pct:.1f}%")
                            
                            # Tabela detalhada
                            with st.expander(f"📋 Distribuição Detalhada - {titulo_estado}"):
                                # Criar tabela com dados completos
                                tabela_faixas = pd.DataFrame({
                                    'Faixa de Peso': faixa_peso_counts.index,
                                    'Quantidade': faixa_peso_counts.values,
                                    'Percentual (%)': percentuais
                                })
                                
                                # Ordenar por quantidade (maior para menor)
                                tabela_faixas = tabela_faixas.sort_values('Quantidade', ascending=False)
                                
                                st.dataframe(
                                    tabela_faixas,
                                    use_container_width=True,
                                    hide_index=True,
                                    height=300
                                )
                            
                            # Insights automáticos
                            st.markdown("### 💡 Insights da Análise")
                            
                            # Análise de concentração
                            concentracao_top3 = sum(percentuais[:3]) if len(percentuais) >= 3 else sum(percentuais)
                            
                            if len(estados_selecionados) < len(estados_disponiveis):
                                if len(estados_selecionados) == 1:
                                    # Análise de estado único
                                    st.info(f"""
                                    **📊 Perfil de Entregas - {estados_selecionados[0]}:**
                                    - **Faixa principal**: {faixa_principal} ({pct_principal:.1f}%)
                                    - **Concentração**: Top 3 faixas representam {concentracao_top3:.1f}% das entregas
                                    - **Diversificação**: {len(faixas)} faixas de peso diferentes atendidas
                                    """)
                                else:
                                    # Análise de múltiplos estados
                                    st.info(f"""
                                    **📊 Perfil de Entregas - {len(estados_selecionados)} Estados:**
                                    - **Estados**: {', '.join(estados_selecionados[:5])}{'...' if len(estados_selecionados) > 5 else ''}
                                    - **Faixa principal**: {faixa_principal} ({pct_principal:.1f}%)
                                    - **Concentração**: Top 3 faixas representam {concentracao_top3:.1f}% das entregas
                                    - **Diversificação**: {len(faixas)} faixas de peso diferentes
                                    """)
                                
                                # Recomendações baseadas na faixa principal
                                if "0 a 10" in faixa_principal or "até 20" in faixa_principal:
                                    st.success("✈️ **Perfil Leve**: Ideal para transportadoras expressas e aéreas")
                                elif "acima de 100" in faixa_principal or "até 75" in faixa_principal:
                                    st.warning("🚛 **Perfil Pesado**: Requer transportadoras especializadas em carga")
                                else:
                                    st.info("📦 **Perfil Médio**: Adequado para transportadoras convencionais")
                            else:
                                st.info(f"""
                                **📊 Perfil Geral Nacional:**
                                - **Faixa predominante**: {faixa_principal} ({pct_principal:.1f}%)
                                - **Concentração nacional**: {concentracao_top3:.1f}% em 3 principais faixas
                                - **Diversidade logística**: {len(faixas)} faixas atendidas nacionalmente
                                """)
                        else:
                            st.info("📊 Dados de faixa de peso não disponíveis para o estado selecionado")
                    else:
                        st.info("📊 Dados insuficientes para análise de faixa de peso")
                else:
                    st.info("📊 Colunas necessárias (Estado Destino, Faixa de Peso) não disponíveis")
            
            with tab2:
                st.markdown("### 🌎 Análise por Região")
                
                if all(col in sla.columns for col in ['Região', 'Faixa de Peso']):
                    # Filtro por região (multiselect)
                    regioes_disponiveis = sorted(sla['Região'].dropna().unique().tolist())
                    
                    regioes_selecionadas = st.multiselect(
                        "🌎 Selecione as Regiões para Análise:",
                        options=regioes_disponiveis,
                        default=regioes_disponiveis,  # Todas selecionadas por padrão
                        key="filtro_peso_regiao",
                        help="Selecione uma ou mais regiões. Vazio = todas as regiões."
                    )
                    
                    # Se nenhuma selecionada, usar todas
                    if not regioes_selecionadas:
                        regioes_selecionadas = regioes_disponiveis
                    
                    # Aplicar filtro multiselect
                    if len(regioes_selecionadas) < len(regioes_disponiveis):
                        dados_filtrados_regiao = sla[sla['Região'].isin(regioes_selecionadas)].copy()
                        titulo_regiao = f"Regiões: {', '.join(regioes_selecionadas[:3])}" + ("..." if len(regioes_selecionadas) > 3 else "")
                    else:
                        dados_filtrados_regiao = sla.copy()
                        titulo_regiao = "TODAS"
                    
                    if not dados_filtrados_regiao.empty and 'Faixa de Peso' in dados_filtrados_regiao.columns:
                        # Calcular distribuição por faixa de peso por região
                        faixa_peso_counts_regiao = dados_filtrados_regiao['Faixa de Peso'].value_counts()
                        total_entregas_regiao = len(dados_filtrados_regiao)
                        
                        if not faixa_peso_counts_regiao.empty:
                            # Preparar dados para o gráfico de pizza
                            faixas_regiao = faixa_peso_counts_regiao.index.tolist()
                            percentuais_regiao = (faixa_peso_counts_regiao.values / total_entregas_regiao * 100).round(1)
                            
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                # Criar gráfico de barras horizontais para região
                                fig_barras_regiao = px.bar(
                                    x=faixa_peso_counts_regiao.values,
                                    y=faixa_peso_counts_regiao.index,
                                    orientation='h',
                                    title=f"🎯 Distribuição por Faixa de Peso - {titulo_regiao}",
                                    labels={'x': 'Quantidade de Entregas', 'y': 'Faixa de Peso'},
                                    color=faixa_peso_counts_regiao.values,
                                    color_continuous_scale='jet'
                                )
                                
                                fig_barras_regiao.update_traces(
                                    text=[f'{val} ({(val/total_entregas_regiao*100):.1f}%)' for val in faixa_peso_counts_regiao.values],
                                    textposition='outside',
                                    textfont=dict(color='black', size=10, family='Arial Black'),
                                    hovertemplate='<b>%{y}</b><br>' +
                                                  'Quantidade: %{x}<br>' +
                                                  'Percentual: %{text}<br>' +
                                                  '<extra></extra>'
                                )
                                
                                fig_barras_regiao.update_layout(
                                    height=500,
                                    showlegend=False,
                                    coloraxis_showscale=False,
                                    title=dict(
                                        x=0.5,
                                        font=dict(size=14, family="Arial Black")
                                    ),
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    xaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray'),
                                    yaxis=dict(showgrid=False),
                                    margin=dict(l=20, r=80, t=60, b=20)
                                )
                                
                                st.plotly_chart(fig_barras_regiao, use_container_width=True, key="faixa_peso_regiao")
                            
                            with col2:
                                # Métricas complementares para região
                                st.markdown("### 📊 Estatísticas Regionais")
                                
                                # Faixa predominante da região
                                faixa_principal_regiao = faixa_peso_counts_regiao.index[0]
                                pct_principal_regiao = percentuais_regiao[list(faixas_regiao).index(faixa_principal_regiao)]
                                
                                st.metric("🎯 Faixa Predominante", faixa_principal_regiao)
                                st.metric("📊 Participação", f"{pct_principal_regiao:.1f}%")
                                st.metric("📦 Total de Entregas", f"{total_entregas_regiao:,}".replace(",", "."))
                                
                                # Informações adicionais da região
                                if 'Peso Bruto NF' in dados_filtrados_regiao.columns:
                                    peso_medio_regiao = dados_filtrados_regiao['Peso Bruto NF'].mean()
                                    if not pd.isna(peso_medio_regiao):
                                        st.metric("⚖️ Peso Médio", f"{peso_medio_regiao:.1f} kg")
                                
                                # Estados da região (se não for "TODAS")
                                if len(regioes_selecionadas) < len(regioes_disponiveis) and 'Estado Destino' in dados_filtrados_regiao.columns:
                                    estados_na_regiao = dados_filtrados_regiao['Estado Destino'].nunique()
                                    st.metric("🗺️ Estados Atendidos", estados_na_regiao)
                                
                                # Top 3 faixas da região
                                st.markdown("#### 🏆 Top 3 Faixas")
                                for i, (faixa, count) in enumerate(faixa_peso_counts_regiao.head(3).items(), 1):
                                    pct = (count / total_entregas_regiao * 100)
                                    st.write(f"**{i}º** {faixa}: {pct:.1f}%")
                            
                            # Tabela detalhada da região
                            with st.expander(f"📋 Distribuição Detalhada - {titulo_regiao}"):
                                # Criar tabela com dados completos da região
                                tabela_faixas_regiao = pd.DataFrame({
                                    'Faixa de Peso': faixa_peso_counts_regiao.index,
                                    'Quantidade': faixa_peso_counts_regiao.values,
                                    'Percentual (%)': percentuais_regiao
                                })
                                
                                # Ordenar por quantidade (maior para menor)
                                tabela_faixas_regiao = tabela_faixas_regiao.sort_values('Quantidade', ascending=False)
                                
                                st.dataframe(
                                    tabela_faixas_regiao,
                                    use_container_width=True,
                                    hide_index=True,
                                    height=300
                                )
                            
                            # Insights automáticos da região
                            st.markdown("### 💡 Insights da Análise Regional")
                            
                            # Análise de concentração da região
                            concentracao_top3_regiao = sum(percentuais_regiao[:3]) if len(percentuais_regiao) >= 3 else sum(percentuais_regiao)
                            
                            if len(regioes_selecionadas) < len(regioes_disponiveis):
                                if len(regioes_selecionadas) == 1:
                                    # Análise de região única
                                    st.info(f"""
                                    **🌎 Perfil Regional - {regioes_selecionadas[0]}:**
                                    - **Faixa principal**: {faixa_principal_regiao} ({pct_principal_regiao:.1f}%)
                                    - **Concentração regional**: Top 3 faixas representam {concentracao_top3_regiao:.1f}% das entregas
                                    - **Variedade logística**: {len(faixas_regiao)} faixas de peso diferentes
                                    """)
                                else:
                                    # Análise de múltiplas regiões
                                    st.info(f"""
                                    **🌎 Perfil Regional - {len(regioes_selecionadas)} Regiões:**
                                    - **Regiões**: {', '.join(regioes_selecionadas)}
                                    - **Faixa principal**: {faixa_principal_regiao} ({pct_principal_regiao:.1f}%)
                                    - **Concentração**: Top 3 faixas representam {concentracao_top3_regiao:.1f}% das entregas
                                    - **Variedade logística**: {len(faixas_regiao)} faixas de peso diferentes
                                    """)
                                
                                # Recomendações baseadas na faixa principal da região
                                if "0 a 10" in faixa_principal_regiao or "até 20" in faixa_principal_regiao:
                                    st.success("✈️ **Perfil Leve**: Adequada para hub de distribuição expressa")
                                elif "acima de 100" in faixa_principal_regiao or "até 75" in faixa_principal_regiao:
                                    st.warning("🚛 **Perfil Pesado**: Necessita infraestrutura robusta para carga")
                                else:
                                    st.info("📦 **Perfil Equilibrado**: Demanda logística diversificada")
                            else:
                                st.info(f"""
                                **🌎 Perfil Nacional por Regiões:**
                                - **Faixa predominante**: {faixa_principal_regiao} ({pct_principal_regiao:.1f}%)
                                - **Concentração nacional**: {concentracao_top3_regiao:.1f}% em 3 principais faixas
                                - **Diversidade Brasil**: {len(faixas_regiao)} faixas atendidas em todas as regiões
                                """)
                        else:
                            st.info("📊 Dados de faixa de peso não disponíveis para a região selecionada")
                    else:
                        st.info("📊 Dados insuficientes para análise de faixa de peso por região")
                else:
                    st.info("📊 Colunas necessárias (Região, Faixa de Peso) não disponíveis")
            
            # Nona linha - Volume mensal geral
            if 'Mês Nota' in sla.columns:
                st.subheader("📊 Volume Geral de Entregas por Mês")
                
                mensal = sla['Mês Nota'].value_counts()
                mensal_ordenado = ordenar_meses(mensal)
                
                # Ajustar posição do texto baseado no tamanho dos valores
                posicoes, cores_texto = ajustar_posicao_texto(mensal_ordenado.values.tolist())
                
                fig_mensal = px.bar(
                    x=mensal_ordenado.index,
                    y=mensal_ordenado.values,
                    title="Volume Total de NFs por Mês",
                    labels={'x': 'Mês', 'y': 'Quantidade de NFs'},
                    color=mensal_ordenado.values,
                    color_continuous_scale='Blues',
                    text=mensal_ordenado.values
                )
                fig_mensal.update_layout(height=300, showlegend=False, coloraxis_showscale=False)
                
                # Aplicar posições de texto inteligentes
                if len(set(posicoes)) == 1:  # Se todas têm a mesma posição
                    fig_mensal.update_traces(
                        textposition=posicoes[0],
                        textfont=dict(color=cores_texto[0], size=11, family='Arial Black'),
                        hovertemplate='<b>%{x}</b><br>Volume: %{y} NFs<extra></extra>'
                    )
                else:  # Posições mistas - usar auto
                    fig_mensal.update_traces(
                        textposition='auto',
                        textfont=dict(color='black', size=11, family='Arial Black'),
                        hovertemplate='<b>%{x}</b><br>Volume: %{y} NFs<extra></extra>'
                    )
                st.plotly_chart(fig_mensal, use_container_width=True, key="volume_mensal_operacional")
                
    # ===== ABA 5: BUSCA NF =====
    with tab5:
        st.header("🔍 Buscar Nota Fiscal")
        st.markdown("Utilize esta ferramenta para localizar informações específicas de uma nota fiscal.")
        
        numero_nf = st.text_input("Digite o número da Nota Fiscal:", placeholder="Ex: 123456")
        
        if numero_nf:
            # Converter para string para comparação
            numero_nf_str = str(numero_nf)
            
            # Filtrar dados baseado no número da NF
            resultado = sla[sla['Numero'].astype(str).str.contains(numero_nf_str, case=False, na=False)]
            
            if not resultado.empty:
                st.success(f"🎯 Encontradas {len(resultado)} nota(s) fiscal(is)")
                
                # Para cada resultado encontrado
                for idx, row in resultado.iterrows():
                    st.markdown(f"### 📋 Nota Fiscal: {row['Numero']}")
                    
                    # Função para formatar datas (mantida para as métricas)
                    def format_date(date_value):
                        if pd.isna(date_value) or date_value == '' or str(date_value) == 'N/A':
                            return 'N/A'
                        try:
                            if isinstance(date_value, str):
                                # Se já é string, tentar converter
                                date_obj = pd.to_datetime(date_value, errors='coerce')
                            else:
                                date_obj = date_value
                            
                            if pd.isna(date_obj):
                                return str(date_value)
                            
                            return date_obj.strftime('%d-%m-%Y')
                        except:
                            return str(date_value)
                    
                    # Função para formatar romaneio
                    def format_romaneio(romaneio_value):
                        if pd.isna(romaneio_value) or romaneio_value == '':
                            return 'N/A'
                        try:
                            # Se é float, converter para int para remover .0
                            if isinstance(romaneio_value, float):
                                return str(int(romaneio_value))
                            return str(romaneio_value)
                        except:
                            return str(romaneio_value)
                    
                    # Layout principal: Timeline + Métricas
                    col_metricas, col_timeline = st.columns([1, 1])
                    
                    with col_timeline:
                        st.markdown("#### 🚛 Rastreamento da Entrega")
                        
                        # Exibir timeline usando componentes nativos do Streamlit
                        etapas, soma_real_dias = criar_timeline_entrega(row)
                        
                        for i, etapa in enumerate(etapas):
                            # Definir cores baseadas no status
                            if etapa['status'] == 'concluido':
                                cor_fundo = "#d4edda"  # Verde claro
                                cor_borda = "#28a745"  # Verde
                                cor_texto = "#155724"  # Verde escuro
                            else:
                                cor_fundo = "#f8f9fa"  # Cinza claro
                                cor_borda = "#dee2e6"  # Cinza
                                cor_texto = "#6c757d"  # Cinza escuro
                            
                            # Container para cada etapa
                            container = st.container()
                            with container:
                                # Usar HTML simples para melhor controle visual
                                data_texto = etapa['data'] if etapa['data'] else 'Não informado'
                                duracao_texto = etapa.get('duracao', None)
                                
                                # Criar texto da duração se disponível
                                info_adicional = []
                                if data_texto != 'Não informado':
                                    info_adicional.append(data_texto)
                                if duracao_texto:
                                    info_adicional.append(f"⏱️ {duracao_texto}")
                                
                                texto_completo = " • ".join(info_adicional) if info_adicional else "Não informado"
                                
                                etapa_html = f"""
                                <div style="
                                    display: flex;
                                    align-items: center;
                                    margin: 10px 0;
                                    padding: 12px;
                                    background-color: {cor_fundo};
                                    border-left: 4px solid {cor_borda};
                                    border-radius: 8px;
                                    font-family: 'Source Sans Pro', sans-serif;
                                ">
                                    <div style="
                                        font-size: 24px;
                                        margin-right: 12px;
                                        min-width: 30px;
                                    ">
                                        {etapa['icon']}
                                    </div>
                                    <div style="flex-grow: 1;">
                                        <div style="
                                            font-weight: 600;
                                            color: {cor_texto};
                                            font-size: 14px;
                                            margin-bottom: 4px;
                                        ">
                                            {etapa['titulo']}
                                        </div>
                                        <div style="
                                            color: {cor_texto};
                                            font-size: 13px;
                                            opacity: 0.8;
                                        ">
                                            {texto_completo}
                                        </div>
                                    </div>
                                </div>
                                """
                                
                                st.markdown(etapa_html, unsafe_allow_html=True)
                                
                                # Adicionar linha conectora (exceto para o último item)
                                if i < len(etapas) - 1:
                                    st.markdown("""
                                    <div style="
                                        margin-left: 15px;
                                        width: 2px;
                                        height: 10px;
                                        background-color: #dee2e6;
                                    "></div>
                                    """, unsafe_allow_html=True)
                    
                    with col_metricas:
                        st.markdown("#### 📊 Informações Detalhadas")
                        
                        # Organizar métricas em sub-colunas
                        subcol1, subcol2 = st.columns(2)
                        
                        with subcol1:
                            st.metric(
                                label="🏢 BU",
                                value=str(row.get('Unid Negoc', 'N/A'))
                            )
                            
                            st.metric(
                                label="📦 Romaneio",
                                value=format_romaneio(row.get('Nr Romaneio', 'N/A'))
                            )

                        with subcol2:
                            st.metric(
                                label="🚚 Transportador",
                                value=str(row.get('Transportador', 'N/A'))
                            )
                            
                            st.metric(
                                label="⚡ Status",
                                value=str(row.get('Status', 'N/A'))
                            )
                        
                        # Métricas de tempo
                        col_lead, col_real = st.columns(2)
                        
                        with col_lead:
                            # Lead Time (previsto)
                            lead_time_valor = row.get('Lead Time', 'N/A')
                            if pd.notna(lead_time_valor) and lead_time_valor != 'N/A':
                                lead_time_formatado = f"{int(lead_time_valor)} dias"
                            else:
                                lead_time_formatado = 'N/A'
                            
                            st.metric(
                                label="⏱️ Lead Time (Previsto)",
                                value=lead_time_formatado
                            )
                        
                        with col_real:
                            # Tempo Real (soma das etapas)
                            if soma_real_dias is not None:
                                tempo_real_formatado = f"{soma_real_dias} dias"
                                # Calcular diferença vs Lead Time para mostrar delta
                                if pd.notna(lead_time_valor) and lead_time_valor != 'N/A':
                                    diferenca = soma_real_dias - int(lead_time_valor)
                                    delta_texto = f"{diferenca:+d}" if diferenca != 0 else "0"
                                else:
                                    delta_texto = None
                            else:
                                tempo_real_formatado = 'N/A'
                                delta_texto = None
                            
                            st.metric(
                                label="🕐 Tempo Real (Corridos)",
                                value=tempo_real_formatado,
                                delta=delta_texto,
                                help="Soma de: Faturamento + Despacho + Entrega (dias corridos)"
                            )
                    
                    # Separador entre resultados se houver múltiplas NFs
                    if len(resultado) > 1:
                        st.markdown("---")
            else:
                st.warning(f"❌ Nenhuma nota fiscal encontrada com o número '{numero_nf}'")
else:
    st.error("❌ Nenhum arquivo foi carregado. Faça upload de um arquivo Excel válido para continuar.")


