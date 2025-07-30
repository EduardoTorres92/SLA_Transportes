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
    dt_implant = format_date_timeline(row.get('Dt Implant Ped'))
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
            'titulo': '📝 Implantação do Pedido',
            'data': dt_implant,
            'duracao': None,  # Sem cálculo de dias, apenas a data
            'status': 'concluido' if dt_implant else 'pendente',
            'icon': '✅' if dt_implant else '⭕'
        },
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
            st.markdown("### 📋 Todas as Colunas Disponíveis")
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
        bus_excluidas = []
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
    # Manter uma cópia dos dados originais para a busca de nota fiscal
    sla_original = sla.copy()
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
        "📦 Volumetria",
        "🎯 Performance SLA", 
        "🚨 Gestão de Pendências", 
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
    
    # ===== ABA 2: VOLUMETRIA =====
    with tab2:
        st.header("📦 Volumetria")
        st.markdown("Análise de volume de entregas por transportadora, estado e região.")
        
        if sla is not None:
            # Exibir informações básicas dos dados
            st.success(f"✅ Dados carregados com sucesso! Total de {len(sla)} registros")
            
            # ===== ABAS DE VOLUMETRIA =====
            tab_estado, tab_regiao = st.tabs(["🗺️ Por Estado", "🌎 Por Região"])
            
            with tab_estado:
                st.markdown("### 📍 Análise por Estado")
                
                if 'Estado Destino' in sla.columns:
                    # Análise de volume por estado
                    volume_estados = sla['Estado Destino'].value_counts().head(10)
                    
                    if not volume_estados.empty:
                        fig_estados = px.bar(
                            x=volume_estados.values,
                            y=volume_estados.index,
                            orientation='h',
                            title="📍 Top 10 Estados por Volume",
                            labels={'x': 'Quantidade de Entregas', 'y': 'Estado'}
                        )
                        fig_estados.update_layout(height=500)
                        st.plotly_chart(fig_estados, use_container_width=True)
                        
                        # Tabela detalhada
                        st.dataframe(volume_estados.to_frame(name='Volume de Entregas'), use_container_width=True)
                    else:
                        st.info("📊 Dados de Estado Destino não disponíveis")
                else:
                    st.info("📊 Coluna Estado Destino não encontrada")
                    
            with tab_regiao:
                st.markdown("### 🌎 Análise por Região")
                
                if 'Transportador' in sla.columns:
                    # Análise de volume por transportadora
                    volume_transp = sla['Transportador'].value_counts().head(10)
                    
                    if not volume_transp.empty:
                        fig_transp = px.bar(
                            x=volume_transp.values,
                            y=volume_transp.index,
                            orientation='h',
                            title="🚚 Top 10 Transportadoras por Volume",
                            labels={'x': 'Quantidade de Entregas', 'y': 'Transportadora'}
                        )
                        fig_transp.update_layout(height=500)
                        st.plotly_chart(fig_transp, use_container_width=True)
                        
                        # Tabela detalhada
                        st.dataframe(volume_transp.to_frame(name='Volume de Entregas'), use_container_width=True)
                    else:
                        st.info("📊 Dados de Transportador não disponíveis")
                else:
                    st.info("📊 Coluna Transportador não encontrada")
        else:
            st.info("📊 Dados não disponíveis para análise de volumetria")
    
    # ===== ABA 3: PERFORMANCE SLA =====
    with tab3:
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
                
                # Performance por transportadora
                performance_transp = entregas_realizadas.groupby(['Transportador', 'Status_Entrega']).size().unstack(fill_value=0)
                
                if 'Entregue no Prazo' in performance_transp.columns:
                    performance_transp['Total'] = performance_transp.sum(axis=1)
                    performance_transp['% SLA'] = (performance_transp['Entregue no Prazo'] / performance_transp['Total'] * 100).round(1)
                    
                    # Filtrar transportadoras com pelo menos 10 entregas
                    transp_relevantes = performance_transp[performance_transp['Total'] >= 10]
                    
                    if not transp_relevantes.empty:
                        # Gráfico de performance
                        transp_ordenada = transp_relevantes.sort_values('% SLA', ascending=True)
                        
                        fig = px.bar(
                            x=transp_ordenada['% SLA'],
                            y=transp_ordenada.index,
                            orientation='h',
                            title="🎯 Performance SLA por Transportadora",
                            labels={'x': '% SLA Atingido', 'y': 'Transportadora'},
                            color=transp_ordenada['% SLA'],
                            color_continuous_scale='RdYlGn'
                        )
                        fig.update_layout(height=500, showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Tabela de performance
                        tabela_exibir = transp_ordenada[['Entregue no Prazo', 'Entregue Atrasada', 'Total', '% SLA']].copy()
                        tabela_exibir = tabela_exibir.rename(columns={
                            'Entregue no Prazo': '✅ No Prazo',
                            'Entregue Atrasada': '❌ Atrasada',
                            'Total': '📦 Total',
                            '% SLA': '🎯 % SLA'
                        })
                        st.dataframe(tabela_exibir.sort_values('🎯 % SLA', ascending=False), use_container_width=True)
                    else:
                        st.info("📊 Nenhuma transportadora com volume suficiente (min. 10 entregas)")
                else:
                    st.info("📊 Dados insuficientes para calcular performance")
            else:
                st.info("📊 Não há dados suficientes de entregas realizadas")
        else:
            st.info("📊 Dados necessários para análise de performance não disponíveis")
    
    # ===== ABA 4: GESTÃO DE PENDÊNCIAS =====
    with tab4:
        st.header("🚨 Gestão de Pendências")
        st.markdown("Análise e gerenciamento de notas fiscais pendentes de entrega.")
        
        if all(col in sla.columns for col in ['Data de Entrega', 'Previsão de Entrega', 'Transportador']):
            # Identificar notas pendentes
            notas_pendentes = sla[sla['Data de Entrega'].isna()].copy()
            
            # Notas atrasadas (entregues após a previsão)
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
                # Métricas principais
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("🔴 Total Pendentes", len(todas_pendentes))
                    
                with col2:
                    st.metric("⏰ Sem Data Entrega", len(notas_pendentes))
                    
                with col3:
                    st.metric("📅 Entregues Atrasadas", len(notas_atrasadas))
                
                # Gráfico por transportadora
                if 'Transportador' in todas_pendentes.columns:
                    pendentes_transp = todas_pendentes['Transportador'].value_counts().head(10)
                    
                    if not pendentes_transp.empty:
                        fig = px.bar(
                            x=pendentes_transp.values,
                            y=pendentes_transp.index,
                            orientation='h',
                            title="🚚 Notas Pendentes por Transportadora",
                            labels={'x': 'Quantidade', 'y': 'Transportadora'},
                            color=pendentes_transp.values,
                            color_continuous_scale='Reds'
                        )
                        fig.update_layout(height=500, showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Tabela detalhada
                        st.dataframe(pendentes_transp.to_frame(name='Notas Pendentes'), use_container_width=True)
                    else:
                        st.info("📊 Dados de transportadora não disponíveis")
                else:
                    st.info("📊 Coluna Transportador não encontrada")
            else:
                st.success("🎉 Parabéns! Não há notas pendentes de entrega no momento!")
        else:
            st.info("📊 Dados necessários para análise de pendências não disponíveis")
                
    # ===== ABA 5: BUSCA NF =====
    with tab5:
        st.header("🔍 Buscar Nota Fiscal")
        st.markdown("Utilize esta ferramenta para localizar informações específicas de uma nota fiscal.")
        
        numero_nf = st.text_input("Digite o número da Nota Fiscal:", placeholder="Ex: 123456")
        
        if numero_nf:
            # Converter para string para comparação
            numero_nf_str = str(numero_nf)
            
            # Filtrar dados baseado no número da NF (usar dados originais, não filtrados)
            resultado = sla_original[sla_original['Numero'].astype(str).str.contains(numero_nf_str, case=False, na=False)]
            
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
                                if duracao_texto and duracao_texto != 'None':
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
                            # Tempo Total (soma das etapas)
                            if soma_real_dias is not None:
                                tempo_total_formatado = f"{soma_real_dias} dias"
                            else:
                                tempo_total_formatado = 'N/A'
                            
                            st.metric(
                                label="🕐 Tempo Total",
                                value=tempo_total_formatado,
                                help="Soma de: Faturamento + Despacho + Entrega (dias corridos)"
                            )
                    
                    # Separador entre resultados se houver múltiplas NFs
                    if len(resultado) > 1:
                        st.markdown("---")
            else:
                st.warning(f"❌ Nenhuma nota fiscal encontrada com o número '{numero_nf}'")
else:
    st.error("❌ Nenhum arquivo foi carregado. Faça upload de um arquivo Excel válido para continuar.")


