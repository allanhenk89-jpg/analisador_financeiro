"""
Sistema de Análise Financeira - Versão SEM PANDAS (100% puro Python)
"""

import streamlit as st
import csv
import io
from datetime import datetime
import re

# Configuração da página
st.set_page_config(page_title="Analisador Financeiro", page_icon="💰", layout="wide")

def parse_csv_content(uploaded_file):
    """Le CSV manualmente sem usar pandas"""
    content = uploaded_file.read().decode('utf-8')
    lines = content.split('\n')
    
    if not lines:
        return None
    
    # Detecta cabecalho
    header = lines[0].split(',')
    header = [h.strip().lower().replace('"', '') for h in header]
    
    # Identifica colunas
    data_col = None
    desc_col = None
    valor_col = None
    
    for i, col in enumerate(header):
        if 'data' in col or 'date' in col:
            data_col = i
        if 'desc' in col or 'historico' in col or 'nome' in col or 'descricao' in col:
            desc_col = i
        if 'valor' in col or 'value' in col or 'amount' in col:
            valor_col = i
    
    if data_col is None or desc_col is None or valor_col is None:
        return None
    
    # Processa linhas
    transactions = []
    for line in lines[1:]:
        if not line.strip():
            continue
        
        # Divide CSV (simples, sem suporte a virgulas dentro de aspas)
        parts = line.split(',')
        if len(parts) <= max(data_col, desc_col, valor_col):
            continue
        
        # Extrai dados
        data_str = parts[data_col].strip().replace('"', '')
        desc = parts[desc_col].strip().replace('"', '')
        valor_str = parts[valor_col].strip().replace('"', '')
        
        # Converte data
        try:
            data = None
            for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d/%m/%y', '%m/%d/%Y', '%d-%m-%Y']:
                try:
                    data = datetime.strptime(data_str, fmt)
                    break
                except:
                    continue
            if data is None:
                continue
        except:
            continue
        
        # Converte valor
        try:
            valor = float(valor_str.replace(',', '.'))
        except:
            try:
                # Tenta com formato brasileiro (1.000,50)
                valor = float(valor_str.replace('.', '').replace(',', '.'))
            except:
                continue
        
        # Classifica tipo
        tipo = 'entrada' if valor > 0 else 'saida'
        
        # Classifica categoria
        categoria = classificar_categoria(desc, valor)
        
        transactions.append({
            'data': data,
            'descricao': desc,
            'valor': valor,
            'tipo': tipo,
            'categoria': categoria,
            'mes_ano': data.strftime('%Y-%m'),
            'mes_nome': data.strftime('%B/%Y')
        })
    
    return transactions

def classificar_categoria(desc, valor):
    """Classifica a transacao baseado na descricao"""
    desc_lower = desc.lower()
    
    categorias = {
        '🍔 Alimentacao': ['mercado', 'supermercado', 'restaurante', 'ifood', 'comida', 'padaria', 'feira', 'mcdonalds', 'burger'],
        '🚗 Transporte': ['uber', 'taxi', 'combustivel', 'gasolina', 'estacionamento', 'pedagio', '99pop'],
        '🏠 Moradia': ['aluguel', 'condominio', 'luz', 'energia', 'agua', 'gas', 'internet', 'telefone'],
        '⚕️ Saude': ['farmacia', 'medico', 'consulta', 'plano', 'hospital', 'dental'],
        '🎬 Lazer': ['cinema', 'netflix', 'streaming', 'show', 'viagem', 'hotel', 'hobby'],
        '🛍️ Compras': ['shopping', 'amazon', 'mercado livre', 'roupa', 'vestuario', 'magazine'],
        '📚 Educacao': ['faculdade', 'curso', 'escola', 'livro', 'material'],
        '💳 Contas': ['cartao', 'boleto', 'fatura', 'seguro', 'imposto']
    }
    
    if valor > 0:
        return '💰 Entrada'
    
    for cat, palavras in categorias.items():
        for palavra in palavras:
            if palavra in desc_lower:
                return cat
    
    return '📌 Outros'

def detectar_conta(filename):
    """Detecta o nome da conta pelo nome do arquivo"""
    filename_lower = filename.lower()
    bancos = {
        'nubank': 'Nubank', 'itau': 'Itau', 'bradesco': 'Bradesco',
        'santander': 'Santander', 'caixa': 'Caixa', 'bb': 'Banco do Brasil',
        'inter': 'Banco Inter', 'c6': 'C6 Bank', 'next': 'Next'
    }
    for key, value in bancos.items():
        if key in filename_lower:
            return value
    return 'Outra Conta'

# ========== FUNCOES DE ANALISE ==========

def calcular_metricas(transacoes):
    """Calcula metricas financeiras"""
    entradas = sum(t['valor'] for t in transacoes if t['valor'] > 0)
    saidas = sum(t['valor'] for t in transacoes if t['valor'] < 0)
    return {
        'entradas': entradas,
        'saidas': abs(saidas),
        'saldo': entradas + saidas,
        'total_transacoes': len(transacoes)
    }

def agrupar_por_categoria(transacoes):
    """Agrupa gastos por categoria"""
    gastos = {}
    for t in transacoes:
        if t['valor'] < 0:
            cat = t['categoria']
            gastos[cat] = gastos.get(cat, 0) + abs(t['valor'])
    return gastos

def agrupar_por_mes(transacoes):
    """Agrupa entradas e saidas por mes"""
    meses = {}
    for t in transacoes:
        mes = t['mes_ano']
        if mes not in meses:
            meses[mes] = {'entradas': 0, 'saidas': 0, 'nome': t['mes_nome']}
        
        if t['valor'] > 0:
            meses[mes]['entradas'] += t['valor']
        else:
            meses[mes]['saidas'] += abs(t['valor'])
    
    return dict(sorted(meses.items()))

# ========== INTERFACE PRINCIPAL ==========

st.title("💰 Analisador Financeiro")
st.markdown("---")

# Inicializa session state
if 'transacoes' not in st.session_state:
    st.session_state.transacoes = []

# Sidebar
with st.sidebar:
    st.header("📤 Upload de Extratos")
    st.info("Formato aceito: CSV. Colunas necessarias: data, descricao, valor")
    
    uploaded_files = st.file_uploader(
        "Selecione os arquivos CSV",
        type=['csv'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for file in uploaded_files:
            conta = detectar_conta(file.name)
            nova_conta = st.text_input(f"Conta: {file.name}", value=conta, key=f"nome_{file.name}")
            
            if st.button(f"📂 Importar {file.name}", key=f"btn_{file.name}"):
                with st.spinner(f"Processando {file.name}..."):
                    transacoes = parse_csv_content(file)
                    if transacoes and len(transacoes) > 0:
                        for t in transacoes:
                            t['conta'] = nova_conta
                        st.session_state.transacoes.extend(transacoes)
                        st.success(f"✅ {len(transacoes)} transacoes importadas de {nova_conta}")
                    else:
                        st.error(f"❌ Erro ao processar {file.name}. Verifique o formato do CSV.")
        
        if st.session_state.transacoes:
            st.success(f"📊 Total: {len(st.session_state.transacoes)} transacoes")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Limpar todos os dados", use_container_width=True):
                    st.session_state.transacoes = []
                    st.rerun()
            with col2:
                if st.button("📥 Exportar dados", use_container_width=True):
                    output = io.StringIO()
                    writer = csv.writer(output)
                    writer.writerow(['data', 'descricao', 'conta', 'categoria', 'valor'])
                    for t in st.session_state.transacoes:
                        writer.writerow([
                            t['data'].strftime('%d/%m/%Y'),
                            t['descricao'],
                            t['conta'],
                            t['categoria'],
                            t['valor']
                        ])
                    st.download_button(
                        label="Baixar CSV",
                        data=output.getvalue(),
                        file_name=f"dados_financeiros_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )

# Area principal
if st.session_state.transacoes:
    transacoes = st.session_state.transacoes
    
    # Filtros
    st.header("🔍 Filtros")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        contas = sorted(list(set(t['conta'] for t in transacoes)))
        contas_sel = st.multiselect("🏦 Contas", contas, default=contas)
    
    with col2:
        meses = sorted(list(set(t['mes_ano'] for t in transacoes)))
        meses_nomes = {t['mes_ano']: t['mes_nome'] for t in transacoes}
        meses_sel = st.multiselect("📅 Meses", meses, format_func=lambda x: meses_nomes.get(x, x), default=meses)
    
    with col3:
        tipos_sel = st.multiselect("🔄 Tipo", ['entrada', 'saida'], default=['entrada', 'saida'])
    
    # Aplica filtros
    filtradas = [t for t in transacoes 
                 if t['conta'] in contas_sel 
                 and t['mes_ano'] in meses_sel
                 and t['tipo'] in tipos_sel]
    
    if filtradas:
        # Metricas
        metricas = calcular_metricas(filtradas)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Saldo", f"R$ {metricas['saldo']:,.2f}")
        with col2:
            st.metric("📈 Entradas", f"R$ {metricas['entradas']:,.2f}")
        with col3:
            st.metric("📉 Saidas", f"R$ {metricas['saidas']:,.2f}")
        with col4:
            st.metric("📊 Transacoes", metricas['total_transacoes'])
        
        st.markdown("---")
        
        # Grafico de evolucao mensal
        st.subheader("📈 Evolucao Mensal")
        
        meses_agrupados = agrupar_por_mes(filtradas)
        if meses_agrupados:
            meses_lista = list(meses_agrupados.keys())
            entradas_lista = [meses_agrupados[m]['entradas'] for m in meses_lista]
            saidas_lista = [meses_agrupados[m]['saidas'] for m in meses_lista]
            
            max_valor = max(max(entradas_lista) if entradas_lista else 0, 
                           max(saidas_lista) if saidas_lista else 0)
            
            for i, mes in enumerate(meses_lista):
                st.write(f"**{meses_agrupados[mes]['nome']}**")
                col1, col2 = st.columns(2)
                with col1:
                    perc_ent = (entradas_lista[i] / max_valor * 100) if max_valor > 0 else 0
                    st.write(f"📈 Entradas: R$ {entradas_lista[i]:,.2f}")
                    st.progress(min(perc_ent/100, 1.0), text=f"{perc_ent:.0f}%")
                with col2:
                    perc_sai = (saidas_lista[i] / max_valor * 100) if max_valor > 0 else 0
                    st.write(f"📉 Saidas: R$ {saidas_lista[i]:,.2f}")
                    st.progress(min(perc_sai/100, 1.0), text=f"{perc_sai:.0f}%")
                st.write("")
        
        st.markdown("---")
        
        # Resumo por categoria
        st.subheader("📊 Resumo por Categoria")
        
        gastos_por_cat = agrupar_por_categoria(filtradas)
        if gastos_por_cat:
            total_gastos = sum(gastos_por_cat.values())
            
            for cat, valor in sorted(gastos_por_cat.items(), key=lambda x: x[1], reverse=True):
                perc = (valor / total_gastos) * 100 if total_gastos > 0 else 0
                col1, col2, col3 = st.columns([2, 3, 1])
                with col1:
                    st.write(f"**{cat}**")
                with col2:
                    st.progress(min(perc/100, 1.0))
                with col3:
                    st.write(f"R$ {valor:,.2f} ({perc:.1f}%)")
        else:
            st.info("Nenhum gasto registrado no periodo.")
        
        st.markdown("---")
        
        # Tabela de transacoes
        st.subheader("📋 Transacoes Recentes")
        
        tabela = []
        for t in sorted(filtradas, key=lambda x: x['data'], reverse=True)[:100]:
            tabela.append({
                'Data': t['data'].strftime('%d/%m/%Y'),
                'Descricao': t['descricao'][:50],
                'Conta': t['conta'],
                'Categoria': t['categoria'],
                'Valor': f"R$ {t['valor']:,.2f}"
            })
        
        st.dataframe(tabela, use_container_width=True, height=400)
        
        # Resumo por conta
        with st.expander("📊 Detalhamento por Conta"):
            contas_resumo = {}
            for t in filtradas:
                conta = t['conta']
                if conta not in contas_resumo:
                    contas_resumo[conta] = {'entradas': 0, 'saidas': 0, 'transacoes': 0}
                contas_resumo[conta]['transacoes'] += 1
                if t['valor'] > 0:
                    contas_resumo[conta]['entradas'] += t['valor']
                else:
                    contas_resumo[conta]['saidas'] += abs(t['valor'])
            
            for conta, dados in contas_resumo.items():
                saldo = dados['entradas'] - dados['saidas']
                st.write(f"**{conta}**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"💰 Saldo: R$ {saldo:,.2f}")
                with col2:
                    st.write(f"📈 Entradas: R$ {dados['entradas']:,.2f}")
                with col3:
                    st.write(f"📉 Saidas: R$ {dados['saidas']:,.2f}")
                with col4:
                    st.write(f"🔄 {dados['transacoes']} transacoes")
                st.write("")
    
    else:
        st.info("Nenhuma transacao encontrada com os filtros selecionados.")

else:
    st.info("👈 Faca upload de arquivos CSV na barra lateral para comecar!")
    
    st.markdown("**Instrucoes:**")
    st.markdown("1. Prepare seu extrato bancario em formato CSV")
    st.markdown("2. O arquivo deve ter as colunas: data, descricao, valor")
    st.markdown("3. Faca upload na barra lateral")
    
    st.markdown("**Exemplo de arquivo CSV valido:**")
    st.code("""
data,descricao,valor
01/12/2024,Salario,5000
05/12/2024,Supermercado,-350
10/12/2024,Uber,-45
    """, language="csv")
    
    # Botao exemplo
    if st.button("📝 Carregar dados de exemplo", type="primary"):
        exemplo = []
        dados_exemplo = [
            ('01/12/2024', 'Salario - Empresa XYZ', 5000.00),
            ('05/12/2024', 'Supermercado Extra', -350.50),
            ('10/12/2024', 'Uber - Viagem trabalho', -45.90),
            ('15/12/2024', 'Netflix Assinatura', -39.90),
            ('18/12/2024', 'Farmacia Droga Raia', -78.30),
            ('20/12/2024', 'Aluguel', -1200.00),
            ('25/12/2024', 'Cinema com amigos', -60.00),
            ('28/12/2024', 'Transferencia Pix Recebida', 200.00),
        ]
        
        for data_str, desc, valor in dados_exemplo:
            data = datetime.strptime(data_str, '%d/%m/%Y')
            tipo = 'entrada' if valor > 0 else 'saida'
            categoria = classificar_categoria(desc, valor)
            exemplo.append({
                'data': data,
                'descricao': desc,
                'valor': valor,
                'tipo': tipo,
                'categoria': categoria,
                'conta': 'Conta Exemplo',
                'mes_ano': data.strftime('%Y-%m'),
                'mes_nome': data.strftime('%B/%Y')
            })
        
        st.session_state.transacoes = exemplo
        st.success("✅ Dados de exemplo carregados!")
        st.rerun()

st.markdown("---")
st.caption("Dica: Para exportar do seu banco, procure pela opcao 'Exportar como CSV' no extrato.")
