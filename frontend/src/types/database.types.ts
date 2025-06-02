export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  public: {
    Tables: {
      auditoria_alteracoes: {
        Row: {
          acao: string | null
          created_at: string | null
          dados_antes: Json | null
          dados_depois: Json | null
          id: string
          ip_address: string | null
          registro_id: string
          tabela: string
          user_agent: string | null
          usuario_id: string
        }
        Insert: {
          acao?: string | null
          created_at?: string | null
          dados_antes?: Json | null
          dados_depois?: Json | null
          id?: string
          ip_address?: string | null
          registro_id: string
          tabela: string
          user_agent?: string | null
          usuario_id: string
        }
        Update: {
          acao?: string | null
          created_at?: string | null
          dados_antes?: Json | null
          dados_depois?: Json | null
          id?: string
          ip_address?: string | null
          registro_id?: string
          tabela?: string
          user_agent?: string | null
          usuario_id?: string
        }
        Relationships: []
      }
      bancos: {
        Row: {
          ativo: boolean | null
          codigo: string | null
          criado_em: string | null
          descricao: string | null
          id: string
          nome: string
        }
        Insert: {
          ativo?: boolean | null
          codigo?: string | null
          criado_em?: string | null
          descricao?: string | null
          id?: string
          nome: string
        }
        Update: {
          ativo?: boolean | null
          codigo?: string | null
          criado_em?: string | null
          descricao?: string | null
          id?: string
          nome?: string
        }
        Relationships: []
      }
      c_ambientes: {
        Row: {
          created_at: string | null
          descricao_completa: string | null
          detalhes_xml: Json | null
          id: string
          linha_produto: string | null
          loja_id: string | null
          nome_ambiente: string
          nome_cliente: string | null
          valor_total: number
        }
        Insert: {
          created_at?: string | null
          descricao_completa?: string | null
          detalhes_xml?: Json | null
          id?: string
          linha_produto?: string | null
          loja_id?: string | null
          nome_ambiente: string
          nome_cliente?: string | null
          valor_total: number
        }
        Update: {
          created_at?: string | null
          descricao_completa?: string | null
          detalhes_xml?: Json | null
          id?: string
          linha_produto?: string | null
          loja_id?: string | null
          nome_ambiente?: string
          nome_cliente?: string | null
          valor_total?: number
        }
        Relationships: [
          {
            foreignKeyName: "c_ambientes_loja_id_fkey"
            columns: ["loja_id"]
            isOneToOne: false
            referencedRelation: "c_lojas"
            referencedColumns: ["id"]
          },
        ]
      }
      c_aprovacao_historico: {
        Row: {
          acao: Database["public"]["Enums"]["acao_aprovacao"]
          aprovador_id: string
          created_at: string | null
          id: string
          margem_resultante: number | null
          nivel_aprovacao: string | null
          observacao: string | null
          orcamento_id: string | null
          valor_desconto: number | null
        }
        Insert: {
          acao: Database["public"]["Enums"]["acao_aprovacao"]
          aprovador_id: string
          created_at?: string | null
          id?: string
          margem_resultante?: number | null
          nivel_aprovacao?: string | null
          observacao?: string | null
          orcamento_id?: string | null
          valor_desconto?: number | null
        }
        Update: {
          acao?: Database["public"]["Enums"]["acao_aprovacao"]
          aprovador_id?: string
          created_at?: string | null
          id?: string
          margem_resultante?: number | null
          nivel_aprovacao?: string | null
          observacao?: string | null
          orcamento_id?: string | null
          valor_desconto?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "c_aprovacao_historico_orcamento_id_fkey"
            columns: ["orcamento_id"]
            isOneToOne: false
            referencedRelation: "c_orcamentos"
            referencedColumns: ["id"]
          },
        ]
      }
      c_clientes: {
        Row: {
          cep: string | null
          cidade: string | null
          cpf_cnpj: string | null
          created_at: string | null
          email: string | null
          endereco: string | null
          id: string
          loja_id: string | null
          nome: string
          observacao: string | null
          telefone: string | null
          tipo_venda: Database["public"]["Enums"]["tipo_venda"] | null
          updated_at: string | null
        }
        Insert: {
          cep?: string | null
          cidade?: string | null
          cpf_cnpj?: string | null
          created_at?: string | null
          email?: string | null
          endereco?: string | null
          id?: string
          loja_id?: string | null
          nome: string
          observacao?: string | null
          telefone?: string | null
          tipo_venda?: Database["public"]["Enums"]["tipo_venda"] | null
          updated_at?: string | null
        }
        Update: {
          cep?: string | null
          cidade?: string | null
          cpf_cnpj?: string | null
          created_at?: string | null
          email?: string | null
          endereco?: string | null
          id?: string
          loja_id?: string | null
          nome?: string
          observacao?: string | null
          telefone?: string | null
          tipo_venda?: Database["public"]["Enums"]["tipo_venda"] | null
          updated_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "c_clientes_loja_id_fkey"
            columns: ["loja_id"]
            isOneToOne: false
            referencedRelation: "c_lojas"
            referencedColumns: ["id"]
          },
        ]
      }
      c_contratos: {
        Row: {
          assinado: boolean | null
          condicoes: string | null
          created_at: string | null
          data_assinatura: string | null
          empresa_id: string | null
          hash_assinatura: string | null
          id: string
          numero_contrato: string
          observacoes: string | null
          orcamento_id: string | null
          updated_at: string | null
          valor_total: number
        }
        Insert: {
          assinado?: boolean | null
          condicoes?: string | null
          created_at?: string | null
          data_assinatura?: string | null
          empresa_id?: string | null
          hash_assinatura?: string | null
          id?: string
          numero_contrato: string
          observacoes?: string | null
          orcamento_id?: string | null
          updated_at?: string | null
          valor_total: number
        }
        Update: {
          assinado?: boolean | null
          condicoes?: string | null
          created_at?: string | null
          data_assinatura?: string | null
          empresa_id?: string | null
          hash_assinatura?: string | null
          id?: string
          numero_contrato?: string
          observacoes?: string | null
          orcamento_id?: string | null
          updated_at?: string | null
          valor_total?: number
        }
        Relationships: [
          {
            foreignKeyName: "c_contratos_empresa_id_fkey"
            columns: ["empresa_id"]
            isOneToOne: false
            referencedRelation: "cad_empresas"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "c_contratos_orcamento_id_fkey"
            columns: ["orcamento_id"]
            isOneToOne: false
            referencedRelation: "c_orcamentos"
            referencedColumns: ["id"]
          },
        ]
      }
      c_lojas: {
        Row: {
          ativo: boolean | null
          created_at: string | null
          email: string | null
          empresa_id: string | null
          endereco: string | null
          id: string
          nome: string
          telefone: string | null
          updated_at: string | null
        }
        Insert: {
          ativo?: boolean | null
          created_at?: string | null
          email?: string | null
          empresa_id?: string | null
          endereco?: string | null
          id?: string
          nome: string
          telefone?: string | null
          updated_at?: string | null
        }
        Update: {
          ativo?: boolean | null
          created_at?: string | null
          email?: string | null
          empresa_id?: string | null
          endereco?: string | null
          id?: string
          nome?: string
          telefone?: string | null
          updated_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "c_lojas_empresa_id_fkey"
            columns: ["empresa_id"]
            isOneToOne: false
            referencedRelation: "cad_empresas"
            referencedColumns: ["id"]
          },
        ]
      }
      c_orcamento_ambientes: {
        Row: {
          ambiente_id: string | null
          created_at: string | null
          id: string
          incluido: boolean | null
          orcamento_id: string | null
        }
        Insert: {
          ambiente_id?: string | null
          created_at?: string | null
          id?: string
          incluido?: boolean | null
          orcamento_id?: string | null
        }
        Update: {
          ambiente_id?: string | null
          created_at?: string | null
          id?: string
          incluido?: boolean | null
          orcamento_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "c_orcamento_ambientes_ambiente_id_fkey"
            columns: ["ambiente_id"]
            isOneToOne: false
            referencedRelation: "c_ambientes"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "c_orcamento_ambientes_orcamento_id_fkey"
            columns: ["orcamento_id"]
            isOneToOne: false
            referencedRelation: "c_orcamentos"
            referencedColumns: ["id"]
          },
        ]
      }
      c_orcamento_custos_adicionais: {
        Row: {
          created_at: string | null
          descricao_custo: string
          id: string
          orcamento_id: string | null
          valor_custo: number
        }
        Insert: {
          created_at?: string | null
          descricao_custo: string
          id?: string
          orcamento_id?: string | null
          valor_custo: number
        }
        Update: {
          created_at?: string | null
          descricao_custo?: string
          id?: string
          orcamento_id?: string | null
          valor_custo?: number
        }
        Relationships: [
          {
            foreignKeyName: "c_orcamento_custos_adicionais_orcamento_id_fkey"
            columns: ["orcamento_id"]
            isOneToOne: false
            referencedRelation: "c_orcamentos"
            referencedColumns: ["id"]
          },
        ]
      }
      c_orcamentos: {
        Row: {
          aprovador_id: string | null
          cliente_id: string | null
          comissao_gerente: number
          comissao_vendedor: number
          config_snapshot: Json | null
          created_at: string | null
          created_by: string | null
          custo_fabrica: number
          custo_frete: number
          custo_medidor: number
          custo_montador: number
          data_aprovacao: string | null
          desconto_percentual: number
          id: string
          loja_id: string | null
          margem_lucro: number
          medidor_selecionado_id: string | null
          montador_selecionado_id: string | null
          necessita_aprovacao: boolean | null
          numero: string
          observacoes: string | null
          plano_pagamento: Json | null
          status_id: string | null
          transportadora_selecionada_id: string | null
          updated_at: string | null
          valor_ambientes: number
          valor_final: number
          vendedor_id: string | null
        }
        Insert: {
          aprovador_id?: string | null
          cliente_id?: string | null
          comissao_gerente: number
          comissao_vendedor: number
          config_snapshot?: Json | null
          created_at?: string | null
          created_by?: string | null
          custo_fabrica: number
          custo_frete: number
          custo_medidor: number
          custo_montador: number
          data_aprovacao?: string | null
          desconto_percentual: number
          id?: string
          loja_id?: string | null
          margem_lucro: number
          medidor_selecionado_id?: string | null
          montador_selecionado_id?: string | null
          necessita_aprovacao?: boolean | null
          numero: string
          observacoes?: string | null
          plano_pagamento?: Json | null
          status_id?: string | null
          transportadora_selecionada_id?: string | null
          updated_at?: string | null
          valor_ambientes: number
          valor_final: number
          vendedor_id?: string | null
        }
        Update: {
          aprovador_id?: string | null
          cliente_id?: string | null
          comissao_gerente?: number
          comissao_vendedor?: number
          config_snapshot?: Json | null
          created_at?: string | null
          created_by?: string | null
          custo_fabrica?: number
          custo_frete?: number
          custo_medidor?: number
          custo_montador?: number
          data_aprovacao?: string | null
          desconto_percentual?: number
          id?: string
          loja_id?: string | null
          margem_lucro?: number
          medidor_selecionado_id?: string | null
          montador_selecionado_id?: string | null
          necessita_aprovacao?: boolean | null
          numero?: string
          observacoes?: string | null
          plano_pagamento?: Json | null
          status_id?: string | null
          transportadora_selecionada_id?: string | null
          updated_at?: string | null
          valor_ambientes?: number
          valor_final?: number
          vendedor_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "c_orcamentos_aprovador_id_fkey"
            columns: ["aprovador_id"]
            isOneToOne: false
            referencedRelation: "cad_equipe"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "c_orcamentos_cliente_id_fkey"
            columns: ["cliente_id"]
            isOneToOne: false
            referencedRelation: "c_clientes"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "c_orcamentos_loja_id_fkey"
            columns: ["loja_id"]
            isOneToOne: false
            referencedRelation: "c_lojas"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "c_orcamentos_medidor_selecionado_id_fkey"
            columns: ["medidor_selecionado_id"]
            isOneToOne: false
            referencedRelation: "cad_equipe"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "c_orcamentos_montador_selecionado_id_fkey"
            columns: ["montador_selecionado_id"]
            isOneToOne: false
            referencedRelation: "cad_montadores"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "c_orcamentos_status_id_fkey"
            columns: ["status_id"]
            isOneToOne: false
            referencedRelation: "config_status_orcamento"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "c_orcamentos_transportadora_selecionada_id_fkey"
            columns: ["transportadora_selecionada_id"]
            isOneToOne: false
            referencedRelation: "cad_transportadoras"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "c_orcamentos_vendedor_id_fkey"
            columns: ["vendedor_id"]
            isOneToOne: false
            referencedRelation: "cad_equipe"
            referencedColumns: ["id"]
          },
        ]
      }
      c_parcelas_contrato: {
        Row: {
          contrato_id: string | null
          created_at: string | null
          data_pagamento: string | null
          data_vencimento: string
          id: string
          numero_parcela: number
          status_pagamento:
            | Database["public"]["Enums"]["status_pagamento"]
            | null
          updated_at: string | null
          valor_parcela: number
        }
        Insert: {
          contrato_id?: string | null
          created_at?: string | null
          data_pagamento?: string | null
          data_vencimento: string
          id?: string
          numero_parcela: number
          status_pagamento?:
            | Database["public"]["Enums"]["status_pagamento"]
            | null
          updated_at?: string | null
          valor_parcela: number
        }
        Update: {
          contrato_id?: string | null
          created_at?: string | null
          data_pagamento?: string | null
          data_vencimento?: string
          id?: string
          numero_parcela?: number
          status_pagamento?:
            | Database["public"]["Enums"]["status_pagamento"]
            | null
          updated_at?: string | null
          valor_parcela?: number
        }
        Relationships: [
          {
            foreignKeyName: "c_parcelas_contrato_contrato_id_fkey"
            columns: ["contrato_id"]
            isOneToOne: false
            referencedRelation: "c_contratos"
            referencedColumns: ["id"]
          },
        ]
      }
      cad_empresas: {
        Row: {
          cnpj: string | null
          created_at: string | null
          id: string
          nome: string
          updated_at: string | null
        }
        Insert: {
          cnpj?: string | null
          created_at?: string | null
          id?: string
          nome: string
          updated_at?: string | null
        }
        Update: {
          cnpj?: string | null
          created_at?: string | null
          id?: string
          nome?: string
          updated_at?: string | null
        }
        Relationships: []
      }
      cad_equipe: {
        Row: {
          ativo: boolean | null
          comissao_percentual_gerente: number | null
          comissao_percentual_vendedor: number | null
          created_at: string | null
          email: string | null
          id: string
          limite_desconto: number | null
          loja_id: string | null
          nome: string
          perfil: Database["public"]["Enums"]["perfil_usuario"]
          setor_id: string | null
          tem_minimo_garantido: boolean | null
          updated_at: string | null
          valor_medicao: number | null
          valor_minimo_garantido: number | null
        }
        Insert: {
          ativo?: boolean | null
          comissao_percentual_gerente?: number | null
          comissao_percentual_vendedor?: number | null
          created_at?: string | null
          email?: string | null
          id?: string
          limite_desconto?: number | null
          loja_id?: string | null
          nome: string
          perfil: Database["public"]["Enums"]["perfil_usuario"]
          setor_id?: string | null
          tem_minimo_garantido?: boolean | null
          updated_at?: string | null
          valor_medicao?: number | null
          valor_minimo_garantido?: number | null
        }
        Update: {
          ativo?: boolean | null
          comissao_percentual_gerente?: number | null
          comissao_percentual_vendedor?: number | null
          created_at?: string | null
          email?: string | null
          id?: string
          limite_desconto?: number | null
          loja_id?: string | null
          nome?: string
          perfil?: Database["public"]["Enums"]["perfil_usuario"]
          setor_id?: string | null
          tem_minimo_garantido?: boolean | null
          updated_at?: string | null
          valor_medicao?: number | null
          valor_minimo_garantido?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "cad_equipe_loja_id_fkey"
            columns: ["loja_id"]
            isOneToOne: false
            referencedRelation: "c_lojas"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "cad_equipe_setor_id_fkey"
            columns: ["setor_id"]
            isOneToOne: false
            referencedRelation: "cad_setores"
            referencedColumns: ["id"]
          },
        ]
      }
      cad_montadores: {
        Row: {
          ativo: boolean | null
          categoria: Database["public"]["Enums"]["categoria_montador"] | null
          created_at: string | null
          id: string
          loja_id: string | null
          nome: string
          valor: number
        }
        Insert: {
          ativo?: boolean | null
          categoria?: Database["public"]["Enums"]["categoria_montador"] | null
          created_at?: string | null
          id?: string
          loja_id?: string | null
          nome: string
          valor: number
        }
        Update: {
          ativo?: boolean | null
          categoria?: Database["public"]["Enums"]["categoria_montador"] | null
          created_at?: string | null
          id?: string
          loja_id?: string | null
          nome?: string
          valor?: number
        }
        Relationships: [
          {
            foreignKeyName: "cad_montadores_loja_id_fkey"
            columns: ["loja_id"]
            isOneToOne: false
            referencedRelation: "c_lojas"
            referencedColumns: ["id"]
          },
        ]
      }
      cad_setores: {
        Row: {
          id: string
          loja_id: string | null
          nome: string
        }
        Insert: {
          id?: string
          loja_id?: string | null
          nome: string
        }
        Update: {
          id?: string
          loja_id?: string | null
          nome?: string
        }
        Relationships: [
          {
            foreignKeyName: "cad_setores_loja_id_fkey"
            columns: ["loja_id"]
            isOneToOne: false
            referencedRelation: "c_lojas"
            referencedColumns: ["id"]
          },
        ]
      }
      cad_transportadoras: {
        Row: {
          ativo: boolean | null
          created_at: string | null
          id: string
          loja_id: string | null
          nome: string
          valor_fixo: number
        }
        Insert: {
          ativo?: boolean | null
          created_at?: string | null
          id?: string
          loja_id?: string | null
          nome: string
          valor_fixo: number
        }
        Update: {
          ativo?: boolean | null
          created_at?: string | null
          id?: string
          loja_id?: string | null
          nome?: string
          valor_fixo?: number
        }
        Relationships: [
          {
            foreignKeyName: "cad_transportadoras_loja_id_fkey"
            columns: ["loja_id"]
            isOneToOne: false
            referencedRelation: "c_lojas"
            referencedColumns: ["id"]
          },
        ]
      }
      config_historico_configuracoes: {
        Row: {
          alterado_por: string
          campo_alterado: string
          data_alteracao: string | null
          id: string
          loja_id: string | null
          motivo_alteracao: string | null
          tabela_alterada: string
          valor_anterior: string | null
          valor_novo: string | null
        }
        Insert: {
          alterado_por: string
          campo_alterado: string
          data_alteracao?: string | null
          id?: string
          loja_id?: string | null
          motivo_alteracao?: string | null
          tabela_alterada: string
          valor_anterior?: string | null
          valor_novo?: string | null
        }
        Update: {
          alterado_por?: string
          campo_alterado?: string
          data_alteracao?: string | null
          id?: string
          loja_id?: string | null
          motivo_alteracao?: string | null
          tabela_alterada?: string
          valor_anterior?: string | null
          valor_novo?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "config_historico_configuracoes_loja_id_fkey"
            columns: ["loja_id"]
            isOneToOne: false
            referencedRelation: "c_lojas"
            referencedColumns: ["id"]
          },
        ]
      }
      config_loja: {
        Row: {
          comissao_minima_gerente: number | null
          comissao_minima_vendedor: number | null
          created_at: string | null
          deflator_custo_fabrica: number
          formato_numeracao:
            | Database["public"]["Enums"]["formato_numeracao"]
            | null
          id: string
          limite_desconto_gerente: number
          limite_desconto_vendedor: number
          loja_id: string | null
          numero_inicial_contrato: number | null
          numero_inicial_orcamento: number | null
          permitir_desconto_negativo: boolean | null
          prefixo_numeracao: string | null
          proximo_numero_contrato: number | null
          proximo_numero_orcamento: number | null
          updated_at: string | null
          updated_by: string | null
          valor_frete_percentual: number
          valor_medidor_padrao: number
        }
        Insert: {
          comissao_minima_gerente?: number | null
          comissao_minima_vendedor?: number | null
          created_at?: string | null
          deflator_custo_fabrica?: number
          formato_numeracao?:
            | Database["public"]["Enums"]["formato_numeracao"]
            | null
          id?: string
          limite_desconto_gerente?: number
          limite_desconto_vendedor?: number
          loja_id?: string | null
          numero_inicial_contrato?: number | null
          numero_inicial_orcamento?: number | null
          permitir_desconto_negativo?: boolean | null
          prefixo_numeracao?: string | null
          proximo_numero_contrato?: number | null
          proximo_numero_orcamento?: number | null
          updated_at?: string | null
          updated_by?: string | null
          valor_frete_percentual?: number
          valor_medidor_padrao?: number
        }
        Update: {
          comissao_minima_gerente?: number | null
          comissao_minima_vendedor?: number | null
          created_at?: string | null
          deflator_custo_fabrica?: number
          formato_numeracao?:
            | Database["public"]["Enums"]["formato_numeracao"]
            | null
          id?: string
          limite_desconto_gerente?: number
          limite_desconto_vendedor?: number
          loja_id?: string | null
          numero_inicial_contrato?: number | null
          numero_inicial_orcamento?: number | null
          permitir_desconto_negativo?: boolean | null
          prefixo_numeracao?: string | null
          proximo_numero_contrato?: number | null
          proximo_numero_orcamento?: number | null
          updated_at?: string | null
          updated_by?: string | null
          valor_frete_percentual?: number
          valor_medidor_padrao?: number
        }
        Relationships: [
          {
            foreignKeyName: "config_loja_loja_id_fkey"
            columns: ["loja_id"]
            isOneToOne: true
            referencedRelation: "c_lojas"
            referencedColumns: ["id"]
          },
        ]
      }
      config_regras_comissao_faixa: {
        Row: {
          ativo: boolean | null
          created_at: string | null
          id: string
          loja_id: string | null
          ordem: number
          percentual: number
          tipo_comissao: string | null
          valor_maximo: number | null
          valor_minimo: number
        }
        Insert: {
          ativo?: boolean | null
          created_at?: string | null
          id?: string
          loja_id?: string | null
          ordem: number
          percentual: number
          tipo_comissao?: string | null
          valor_maximo?: number | null
          valor_minimo: number
        }
        Update: {
          ativo?: boolean | null
          created_at?: string | null
          id?: string
          loja_id?: string | null
          ordem?: number
          percentual?: number
          tipo_comissao?: string | null
          valor_maximo?: number | null
          valor_minimo?: number
        }
        Relationships: [
          {
            foreignKeyName: "config_regras_comissao_faixa_loja_id_fkey"
            columns: ["loja_id"]
            isOneToOne: false
            referencedRelation: "c_lojas"
            referencedColumns: ["id"]
          },
        ]
      }
      config_status_orcamento: {
        Row: {
          bloqueia_edicao: boolean | null
          created_at: string | null
          id: string
          is_default: boolean | null
          is_final: boolean | null
          loja_id: string | null
          nome_status: string
          ordem: number
          updated_at: string | null
        }
        Insert: {
          bloqueia_edicao?: boolean | null
          created_at?: string | null
          id?: string
          is_default?: boolean | null
          is_final?: boolean | null
          loja_id?: string | null
          nome_status: string
          ordem: number
          updated_at?: string | null
        }
        Update: {
          bloqueia_edicao?: boolean | null
          created_at?: string | null
          id?: string
          is_default?: boolean | null
          is_final?: boolean | null
          loja_id?: string | null
          nome_status?: string
          ordem?: number
          updated_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "config_status_orcamento_loja_id_fkey"
            columns: ["loja_id"]
            isOneToOne: false
            referencedRelation: "c_lojas"
            referencedColumns: ["id"]
          },
        ]
      }
      xml_processing_logs: {
        Row: {
          ambientes_criados: number | null
          colecoes_encontradas: string | null
          created_at: string | null
          created_by: string | null
          dados_cliente: Json | null
          error_details: Json | null
          file_size: number | null
          filename: string
          id: string
          loja_id: string | null
          processing_time: number | null
          status: string
          valor_total: number | null
        }
        Insert: {
          ambientes_criados?: number | null
          colecoes_encontradas?: string | null
          created_at?: string | null
          created_by?: string | null
          dados_cliente?: Json | null
          error_details?: Json | null
          file_size?: number | null
          filename: string
          id?: string
          loja_id?: string | null
          processing_time?: number | null
          status: string
          valor_total?: number | null
        }
        Update: {
          ambientes_criados?: number | null
          colecoes_encontradas?: string | null
          created_at?: string | null
          created_by?: string | null
          dados_cliente?: Json | null
          error_details?: Json | null
          file_size?: number | null
          filename?: string
          id?: string
          loja_id?: string | null
          processing_time?: number | null
          status?: string
          valor_total?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "xml_processing_logs_loja_id_fkey"
            columns: ["loja_id"]
            isOneToOne: false
            referencedRelation: "c_lojas"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      user_has_access_to_loja: {
        Args: { target_loja_id: string }
        Returns: boolean
      }
    }
    Enums: {
      acao_aprovacao: "SOLICITADO" | "APROVADO" | "REJEITADO" | "CANCELADO"
      categoria_montador:
        | "MARCENEIRO"
        | "MONTADOR_MOVEIS"
        | "ELETRICISTA"
        | "INSTALADOR_GERAL"
      formato_numeracao: "SEQUENCIAL" | "ANO_SEQUENCIAL" | "PERSONALIZADO"
      perfil_usuario: "VENDEDOR" | "GERENTE" | "MEDIDOR" | "ADMIN_MASTER"
      status_pagamento: "PENDENTE" | "PAGO" | "ATRASADO" | "CANCELADO"
      tipo_venda: "NORMAL" | "FUTURA"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DefaultSchema = Database[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof Database },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof Database
  }
    ? keyof (Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        Database[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof Database }
  ? (Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      Database[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof Database },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof Database
  }
    ? keyof Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof Database }
  ? Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof Database },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof Database
  }
    ? keyof Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof Database }
  ? Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof Database },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof Database
  }
    ? keyof Database[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends { schema: keyof Database }
  ? Database[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

// Constants para facilitar validações
export const Constants = {
  public: {
    Enums: {
      acao_aprovacao: ["SOLICITADO", "APROVADO", "REJEITADO", "CANCELADO"],
      categoria_montador: [
        "MARCENEIRO",
        "MONTADOR_MOVEIS",
        "ELETRICISTA",
        "INSTALADOR_GERAL",
      ],
      formato_numeracao: ["SEQUENCIAL", "ANO_SEQUENCIAL", "PERSONALIZADO"],
      perfil_usuario: ["VENDEDOR", "GERENTE", "MEDIDOR", "ADMIN_MASTER"],
      status_pagamento: ["PENDENTE", "PAGO", "ATRASADO", "CANCELADO"],
      tipo_venda: ["NORMAL", "FUTURA"],
    },
  },
} as const;

// Helper types para facilitar o uso
export type Orcamento = Tables<'c_orcamentos'>;
export type Cliente = Tables<'c_clientes'>;
export type Ambiente = Tables<'c_ambientes'>;
export type Contrato = Tables<'c_contratos'>;
export type Equipe = Tables<'cad_equipe'>;
export type Loja = Tables<'c_lojas'>;
export type ConfigLoja = Tables<'config_loja'>;
export type StatusOrcamento = Tables<'config_status_orcamento'>;

// Helper types para inserção
export type OrcamentoInsert = TablesInsert<'c_orcamentos'>;
export type ClienteInsert = TablesInsert<'c_clientes'>;
export type AmbienteInsert = TablesInsert<'c_ambientes'>;
export type ContratoInsert = TablesInsert<'c_contratos'>;
export type EquipeInsert = TablesInsert<'cad_equipe'>;

// Helper types para atualização
export type OrcamentoUpdate = TablesUpdate<'c_orcamentos'>;
export type ClienteUpdate = TablesUpdate<'c_clientes'>;
export type AmbienteUpdate = TablesUpdate<'c_ambientes'>;
export type ContratoUpdate = TablesUpdate<'c_contratos'>;
export type EquipeUpdate = TablesUpdate<'cad_equipe'>;

// Enum helpers  
export type PerfilUsuario = Enums<'perfil_usuario'>;
export type StatusPagamento = Enums<'status_pagamento'>;
export type TipoVenda = Enums<'tipo_venda'>;
export type AcaoAprovacao = Enums<'acao_aprovacao'>;
export type CategoriaMontador = Enums<'categoria_montador'>;
export type FormatoNumeracao = Enums<'formato_numeracao'>; 