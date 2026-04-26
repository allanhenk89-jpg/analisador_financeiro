"""
Sistema de Análise Financeira - Versão Estável
Corrigido para funcionar no Streamlit Cloud
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import re

# Configuração da página - deve ser o PRIMEIRO comando Streamlit
st.set_page_config(
    page_title="Analisador Financeiro",
    page_icon="💰",
    layout="wide"
)

# ========== CLASSES E FUNÇÕES ==========

class FinancialAnalyzer:
    def __init__(self):
        self.categories = {
            'entradas': ['salário', 'salario', 'depósito', 'deposito', 'transferência', 'transferencia', 'pix recebido', 'rendimento', 'dividendo'],
            'alimentacao': ['mercado', 'supermercado', 'restaurante', 'ifood', 'rappi', 'comida', 'padaria', 'feira'],
            'transporte': ['uber', 'taxi', 'combustível', 'gasolina', 'estacionamento', 'pedágio'],
            'moradia': ['aluguel', 'condomínio', 'luz', 'energia', 'água', 'gás', 'internet'],
            'saude': ['farmácia', 'farmacia', 'médico', 'medico', 'consulta', 'plano de saúde'],
            'lazer': ['cinema', 'netflix', 'streaming', 'show', 'viagem', 'hobby'],
            'compras': ['shopping', 'amazon', 'mercadolivre', 'roupa', 'vestuário'],
            'contas': ['cartão', 'cartao', 'boleto', 'fatura', 'seguro']
        }
    
    def detect_account(self, filename):
        filename = filename.lower()
        bancos = {
            'nubank': 'Nubank', 'itau': 'Itaú', 'bradesco': 'Bradesco',
            'santander': 'Santander', 'caixa': 'Caixa', 'bb': 'Banco do Brasil',
            'inter': 'Banco Inter', 'c6': 'C6 Bank'
        }
        for key, value in bancos.items():
            if key in filename:
                return value
        return 'Outra Conta'
    
    def process_file(self, uploaded_file, account_name):
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Padroniza colunas
            col_map = {
                'data': ['data', 'date', 'Data', 'Date'],
                'descricao': ['descricao', 'descrição', 'description', 'historico'],
                'valor': ['valor', 'value', 'amount', 'Valor']
            }
            
            for std_name, variations in col_map.items():
                for var in variations:
                    if var in df.columns:
                        df = df.rename(columns={var: std_name})
                        break
            
            # Verifica colunas essenciais
            if not all(col in df.columns for col in ['data', 'descricao', 'valor']):
                return None
            
            # Processa datas
            df['data'] = pd.to_datetime(df['data'], errors='coerce')
            df = df.dropna(subset=['data'])
            df['mes_ano'] = df['data'].dt.strftime('%Y-%m')
            df['ano'] = df['data'].dt.year
            df['mes'] = df['data'].dt.month
            
            # Classifica transações
            df['conta'] = account_name
            
            def classify(row):
                valor = row['valor']
                desc = str(row['descricao']).lower()
                
                if valor > 0:
                    return 'entrada', '📈 Entrada'
                else:
                    for category, keywords in self.categories.items():
                        if category == 'entradas':
                            continue
                        for keyword in keywords:
                            if keyword in desc:
                                return 'saida', f'💳 {category.capitalize()}'
                    return 'saida', '💳 Outros'
            
            df[['tipo', 'categoria']] = df.apply(lambda row: pd.Series(classify(row)), axis=1)
            df['valor_abs'] = df['valor'].abs()
            
            return df
            
        except Exception as e:
            st.error(f"Erro: {str(e)}")
            return None

# ========== FUNÇÃO PRINCIPAL ==========

def main():
    # Inicializa session state
    if 'dataframes' not in st.session_state:
        st.session_state.dataframes = []
    if 'master_df' not in st.session_state:
        st.session_state.master_df = None
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = FinancialAnalyzer()
    
    analyzer = st.session_state.analyzer
    
    # Header
    st.title("💰 Analisador Financeiro")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("📤 Upload de Extratos")
        st.info("Formatos: CSV ou Excel\nColunas: data, descricao, valor")
        
        files = st.file_uploader(
            "Selecione os arquivos",
            type=['csv', 'xlsx', 'xls'],
            accept_multiple_files=True
        )
        
        if files and st.button("🔄 Processar"):
            st.session_state.dataframes = []
            progress = st.progress(0)
            
            for i, file in enumerate(files):
                account = analyzer.detect_account(file.name)
                account = st.text_input(f"Conta: {file.name}", value=account, key=f"acc_{i}")
                
                df = analyzer.process_file(file, account)
                if df is not None:
                    st.session_state.dataframes.append(df)
                    st.success(f"✅ {file.name}: {len(df)} transações")
                progress.progress((i+1)/len(files))
            
            if st.session_state.dataframes:
                st.session_state.master_df = pd.concat(st.session_state.dataframes, ignore_index=True)
                st.success(f"🎉 Total: {len(st.session_state.master_df)} transações")
    
    # Main content
    if st.session_state.master_df is not None and not st.session_state.master_df.empty:
        df = st.session_state.master_df
        
        # Filtros
        st.header("🔍 Filtros")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            contas = st.multiselect("Contas", options=sorted(df['conta'].unique()), default=sorted(df['conta'].unique()))
        with col2:
            meses = st.multiselect("Meses", options=sorted(df['mes_ano'].unique()), default=sorted(df['mes_ano'].unique()))
        with col3:
            tipo = st.selectbox("Tipo", options=['todos', 'entrada', 'saida'])
        
        # Aplica filtros
        filtered = df.copy()
        if contas:
            filtered = filtered[filtered['conta'].isin(contas)]
        if meses:
            filtered = filtered[filtered['mes_ano'].isin(meses)]
        if tipo != 'todos':
            filtered = filtered[filtered['tipo'] == tipo]
        
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        entradas = filtered[filtered['valor'] > 0]['valor'].sum()
        saidas = filtered[filtered['valor'] < 0]['valor'].sum()
        
        with col1:
            st.metric("💰 Saldo", f"R$ {entradas + saidas:,.2f}")
        with col2:
            st.metric("📈 Entradas", f"R$ {entradas:,.2f}")
        with col3:
            st.metric("📉 Saídas", f"R$ {abs(saidas):,.2f}")
        with col4:
            st.metric("📊 Transações", len(filtered))
        
        st.markdown("---")
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Evolução Mensal")
            monthly = filtered.groupby('mes_ano').agg({
                'valor': lambda x: x[x > 0].sum(),
                'tipo': lambda x: abs(x[x < 0].sum())
            }).reset_index()
            monthly.columns = ['mes', 'entradas', 'saidas']
            
            if not monthly.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(name='Entradas', x=monthly['mes'], y=monthly['entradas'], marker_color='green'))
                fig.add_trace(go.Bar(name='Saídas', x=monthly['mes'], y=monthly['saidas'], marker_color='red'))
                fig.update_layout(barmode='group', height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Categorias de Gastos")
            gastos = filtered[filtered['tipo'] == 'saida'].groupby('categoria')['valor_abs'].sum()
            if not gastos.empty:
                fig = px.pie(values=gastos.values, names=gastos.index, height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # Tabela
        st.subheader("📋 Transações")
        st.dataframe(
            filtered[['data', 'descricao', 'conta', 'categoria', 'valor']].head(100),
            use_container_width=True
        )
        
        # Exportar
        if st.button("📥 Exportar para Excel"):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                filtered.to_excel(writer, index=False)
            st.download_button(
                label="Baixar arquivo",
                data=output.getvalue(),
                file_name=f"analise_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    else:
        st.info("👈 Faça upload dos seus extratos bancários na barra lateral para começar!")
        
        # Exemplo
        if st.button("📝 Carregar exemplo"):
            exemplo = pd.DataFrame({
                'data': ['01/12/2024', '05/12/2024', '10/12/2024', '15/12/2024'],
                'descricao': ['Salário', 'Supermercado', 'Uber', 'Netflix'],
                'valor': [5000, -350, -45, -40]
            })
            exemplo['data'] = pd.to_datetime(exemplo['data'])
            st.session_state.master_df = exemplo
            st.rerun()

# ========== EXECUÇÃO ==========
if __name__ == "__main__":
    main()
