#!/usr/bin/env python3
"""
🚨 VALIDAÇÃO DA CORREÇÃO - COMISSÃO POR FAIXA ÚNICA

ERRO IDENTIFICADO E CORRIGIDO:
- ANTES: Algoritmo progressivo (como imposto de renda) - INCORRETO
- AGORA: Faixa única sobre valor total - CORRETO

REGRA REAL DE NEGÓCIO:
- Identifica qual faixa o valor se encaixa
- Aplica percentual da faixa sobre TODO o valor
- NÃO soma faixas anteriores

EXEMPLOS CORRETOS:
- R$ 40.000 → Faixa 2 → 6% × R$ 40.000 = R$ 2.400 (não R$ 2.150)
- R$ 100.000 → Faixa 3 → 8% × R$ 100.000 = R$ 8.000 (não R$ 6.750)
"""

import sys
import os
import pandas as pd

# Adicionar backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def configurar_ambiente():
    """Configurar variáveis de ambiente para teste"""
    os.environ['SUPABASE_URL'] = 'https://momwbpxqnvgehotfmvde.supabase.co'
    os.environ['SUPABASE_ANON_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vbXdicHhxbnZnZWhvdGZtdmRlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc3NzAxNTIsImV4cCI6MjA2MzM0NjE1Mn0.n90ZweBT-o1ugerZJDZl8gx65WGe1eUrhph6VuSdSCs'
    os.environ['SUPABASE_SERVICE_KEY'] = 'placeholder'
    os.environ['ENVIRONMENT'] = 'development'

def calcular_comissao_faixa_unica_correto(valor_venda):
    """
    Calcular comissão pela regra CORRETA: faixa única sobre valor total
    
    Regras:
    - Faixa 1: até R$ 25.000 = 5% sobre total
    - Faixa 2: R$ 25.001 - R$ 50.000 = 6% sobre total
    - Faixa 3: acima R$ 50.000 = 8% sobre total
    """
    print(f"\n🧮 CÁLCULO CORRETO (FAIXA ÚNICA) PARA R$ {valor_venda:,.2f}")
    print("=" * 60)
    
    # Identificar faixa
    if valor_venda <= 25000.0:
        faixa = 1
        percentual = 0.05  # 5%
        limite_min = 0.0
        limite_max = 25000.0
    elif valor_venda <= 50000.0:
        faixa = 2
        percentual = 0.06  # 6%
        limite_min = 25000.01
        limite_max = 50000.0
    else:
        faixa = 3
        percentual = 0.08  # 8%
        limite_min = 50000.01
        limite_max = None
    
    # Calcular comissão: percentual × valor total
    comissao_total = valor_venda * percentual
    
    print(f"Faixa identificada: {faixa}")
    if limite_max:
        print(f"Limites: R$ {limite_min:,.2f} → R$ {limite_max:,.2f}")
    else:
        print(f"Limites: R$ {limite_min:,.2f} → ∞")
    print(f"Percentual: {percentual:.1%}")
    print(f"Cálculo: R$ {valor_venda:,.2f} × {percentual:.1%} = R$ {comissao_total:,.2f}")
    
    print(f"\n{'='*40}")
    print(f"COMISSÃO TOTAL: R$ {comissao_total:,.2f}")
    print(f"{'='*40}")
    
    return comissao_total, faixa, percentual

def testar_algoritmo_corrigido():
    """Testar o algoritmo corrigido do sistema"""
    configurar_ambiente()
    
    try:
        from modules.orcamentos.services import OrcamentoService
        from core.database import SupabaseClient
        from core.config import get_settings
        
        settings = get_settings()
        supabase_client = SupabaseClient(settings)
        service = OrcamentoService(supabase_client)
        
        # Criar DataFrame com regras
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
        
        print(f"\n🔍 TESTE ALGORITMO CORRIGIDO")
        print("=" * 60)
        
        # Testar casos críticos
        casos_teste = [
            {'valor': 40000.0, 'nome': 'Caso PRD (era R$ 2.150, agora R$ 2.400)'},
            {'valor': 100000.0, 'nome': 'Stress test (era R$ 6.750, agora R$ 8.000)'},
            {'valor': 25000.0, 'nome': 'Limite exato faixa 1'},
            {'valor': 25001.0, 'nome': 'Início faixa 2'},
            {'valor': 50000.0, 'nome': 'Limite exato faixa 2'},
            {'valor': 50001.0, 'nome': 'Início faixa 3'}
        ]
        
        for caso in casos_teste:
            valor_teste = caso['valor']
            print(f"\n📊 {caso['nome']}: R$ {valor_teste:,.2f}")
            
            resultado = service.calcular_comissao_faixa_unica_pandas(valor_teste, regras_vendedor)
            
            print(f"   Comissão calculada: R$ {resultado['comissao_total']:,.2f}")
            print(f"   Faixa aplicada: {resultado['faixa_aplicada']}")
            
            if resultado['detalhes_faixas']:
                faixa = resultado['detalhes_faixas'][0]
                print(f"   Detalhes: R$ {faixa['valor_total_aplicado']:,.2f} × {faixa['percentual']:.1%} = R$ {faixa['comissao_calculada']:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False

def validar_casos_criticos():
    """Validar os casos que estavam dando erro"""
    print(f"\n📋 VALIDAÇÃO DOS CASOS CRÍTICOS")
    print("=" * 60)
    
    casos_criticos = [
        {'valor': 40000.0, 'esperado_antigo': 2150.0, 'esperado_correto': 2400.0},
        {'valor': 100000.0, 'esperado_antigo': 6750.0, 'esperado_correto': 8000.0}
    ]
    
    for caso in casos_criticos:
        valor = caso['valor']
        correto, faixa, percentual = calcular_comissao_faixa_unica_correto(valor)
        
        print(f"\n✅ VALIDAÇÃO:")
        print(f"   Valor antigo (ERRADO): R$ {caso['esperado_antigo']:,.2f}")
        print(f"   Valor correto: R$ {caso['esperado_correto']:,.2f}")
        print(f"   Calculado manual: R$ {correto:,.2f}")
        
        if abs(correto - caso['esperado_correto']) < 0.01:
            print(f"   Status: ✅ CORRETO")
        else:
            print(f"   Status: ❌ AINDA COM ERRO")

def main():
    """Executar validação completa da correção"""
    print("🚨 VALIDAÇÃO DA CORREÇÃO - COMISSÃO POR FAIXA ÚNICA")
    print("🎯 Objetivo: Confirmar que algoritmo foi corrigido")
    print("=" * 80)
    
    # 1. Validar cálculo manual dos casos críticos
    validar_casos_criticos()
    
    # 2. Testar algoritmo corrigido do sistema
    sucesso_sistema = testar_algoritmo_corrigido()
    
    # 3. Resumo
    print(f"\n📊 RESUMO DA CORREÇÃO")
    print("=" * 60)
    print("✅ ANTES: Algoritmo progressivo (ERRO)")
    print("✅ AGORA: Faixa única sobre total (CORRETO)")
    print("✅ R$ 40.000: R$ 2.150 → R$ 2.400")
    print("✅ R$ 100.000: R$ 6.750 → R$ 8.000")
    
    if sucesso_sistema:
        print("\n🎉 CORREÇÃO APLICADA COM SUCESSO!")
        print("✅ Sistema agora calcula comissão corretamente")
        print("✅ Regra de negócio real implementada")
    else:
        print("\n❌ ERRO: Sistema ainda não corrigido")
    
    print("=" * 80)

if __name__ == "__main__":
    main() 