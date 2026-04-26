"""
Sistema de Análise Financeira - Organizador de Extratos Bancários
Autor: IA Generativa
Versão: 1.0
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import re
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Analisador Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .positive {
        color: #00C853;
        font-weight: bold;
    }
    .negative {
        color: #D50000;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class FinancialAnalyzer:
    """Classe principal para análise financeira"""
    
    def __init__(self):
        self.df = None
        self.categories = self._load_categories()
    
    def _load_categories(self):
        """Dicionário para classificação automática de transações"""
        return {
            # Entradas
            'salario': ['salário', 'salario', 'remuneração', 'holerite', 'pagamento de salário'],
            'transferencia': ['transferência', 'transferencia', 'ted', 'doc', 'pix recebido'],
            'investimento': ['dividendo', 'rendimento', 'juros', 'aplicação', 'resgate'],
            'reembolso': ['reembolso', 'estorno', 'devolução', 'restituição'],
            
            # Saídas
            'alimentacao': ['mercado', 'supermercado', 'feira', 'restaurante', 'padaria', 'ifood', 'rappi', 'comida'],
            'transporte': ['uber', 'taxi', 'combustível', 'gasolina', 'estacionamento', 'pedágio', '99pop'],
            'moradia': ['aluguel', 'condomínio', 'luz', 'energia', 'água', 'gás', 'internet', 'telefone'],
            'saude': ['farmácia', 'médico', 'consulta', 'exame', 'plano de saúde', 'hospital'],
            'educacao': ['faculdade', 'curso', 'escola', 'livro', 'material', 'mensalidade'],
            'lazer': ['cinema', 'teatro', 'show', 'viagem', 'hotel', 'hobby', 'streaming', 'netflix'],
            'compras': ['shopping', 'magazine', 'amazon', 'mercadolivre', 'vestuário', 'roupa'],
            'contas': ['cartão', 'boleto', 'fatura', 'seguro', 'imposto'],
            'outros': []
        }
    
    def detect_account_from_filename(self, filename):
        """Detecta o nome da conta baseado no nome do arquivo"""
        name_lower = filename.lower()
        if 'nubank' in name_lower or 'roxo' in name_lower:
            return 'Nubank'
        elif 'itau' in name_lower or 'itáu' in name_lower:
            return 'Itaú'
        elif 'bradesco' in name_lower:
            return 'Bradesco'
        elif 'santander' in name_lower:
            return 'Santander'
        elif 'caixa' in name_lower or 'caixa econômica' in name_lower:
            return 'Caixa'
        elif 'bb' in name_lower or 'brasil' in name_lower:
            return 'Banco do Brasil'
        elif 'inter' in name_lower:
            return 'Banco Inter'
        elif 'c6' in name_lower:
            return 'C6 Bank'
        else:
            return 'Outra Conta'
    
    def parse_date(self, date_str):
        """Tenta converter string para data em diferentes formatos"""
        if pd.isna(date_str):
            return None
        
        date_str = str(date_str).strip()
        formats = [
            '%d/%m/%Y', '%Y-%m-%d', '%d/%m/%y', '%m/%d/%Y',
            '%d-%m-%Y', '%Y%m%d', '%d.%m.%Y', '%d/%m/%Y %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return pd.to_datetime(date_str, format=fmt)
            except:
                continue
        
        try:
            return pd.to_datetime(date_str)
        except:
            return None
    
    def classify_transaction(self, description, value):
        """Classifica a transação baseado na descrição"""
        description_lower = str(description).lower()
        
        # Determina se é entrada ou saída
        transaction_type = 'entrada' if value > 0 else 'saida'
        
        # Busca categoria
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in description_lower:
                    return category, transaction_type
        
        return 'outros', transaction_type
    
    def process_uploaded_file(self, uploaded_file, account_name):
        """Processa um arquivo de extrato bancário"""
        try:
            # Tenta ler como CSV
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            # Tenta ler como Excel
            elif uploaded_file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(uploaded_file)
            else:
                st.error(f"Formato não suportado: {uploaded_file.name}")
                return None
            
            # Mapeia colunas comuns
            df = self._standardize_columns(df)
            
            if df is None or df.empty:
                st.warning(f"Arquivo {uploaded_file.name} não contém dados válidos")
                return None
            
            # Adiciona informações da conta
            df['conta'] = account_name
            df['arquivo_origem'] = uploaded_file.name
            
            # Processa datas
            if 'data' in df.columns:
                df['data'] = df['data'].apply(self.parse_date)
                df = df.dropna(subset=['data'])
                df['mes_ano'] = df['data'].dt.strftime('%Y-%m')
                df['mes'] = df['data'].dt.month
                df['ano'] = df['data'].dt.year
            
            # Classifica transações
            classification = df.apply(
                lambda row: self.classify_transaction(row.get('descricao', ''), row.get('valor', 0)),
                axis=1
            )
            df['categoria'] = [c[0] for c in classification]
            df['tipo'] = [c[1] for c in classification]
            
            return df
            
        except Exception as e:
            st.error(f"Erro ao processar {uploaded_file.name}: {str(e)}")
            return None
    
    def _standardize_columns(self, df):
        """Padroniza nomes de colunas comuns em extratos bancários"""
        column_mapping = {
            'data': ['data', 'date', 'data_lancamento', 'data da transação', 'dt', 'fecha'],
            'descricao': ['descricao', 'descrição', 'description', 'historico', 'histórico', 'nome', 'titulo', 'conceito', 'detalhes'],
            'valor': ['valor', 'value', 'amount', 'val', 'vlr', 'preco', 'preço']
        }
        
        # Renomeia colunas
        df_renamed = df.copy()
        for standard_name, possible_names in column_mapping.items():
            for col in df.columns:
                if col.lower() in possible_names:
                    df_renamed = df_renamed.rename(columns={col: standard_name})
                    break
        
        # Verifica se as colunas essenciais existem
        required_cols = ['data', 'descricao', 'valor']
        missing_cols = [col for col in required_cols if col not in df_renamed.columns]
        
        if missing_cols:
            st.warning(f"Colunas não encontradas: {missing_cols}")
            st.write("Colunas disponíveis:", list(df_renamed.columns))
            return None
        
        return df_renamed
    
    def consolidate_data(self, dataframes):
        """Consolida múltiplos dataframes em um único"""
        if not dataframes:
            return None
        
        consolidated = pd.concat(dataframes, ignore_index=True)
        consolidated = consolidated.sort_values('data')
        return consolidated
    
    def filter_data(self, df, accounts=None, months=None, transaction_type=None, start_date=None, end_date=None):
        """Aplica filtros aos dados"""
        filtered = df.copy()
        
        if accounts and len(accounts) > 0:
            filtered = filtered[filtered['conta'].isin(accounts)]
        
        if months and len(months) > 0:
            filtered = filtered[filtered['mes_ano'].isin(months)]
        
        if transaction_type and transaction_type != 'todos':
            filtered = filtered[filtered['tipo'] == transaction_type]
        
        if start_date:
            filtered = filtered[filtered['data'] >= start_date]
        
        if end_date:
            filtered = filtered[filtered['data'] <= end_date]
        
        return filtered

def main():
    """Função principal do aplicativo"""
    
    st.markdown('<h1 class="main-header">💰 Analisador Financeiro Inteligente</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Inicializa o analisador
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = FinancialAnalyzer()
        st.session_state.dataframes = []
        st.session_state.master_df = None
    
    analyzer = st.session_state.analyzer
    
    # Sidebar para upload
    with st.sidebar:
        st.header("📤 Upload de Extratos")
        st.markdown("**Formatos suportados:** CSV, Excel (.xlsx, .xls)")
        st.markdown("**Colunas necessárias:** Data, Descrição, Valor")
        
        uploaded_files = st.file_uploader(
            "Selecione os extratos bancários",
            type=['csv', 'xlsx', 'xls'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            if st.button("🔄 Processar Todos os Extratos"):
                st.session_state.dataframes = []
                progress_bar = st.progress(0)
                
                for i, file in enumerate(uploaded_files):
                    # Detecta conta automaticamente
                    account_name = analyzer.detect_account_from_filename(file.name)
                    
                    # Opção de alterar nome da conta
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        account_name = st.text_input(f"Conta para {file.name}", value=account_name, key=f"account_{i}")
                    
                    df = analyzer.process_uploaded_file(file, account_name)
                    if df is not None:
                        st.session_state.dataframes.append(df)
                        st.success(f"✅ {file.name} processado - {len(df)} transações")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                if st.session_state.dataframes:
                    st.session_state.master_df = analyzer.consolidate_data(st.session_state.dataframes)
                    st.success(f"🎉 Total consolidado: {len(st.session_state.master_df)} transações")
    
    # Área principal
    if st.session_state.master_df is not None:
        df = st.session_state.master_df
        
        # Métricas gerais
        st.header("📊 Resumo Financeiro Consolidado")
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_entradas = df[df['tipo'] == 'entrada']['valor'].sum()
        total_saidas = abs(df[df['tipo'] == 'saida']['valor'].sum())
        saldo_atual = total_entradas - total_saidas
        total_transacoes = len(df)
        
        with col1:
            st.metric("💰 Saldo Atual", f"R$ {saldo_atual:,.2f}", 
                     delta=f"R$ {saldo_atual:,.2f}" if saldo_atual >= 0 else None,
                     delta_color="normal")
        
        with col2:
            st.metric("📈 Total Entradas", f"R$ {total_entradas:,.2f}")
        
        with col3:
            st.metric("📉 Total Saídas", f"R$ {total_saidas:,.2f}")
        
        with col4:
            st.metric("🔄 Total Transações", f"{total_transacoes}")
        
        st.markdown("---")
        
        # Filtros
        st.header("🔍 Filtros Avançados")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            contas_disponiveis = sorted(df['conta'].unique())
            contas_selecionadas = st.multiselect("Contas", contas_disponiveis, default=contas_disponiveis)
        
        with col2:
            meses_disponiveis = sorted(df['mes_ano'].unique())
            meses_selecionados = st.multiselect("Meses", meses_disponiveis, default=meses_disponiveis)
        
        with col3:
            tipos = ['todos', 'entrada', 'saida']
            tipo_selecionado = st.selectbox("Tipo de Transação", tipos)
        
        with col4:
            data_min = df['data'].min()
            data_max = df['data'].max()
            periodo = st.date_input("Período Personalizado", value=[data_min, data_max])
        
        # Aplica filtros
        start_date = periodo[0] if len(periodo) > 0 else None
        end_date = periodo[1] if len(periodo) > 1 else None
        
        df_filtrado = analyzer.filter_data(
            df, contas_selecionadas, meses_selecionados, 
            tipo_selecionado, start_date, end_date
        )
        
        # Dashboard com dados filtrados
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Evolução Mensal")
            monthly_data = df_filtrado.groupby('mes_ano').agg({
                'valor': lambda x: x[x > 0].sum(),
                'tipo': lambda x: abs(x[x < 0].sum())
            }).reset_index()
            
            if not monthly_data.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(name='Entradas', x=monthly_data['mes_ano'], 
                                    y=monthly_data['valor'], marker_color='#00C853'))
                fig.add_trace(go.Bar(name='Saídas', x=monthly_data['mes_ano'], 
                                    y=monthly_data['tipo'], marker_color='#D50000'))
                fig.update_layout(barmode='group', title="Entradas vs Saídas por Mês")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🥧 Top Categorias de Gastos")
            gastos_categoria = df_filtrado[df_filtrado['tipo'] == 'saida'].groupby('categoria')['valor'].sum().abs()
            gastos_categoria = gastos_categoria.sort_values(ascending=False).head(10)
            
            if not gastos_categoria.empty:
                fig = px.pie(values=gastos_categoria.values, names=gastos_categoria.index, 
                            title="Distribuição de Gastos por Categoria")
                st.plotly_chart(fig, use_container_width=True)
        
        # Tabela de transações
        st.subheader("📋 Transações Detalhadas")
        
        # Botão para exportar
        if st.button("📥 Exportar dados filtrados (Excel)"):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_filtrado.to_excel(writer, sheet_name='Transacoes', index=False)
            st.download_button(
                label="Baixar Excel",
                data=output.getvalue(),
                file_name=f"analise_financeira_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # Exibe tabela
        st.dataframe(
            df_filtrado[['data', 'descricao', 'conta', 'categoria', 'tipo', 'valor']].head(100),
            use_container_width=True,
            height=400
        )
        
        # Resumo por conta
        with st.expander("📊 Resumo por Conta Bancária"):
            resumo_contas = df_filtrado.groupby('conta').agg({
                'valor': lambda x: x[x > 0].sum(),
                'tipo': lambda x: abs(x[x < 0].sum()),
                'descricao': 'count'
            }).reset_index()
            resumo_contas.columns = ['Conta', 'Total Entradas', 'Total Saídas', 'Número Transações']
            resumo_contas['Saldo'] = resumo_contas['Total Entradas'] - resumo_contas['Total Saídas']
            st.dataframe(resumo_contas, use_container_width=True)
        
    else:
        # Tela inicial
        st.info("👋 **Bem-vindo ao Analisador Financeiro!**")
        st.markdown("""
        ### Como usar:
        1. No menu lateral, faça upload dos seus extratos bancários
        2. O sistema detectará automaticamente as colunas de Data, Descrição e Valor
        3. As transações serão classificadas como entrada ou saída
        4. Filtre por conta, mês, tipo ou período personalizado
        5. Visualize gráficos e métricas do seu fluxo financeiro
        
        ### Formatos aceitos:
        - Arquivos CSV
        - Planilhas Excel (.xlsx, .xls)
        
        ### Dicas:
        - Você pode fazer upload de múltiplos extratos de diferentes bancos
        - O sistema detecta automaticamente o nome do banco pelo nome do arquivo
        - Classificação inteligente baseada em palavras-chave nas descrições
        """)
        
        # Exemplo de extrato mockado
        if st.button("📝 Carregar Exemplo de Dados"):
            example_df = pd.DataFrame({
                'data': ['01/12/2024', '05/12/2024', '10/12/2024', '15/12/2024', '20/12/2024'],
                'descricao': ['Salário - Empresa ABC', 'Supermercado Extra', 'Uber Viagem', 'Netflix Assinatura', 'Transferência Pix Recebida'],
                'valor': [5000.00, -350.50, -45.90, -39.90, 200.00]
            })
            
            # Salva como CSV temporário
            example_csv = example_df.to_csv(index=False).encode('utf-8')
            example_file = io.BytesIO(example_csv)
            example_file.name = 'exemplo_extrato.csv'
            
            df_processed = analyzer.process_uploaded_file(example_file, 'Conta Exemplo')
            if df_processed is not None:
                st.session_state.dataframes = [df_processed]
                st.session_state.master_df = df_processed
                st.rerun()

if __name__ == "__main__":
    main()