"""
Módulo de conexão com banco de dados Supabase.
"""

import os
from supabase import create_client, Client
from typing import Optional

# Configurações do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """
    Retorna uma instância do cliente Supabase.
    Cria uma nova instância se não existir.
    """
    global _supabase_client
    
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError(
                "Variáveis de ambiente SUPABASE_URL e SUPABASE_ANON_KEY são obrigatórias"
            )
        
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    return _supabase_client

def reset_supabase_client():
    """
    Reseta o cliente Supabase (útil para testes).
    """
    global _supabase_client
    _supabase_client = None 