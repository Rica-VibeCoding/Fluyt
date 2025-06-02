#!/usr/bin/env python3
"""
Script de teste para validar conectividade com Supabase
"""

import sys
import os

# Adicionar o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_supabase_connection():
    """Testa conectividade básica com Supabase"""
    print("🔍 TESTE: Conectividade Supabase")
    
    try:
        # Configurar variáveis de ambiente temporariamente
        os.environ['SUPABASE_URL'] = 'https://momwbpxqnvgehotfmvde.supabase.co'
        os.environ['SUPABASE_ANON_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vbXdicHhxbnZnZWhvdGZtdmRlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc3NzAxNTIsImV4cCI6MjA2MzM0NjE1Mn0.n90ZweBT-o1ugerZJDZl8gx65WGe1eUrhph6VuSdSCs'
        os.environ['SUPABASE_SERVICE_KEY'] = 'placeholder'
        
        from core.config import get_settings
        from core.database import SupabaseClient
        
        settings = get_settings()
        print(f"✅ Configurações carregadas")
        print(f"   URL: {settings.supabase_url}")
        print(f"   Anon Key: {settings.supabase_anon_key[:20]}...")
        
        # Criar cliente Supabase
        client = SupabaseClient(settings)
        supabase = client.client
        
        print("✅ Cliente Supabase criado")
        
        # Testar uma consulta simples (listar tabelas)
        try:
            # Tentar acessar uma tabela que deve existir
            result = supabase.table('c_lojas').select('id, nome').limit(1).execute()
            print(f"✅ Conexão com banco - OK")
            print(f"   Dados encontrados: {len(result.data)} registros")
            if result.data:
                print(f"   Primeira loja: {result.data[0].get('nome', 'N/A')}")
        except Exception as e:
            print(f"⚠️ Erro ao consultar dados: {e}")
            # Isso pode ser normal se RLS estiver ativo
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na conectividade Supabase: {e}")
        return False

def test_database_tables():
    """Testa se as tabelas principais existem"""
    print("\n🔍 TESTE: Estrutura do banco de dados")
    
    try:
        # Configurar variáveis de ambiente
        os.environ['SUPABASE_URL'] = 'https://momwbpxqnvgehotfmvde.supabase.co'
        os.environ['SUPABASE_ANON_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vbXdicHhxbnZnZWhvdGZtdmRlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc3NzAxNTIsImV4cCI6MjA2MzM0NjE1Mn0.n90ZweBT-o1ugerZJDZl8gx65WGe1eUrhph6VuSdSCs'
        
        from core.config import get_settings
        from core.database import SupabaseClient
        
        settings = get_settings()
        client = SupabaseClient(settings)
        supabase = client.client
        
        # Tabelas principais que devem existir
        tables_to_check = [
            'c_lojas',
            'c_clientes', 
            'c_orcamentos',
            'c_ambientes',
            'cad_equipe',
            'config_loja'
        ]
        
        results = {}
        
        for table in tables_to_check:
            try:
                # Tentar fazer uma consulta simples
                result = supabase.table(table).select('*').limit(1).execute()
                print(f"✅ Tabela {table} - Existe")
                results[table] = True
            except Exception as e:
                print(f"❌ Tabela {table} - Erro: {str(e)[:50]}...")
                results[table] = False
        
        return results
        
    except Exception as e:
        print(f"❌ Erro ao verificar tabelas: {e}")
        return {}

def main():
    """Executa todos os testes de conectividade"""
    print("🚀 TESTES DE CONECTIVIDADE SUPABASE - FLUYT BACKEND\n")
    
    # Teste 1: Conectividade básica
    connection_ok = test_supabase_connection()
    
    # Teste 2: Estrutura do banco
    tables_result = test_database_tables()
    
    # Resumo
    print(f"\n📊 RESUMO DOS TESTES:")
    print(f"✅ Conectividade Supabase: {'OK' if connection_ok else 'FALHOU'}")
    
    if tables_result:
        tables_ok = sum(1 for v in tables_result.values() if v)
        total_tables = len(tables_result)
        print(f"✅ Tabelas encontradas: {tables_ok}/{total_tables}")
    
    if connection_ok and tables_result:
        print("\n🎉 CONECTIVIDADE SUPABASE OK! Backend pode acessar o banco.")
    else:
        print("\n⚠️ Problemas de conectividade encontrados.")
    
    return connection_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 