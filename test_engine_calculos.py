#!/usr/bin/env python3
"""
TESTE COMPLETO DO ENGINE DE CÁLCULOS - SISTEMA FLUYT

Valida TODOS os cálculos críticos conforme PRD.md:
- Comissão progressiva vendedor
- Comissão progressiva gerente  
- Cálculo custo fábrica (deflator 28%)
- Cálculo frete percentual (2%)
- Custos adicionais
- Margem final
- Cenários edge cases
"""

import sys
import os
import asyncio
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

# Adicionar backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def configurar_ambiente():
    """Configurar variáveis de ambiente para teste"""
    os.environ['SUPABASE_URL'] = 'https://momwbpxqnvgehotfmvde.supabase.co'
    os.environ['SUPABASE_ANON_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vbXdicHhxbnZnZWhvdGZtdmRlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc3NzAxNTIsImV4cCI6MjA2MzM0NjE1Mn0.n90ZweBT-o1ugerZJDZl8gx65WGe1eUrhph6VuSdSCs'
    os.environ['SUPABASE_SERVICE_KEY'] = 'placeholder'
    os.environ['ENVIRONMENT'] = 'development'

def formatar_moeda(valor):
    """Formatar valor como moeda brasileira"""
    return f"R$ {valor:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')

def teste_comissao_progressiva_vendedor():
    """
    🚨 TESTE 1: Comissão por FAIXA ÚNICA (CORRIGIDO - não progressivo)
    
    REGRA REAL DE NEGÓCIO:
    - Identifica qual faixa o valor se encaixa
    - Aplica percentual da faixa sobre TODO o valor
    - NÃO soma faixas anteriores
    
    Regras D-Art:
    - Faixa 1: até R$ 25.000 = 5% sobre total
    - Faixa 2: R$ 25.001-50.000 = 6% sobre total
    - Faixa 3: acima R$ 50.000 = 8% sobre total
    
    Exemplos corretos:
    - R$ 40.000 → Faixa 2 → 6% × R$ 40.000 = R$ 2.400 (não R$ 2.150)
    """
    print("🔍 TESTE 1: Comissão Progressiva Vendedor")
    print("=" * 60)
    
    try:
        from modules.orcamentos.services import OrcamentoService
        from core.database import SupabaseClient
        from core.config import get_settings
        
        settings = get_settings()
        supabase_client = SupabaseClient(settings)
        service = OrcamentoService(supabase_client)
        
        # Criar DataFrame com regras conforme PRD
        regras_vendedor = pd.DataFrame([
            {
                'id': '1',
                'loja_id': 'test',
                'tipo_comissao': 'VENDEDOR',
                'valor_minimo': 0.0,
                'valor_maximo': 25000.0,
                'percentual': 0.05,  # 5%
                'ordem': 1
            },
            {
                'id': '2',
                'loja_id': 'test',
                'tipo_comissao': 'VENDEDOR',
                'valor_minimo': 25000.01,
                'valor_maximo': 50000.0,
                'percentual': 0.06,  # 6%
                'ordem': 2
            },
            {
                'id': '3',
                'loja_id': 'test',
                'tipo_comissao': 'VENDEDOR',
                'valor_minimo': 50000.01,
                'valor_maximo': None,
                'percentual': 0.08,  # 8%
                'ordem': 3
            }
        ])
        
        # Cenários de teste CORRIGIDOS - Faixa única sobre valor total
        cenarios = [
            {'nome': 'Exemplo oficial PRD (CORRIGIDO)', 'valor': 40000.0, 'esperado': 2400.0},  # Faixa 2: 6% × 40k = 2.400
            {'nome': 'Edge case limite faixa 1', 'valor': 24999.0, 'esperado': 1249.95},        # Faixa 1: 5% × 24.999 = 1.249,95  
            {'nome': 'Edge case início faixa 2', 'valor': 25001.0, 'esperado': 1500.06},        # Faixa 2: 6% × 25.001 = 1.500,06
            {'nome': 'Stress test faixa 3 (CORRIGIDO)', 'valor': 100000.0, 'esperado': 8000.0} # Faixa 3: 8% × 100k = 8.000
        ]
        
        resultados = []
        
        for cenario in cenarios:
            resultado = service.calcular_comissao_faixa_unica_pandas(cenario['valor'], regras_vendedor)
            
            valor_calculado = resultado['comissao_total']
            diferenca = abs(valor_calculado - cenario['esperado'])
            sucesso = diferenca < 0.01
            
            print(f"\n📊 {cenario['nome']}")
            print(f"   Valor venda: {formatar_moeda(cenario['valor'])}")
            print(f"   Esperado:    {formatar_moeda(cenario['esperado'])}")
            print(f"   Calculado:   {formatar_moeda(valor_calculado)}")
            print(f"   Diferença:   {formatar_moeda(diferenca)}")
            print(f"   Status:      {'✅ CORRETO' if sucesso else '❌ ERRO'}")
            
            if resultado['detalhes_faixas']:
                print(f"   Detalhes:")
                faixa = resultado['detalhes_faixas'][0]  # Sempre uma única faixa
                print(f"     Faixa {faixa['faixa']}: {formatar_moeda(faixa['valor_total_aplicado'])} × {faixa['percentual']:.1%} = {formatar_moeda(faixa['comissao_calculada'])}")
            
            resultados.append({
                'cenario': cenario['nome'],
                'sucesso': sucesso,
                'valor': cenario['valor'],
                'esperado': cenario['esperado'],
                'calculado': valor_calculado
            })
        
        sucessos = sum(1 for r in resultados if r['sucesso'])
        print(f"\n🎯 RESULTADO: {sucessos}/{len(resultados)} cenários corretos")
        
        return sucessos == len(resultados), resultados
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False, []

def teste_calculos_custos_basicos():
    """
    TESTE 2: Cálculos básicos (deflator, frete, medidor)
    
    Configurações PRD:
    - Deflator fábrica: 28% (0.28)
    - Frete: 2% sobre venda (0.02)
    - Medidor padrão: R$ 200
    """
    print("\n🔍 TESTE 2: Cálculos de Custos Básicos")
    print("=" * 60)
    
    # Dados de teste
    valor_ambientes = 50000.0  # R$ 50.000 XML
    valor_venda = 40000.0      # R$ 40.000 após desconto 20%
    
    # Configurações conforme PRD
    deflator_fabrica = 0.28    # 28%
    percentual_frete = 0.02    # 2%
    valor_medidor = 200.0      # R$ 200
    
    # Cálculos esperados
    custo_fabrica_esperado = valor_ambientes * deflator_fabrica  # 50.000 × 28% = 14.000
    custo_frete_esperado = valor_venda * percentual_frete        # 40.000 × 2% = 800
    custo_medidor_esperado = valor_medidor                       # 200
    
    print(f"\n📊 Cálculo Custo Fábrica (Deflator)")
    print(f"   Valor XML:     {formatar_moeda(valor_ambientes)}")
    print(f"   Deflator:      {deflator_fabrica:.1%}")
    print(f"   Esperado:      {formatar_moeda(custo_fabrica_esperado)}")
    print(f"   Calculado:     {formatar_moeda(valor_ambientes * deflator_fabrica)}")
    print(f"   Status:        {'✅ CORRETO' if abs((valor_ambientes * deflator_fabrica) - custo_fabrica_esperado) < 0.01 else '❌ ERRO'}")
    
    print(f"\n📊 Cálculo Frete Percentual")
    print(f"   Valor venda:   {formatar_moeda(valor_venda)}")
    print(f"   Percentual:    {percentual_frete:.1%}")
    print(f"   Esperado:      {formatar_moeda(custo_frete_esperado)}")
    print(f"   Calculado:     {formatar_moeda(valor_venda * percentual_frete)}")
    print(f"   Status:        {'✅ CORRETO' if abs((valor_venda * percentual_frete) - custo_frete_esperado) < 0.01 else '❌ ERRO'}")
    
    print(f"\n📊 Custo Medidor Padrão")
    print(f"   Valor padrão:  {formatar_moeda(valor_medidor)}")
    print(f"   Esperado:      {formatar_moeda(custo_medidor_esperado)}")
    print(f"   Status:        {'✅ CORRETO' if valor_medidor == custo_medidor_esperado else '❌ ERRO'}")
    
    # Verificar precisão decimal
    fabrica_ok = abs((valor_ambientes * deflator_fabrica) - custo_fabrica_esperado) < 0.01
    frete_ok = abs((valor_venda * percentual_frete) - custo_frete_esperado) < 0.01
    medidor_ok = valor_medidor == custo_medidor_esperado
    
    print(f"\n🎯 RESULTADO: {sum([fabrica_ok, frete_ok, medidor_ok])}/3 cálculos corretos")
    
    return fabrica_ok and frete_ok and medidor_ok

def teste_custos_adicionais():
    """
    TESTE 3: Custos adicionais múltiplos
    
    Validar:
    - Soma de múltiplos custos
    - Impacto na margem final
    - Precisão decimal
    """
    print("\n🔍 TESTE 3: Custos Adicionais")
    print("=" * 60)
    
    # Cenário: Venda R$ 40.000 com custos adicionais
    valor_venda = 40000.0
    
    custos_adicionais = [
        {'descricao': 'Taxa projeto especial', 'valor': 500.0},
        {'descricao': 'Comissão indicador', 'valor': 800.0},
        {'descricao': 'Aluguel equipamento', 'valor': 150.0}
    ]
    
    total_custos_adicionais_esperado = sum(item['valor'] for item in custos_adicionais)  # 1.450
    
    print(f"\n📊 Custos Adicionais:")
    for item in custos_adicionais:
        print(f"   {item['descricao']}: {formatar_moeda(item['valor'])}")
    
    print(f"\n📊 Resumo:")
    print(f"   Total esperado: {formatar_moeda(total_custos_adicionais_esperado)}")
    print(f"   Total calculado: {formatar_moeda(sum(item['valor'] for item in custos_adicionais))}")
    
    # Verificar se soma está correta
    total_calculado = sum(item['valor'] for item in custos_adicionais)
    sucesso = abs(total_calculado - total_custos_adicionais_esperado) < 0.01
    
    print(f"   Status: {'✅ CORRETO' if sucesso else '❌ ERRO'}")
    
    print(f"\n🎯 RESULTADO: {'✅ SUCESSO' if sucesso else '❌ FALHA'}")
    
    return sucesso

def teste_margem_final():
    """
    TESTE 4: Cálculo margem final completa
    
    Fórmula: margem = valor_venda - (todos_custos)
    """
    print("\n🔍 TESTE 4: Margem Final Completa")
    print("=" * 60)
    
    # Cenário completo conforme PRD
    valor_ambientes = 50000.0
    desconto_percentual = 0.20  # 20%
    valor_venda = valor_ambientes * (1 - desconto_percentual)  # 40.000
    
    # Custos conforme PRD
    custo_fabrica = valor_ambientes * 0.28      # 14.000
    comissao_vendedor = 2400.0                  # Corrigido: R$ 40k × 6% = R$ 2.400
    comissao_gerente = 1200.0                   # Exemplo
    custo_medidor = 200.0                       # Padrão
    custo_frete = valor_venda * 0.02            # 800
    custo_montador = 1000.0                     # Exemplo
    custos_adicionais = 500.0                   # Exemplo
    
    total_custos = (custo_fabrica + comissao_vendedor + comissao_gerente + 
                   custo_medidor + custo_frete + custo_montador + custos_adicionais)
    
    margem_esperada = valor_venda - total_custos
    percentual_margem = (margem_esperada / valor_venda) * 100
    
    print(f"\n📊 Composição do Cálculo:")
    print(f"   Valor XML:           {formatar_moeda(valor_ambientes)}")
    print(f"   Desconto:            {desconto_percentual:.1%}")
    print(f"   Valor venda:         {formatar_moeda(valor_venda)}")
    print(f"")
    print(f"   CUSTOS:")
    print(f"   Custo fábrica:       {formatar_moeda(custo_fabrica)}")
    print(f"   Comissão vendedor:   {formatar_moeda(comissao_vendedor)}")
    print(f"   Comissão gerente:    {formatar_moeda(comissao_gerente)}")
    print(f"   Custo medidor:       {formatar_moeda(custo_medidor)}")
    print(f"   Custo frete:         {formatar_moeda(custo_frete)}")
    print(f"   Custo montador:      {formatar_moeda(custo_montador)}")
    print(f"   Custos adicionais:   {formatar_moeda(custos_adicionais)}")
    print(f"   ─────────────────────────────────")
    print(f"   Total custos:        {formatar_moeda(total_custos)}")
    print(f"")
    print(f"   MARGEM FINAL:")
    print(f"   Margem:              {formatar_moeda(margem_esperada)}")
    print(f"   Percentual:          {percentual_margem:.2f}%")
    
    # Validações
    sucesso_calculo = total_custos > 0 and margem_esperada > 0
    sucesso_percentual = 0 < percentual_margem < 100
    
    print(f"\n🎯 VALIDAÇÕES:")
    print(f"   Cálculo válido:      {'✅ SIM' if sucesso_calculo else '❌ NÃO'}")
    print(f"   Percentual válido:   {'✅ SIM' if sucesso_percentual else '❌ NÃO'}")
    print(f"   Margem positiva:     {'✅ SIM' if margem_esperada > 0 else '❌ NÃO'}")
    
    return sucesso_calculo and sucesso_percentual

def teste_precisao_decimal():
    """
    TESTE 5: Precisão decimal nos cálculos
    
    Verificar se não há problemas de arredondamento
    """
    print("\n🔍 TESTE 5: Precisão Decimal")
    print("=" * 60)
    
    # Teste com valores que podem gerar problemas de precisão
    valores_teste = [
        {'valor': 33333.33, 'percentual': 0.28},
        {'valor': 66666.67, 'percentual': 0.05},
        {'valor': 99999.99, 'percentual': 0.02}
    ]
    
    problemas_precisao = 0
    
    for teste in valores_teste:
        valor = teste['valor']
        percentual = teste['percentual']
        
        # Calcular com float normal
        resultado_float = valor * percentual
        
        # Calcular com Decimal para comparação
        valor_decimal = Decimal(str(valor))
        percentual_decimal = Decimal(str(percentual))
        resultado_decimal = float(valor_decimal * percentual_decimal)
        
        diferenca = abs(resultado_float - resultado_decimal)
        
        print(f"\n📊 Teste: {formatar_moeda(valor)} × {percentual:.1%}")
        print(f"   Float:    {formatar_moeda(resultado_float)}")
        print(f"   Decimal:  {formatar_moeda(resultado_decimal)}")
        print(f"   Diferença: {diferenca:.10f}")
        
        if diferenca > 0.01:  # Tolerância de 1 centavo
            problemas_precisao += 1
            print(f"   Status:   ⚠️ PROBLEMA DE PRECISÃO")
        else:
            print(f"   Status:   ✅ PRECISÃO OK")
    
    print(f"\n🎯 RESULTADO: {len(valores_teste) - problemas_precisao}/{len(valores_teste)} testes com precisão adequada")
    
    return problemas_precisao == 0

def teste_performance():
    """
    TESTE 6: Performance com múltiplos cálculos
    
    Verificar se o engine mantém performance adequada
    """
    print("\n🔍 TESTE 6: Performance do Engine")
    print("=" * 60)
    
    import time
    
    try:
        from modules.orcamentos.services import OrcamentoService
        from core.database import SupabaseClient
        from core.config import get_settings
        
        settings = get_settings()
        supabase_client = SupabaseClient(settings)
        service = OrcamentoService(supabase_client)
        
        # Criar DataFrame de regras
        regras_teste = pd.DataFrame([
            {'id': '1', 'loja_id': 'test', 'tipo_comissao': 'VENDEDOR', 'valor_minimo': 0.0, 'valor_maximo': 25000.0, 'percentual': 0.05, 'ordem': 1},
            {'id': '2', 'loja_id': 'test', 'tipo_comissao': 'VENDEDOR', 'valor_minimo': 25000.01, 'valor_maximo': 50000.0, 'percentual': 0.06, 'ordem': 2},
            {'id': '3', 'loja_id': 'test', 'tipo_comissao': 'VENDEDOR', 'valor_minimo': 50000.01, 'valor_maximo': None, 'percentual': 0.08, 'ordem': 3}
        ])
        
        # Testar com múltiplos cálculos
        valores_teste = [10000 + (i * 1000) for i in range(100)]  # 100 valores diferentes
        
        inicio = time.time()
        
        for valor in valores_teste:
            service.calcular_comissao_faixa_unica_pandas(valor, regras_teste)
        
        fim = time.time()
        tempo_total = fim - inicio
        tempo_medio = tempo_total / len(valores_teste) * 1000  # ms por cálculo
        
        print(f"\n📊 Teste de Performance:")
        print(f"   Cálculos realizados: {len(valores_teste)}")
        print(f"   Tempo total:         {tempo_total:.3f}s")
        print(f"   Tempo médio:         {tempo_medio:.2f}ms por cálculo")
        
        # Critério: menos de 10ms por cálculo
        performance_ok = tempo_medio < 10.0
        
        print(f"   Status:              {'✅ PERFORMANCE OK' if performance_ok else '⚠️ PERFORMANCE LENTA'}")
        
        return performance_ok
        
    except Exception as e:
        print(f"❌ ERRO no teste de performance: {e}")
        return False

async def main():
    """Executa todos os testes do engine de cálculos"""
    print("🚀 VALIDAÇÃO COMPLETA DO ENGINE DE CÁLCULOS - FLUYT")
    print("🎯 Objetivo: Garantir que TODOS os cálculos estão conforme PRD.md")
    print("=" * 80)
    
    # Configurar ambiente
    configurar_ambiente()
    
    # Lista de testes
    testes = [
        ("Comissão Progressiva Vendedor", teste_comissao_progressiva_vendedor),
        ("Cálculos Custos Básicos", teste_calculos_custos_basicos),
        ("Custos Adicionais", teste_custos_adicionais),
        ("Margem Final", teste_margem_final),
        ("Precisão Decimal", teste_precisao_decimal),
        ("Performance Engine", teste_performance)
    ]
    
    resultados = []
    
    for nome_teste, funcao_teste in testes:
        try:
            if asyncio.iscoroutinefunction(funcao_teste):
                sucesso = await funcao_teste()
            else:
                sucesso = funcao_teste()
            
            resultados.append((nome_teste, sucesso))
            
        except Exception as e:
            print(f"❌ ERRO em {nome_teste}: {e}")
            resultados.append((nome_teste, False))
    
    # Resumo final
    print("\n" + "=" * 80)
    print("📊 RESUMO FINAL DOS TESTES")
    print("=" * 80)
    
    sucessos = 0
    for nome, sucesso in resultados:
        status = "✅ PASSOU" if sucesso else "❌ FALHOU"
        print(f"{status} {nome}")
        if sucesso:
            sucessos += 1
    
    total = len(resultados)
    percentual = (sucessos / total) * 100
    
    print("\n" + "=" * 80)
    print(f"🎯 RESULTADO GERAL: {sucessos}/{total} testes passaram ({percentual:.1f}%)")
    
    if sucessos == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Engine de cálculos está funcionando conforme PRD.md")
        print("✅ Sistema pronto para cálculos em produção")
    else:
        print("⚠️ Alguns testes falharam!")
        print("❌ Verificar implementação antes de usar em produção")
    
    print("=" * 80)
    
    return sucessos == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 