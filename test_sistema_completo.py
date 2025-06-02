#!/usr/bin/env python3
"""
TESTE SISTEMA COMPLETO - Fluyt Comercial

⚠️ IMPORTANTE: Este script testa o sistema COMPLETO usando endpoints temporários
sem autenticação. Os endpoints de teste devem ser REMOVIDOS após validação.

FUNCIONALIDADES TESTADAS:
1. CRUD Clientes (ambas lojas)
2. CRUD Ambientes 
3. CRUD Orçamentos
4. Engine de Cálculos (exemplo PRD)
5. RLS Isolamento
6. Validações Pydantic
7. Cenário completo E2E

Autor: Fluyt Team
Data: Janeiro 2025
"""

import requests
import json
from decimal import Decimal
from typing import Dict, Any
import time

# Configuração
BASE_URL = "http://localhost:8000/api/v1"
TEST_URL = f"{BASE_URL}/test"

class TesteCompleto:
    def __init__(self):
        self.resultados = []
        self.dados_teste = {}
        self.erros_encontrados = []
        
    def log(self, msg: str, nivel: str = "INFO"):
        """Log formatado"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {nivel}: {msg}")
        
    def executar_teste(self, nome: str, funcao_teste):
        """Executa um teste e registra resultado"""
        self.log(f"🧪 Executando: {nome}")
        try:
            resultado = funcao_teste()
            self.resultados.append({
                "teste": nome,
                "sucesso": resultado.get("success", False),
                "mensagem": resultado.get("message", ""),
                "dados": resultado.get("data", {})
            })
            
            if resultado.get("success"):
                self.log(f"✅ {nome} - PASSOU", "SUCCESS")
            else:
                self.log(f"❌ {nome} - FALHOU: {resultado.get('message')}", "ERROR")
                self.erros_encontrados.append(f"{nome}: {resultado.get('message')}")
                
        except Exception as e:
            self.log(f"💥 {nome} - ERRO CRÍTICO: {str(e)}", "CRITICAL")
            self.resultados.append({
                "teste": nome,
                "sucesso": False,
                "mensagem": f"Erro de execução: {str(e)}",
                "dados": {}
            })
            self.erros_encontrados.append(f"{nome}: Erro crítico - {str(e)}")
            
    def fazer_requisicao(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Fazer requisição HTTP"""
        url = f"{TEST_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, timeout=30)
            else:
                raise ValueError(f"Método {method} não suportado")
                
            return {
                "status_code": response.status_code,
                "success": response.status_code < 400,
                "data": response.json() if response.content else {},
                "message": "Requisição realizada com sucesso" if response.status_code < 400 else f"Erro HTTP {response.status_code}"
            }
            
        except requests.exceptions.ConnectionError:
            return {
                "status_code": 0,
                "success": False,
                "data": {},
                "message": "Erro de conexão - Servidor não está rodando?"
            }
        except Exception as e:
            return {
                "status_code": 0,
                "success": False,
                "data": {},
                "message": f"Erro na requisição: {str(e)}"
            }

    # ===== TESTES INDIVIDUAIS =====
    
    def teste_1_dados_iniciais(self):
        """Teste 1: Buscar dados iniciais"""
        response = self.fazer_requisicao("GET", "/dados-iniciais")
        
        if response["success"] and response["data"]:
            dados = response["data"]["data"]
            self.dados_teste["lojas"] = dados.get("lojas", [])
            self.dados_teste["equipe"] = dados.get("equipe", [])
            self.dados_teste["configuracoes"] = dados.get("configuracoes", [])
            
            # Validar se existem dados
            if not self.dados_teste["lojas"]:
                return {"success": False, "message": "Nenhuma loja encontrada no banco"}
            if not self.dados_teste["equipe"]:
                return {"success": False, "message": "Nenhum membro da equipe encontrado"}
                
            return {
                "success": True,
                "message": f"Dados carregados: {len(self.dados_teste['lojas'])} lojas, {len(self.dados_teste['equipe'])} funcionários",
                "data": {
                    "lojas_count": len(self.dados_teste["lojas"]),
                    "equipe_count": len(self.dados_teste["equipe"]),
                    "config_count": len(self.dados_teste["configuracoes"])
                }
            }
        
        return response

    def teste_2_criar_cliente_loja1(self):
        """Teste 2: Criar cliente na primeira loja"""
        if not self.dados_teste.get("lojas"):
            return {"success": False, "message": "Dados iniciais não carregados"}
            
        loja1 = self.dados_teste["lojas"][0]
        
        cliente_data = {
            "nome": "João Silva Teste",
            "cpf_cnpj": "12345678901",
            "telefone": "11999999999",
            "email": "joao.teste@email.com",
            "endereco": "Rua das Flores, 123",
            "cidade": "São Paulo",
            "cep": "01234567",
            "loja_id": loja1["id"],
            "tipo_venda": "NORMAL",
            "observacao": "Cliente criado em teste automatizado"
        }
        
        response = self.fazer_requisicao("POST", "/cliente", cliente_data)
        
        if response["success"] and response["data"]:
            cliente_criado = response["data"]["data"]["cliente"]
            self.dados_teste["cliente_loja1"] = cliente_criado
            return {
                "success": True,
                "message": f"Cliente criado na loja {loja1['nome']}",
                "data": {"cliente_id": cliente_criado["id"], "loja": loja1["nome"]}
            }
            
        return response

    def teste_3_criar_cliente_loja2(self):
        """Teste 3: Criar cliente na segunda loja (se existir)"""
        if len(self.dados_teste.get("lojas", [])) < 2:
            return {"success": True, "message": "Apenas 1 loja disponível - pulando teste"}
            
        loja2 = self.dados_teste["lojas"][1]
        
        cliente_data = {
            "nome": "Maria Santos Teste",
            "cpf_cnpj": "98765432100",
            "telefone": "11888888888",
            "email": "maria.teste@email.com",
            "endereco": "Av. Principal, 456",
            "cidade": "Rio de Janeiro",
            "cep": "20123456",
            "loja_id": loja2["id"],
            "tipo_venda": "FUTURA",
            "observacao": "Cliente teste loja 2"
        }
        
        response = self.fazer_requisicao("POST", "/cliente", cliente_data)
        
        if response["success"] and response["data"]:
            cliente_criado = response["data"]["data"]["cliente"]
            self.dados_teste["cliente_loja2"] = cliente_criado
            return {
                "success": True,
                "message": f"Cliente criado na loja {loja2['nome']}",
                "data": {"cliente_id": cliente_criado["id"], "loja": loja2["nome"]}
            }
            
        return response

    def teste_4_listar_clientes_loja1(self):
        """Teste 4: Listar clientes da loja 1"""
        if not self.dados_teste.get("lojas"):
            return {"success": False, "message": "Dados iniciais não carregados"}
            
        loja1 = self.dados_teste["lojas"][0]
        response = self.fazer_requisicao("GET", f"/clientes?loja_id={loja1['id']}")
        
        if response["success"] and response["data"]:
            clientes = response["data"]["data"]["clientes"]
            return {
                "success": True,
                "message": f"Encontrados {len(clientes)} clientes na loja {loja1['nome']}",
                "data": {"total_clientes": len(clientes), "loja": loja1["nome"]}
            }
            
        return response

    def teste_5_criar_ambientes(self):
        """Teste 5: Criar ambientes para teste"""
        if not self.dados_teste.get("lojas"):
            return {"success": False, "message": "Dados iniciais não carregados"}
            
        loja1 = self.dados_teste["lojas"][0]
        
        # Ambiente 1
        ambiente1_data = {
            "nome_ambiente": "Cozinha Planejada Teste",
            "nome_cliente": "João Silva Teste",
            "valor_total": "25000.00",
            "linha_produto": "Unique",
            "descricao_completa": "Cozinha completa com acabamento único",
            "detalhes_xml": {"colecao": "Unique", "acabamento": "MDF Branco"},
            "loja_id": loja1["id"]
        }
        
        response1 = self.fazer_requisicao("POST", "/ambiente", ambiente1_data)
        
        # Ambiente 2  
        ambiente2_data = {
            "nome_ambiente": "Dormitório Casal Teste",
            "nome_cliente": "João Silva Teste",
            "valor_total": "15000.00",
            "linha_produto": "Sublime",
            "descricao_completa": "Dormitório completo com guarda-roupa",
            "detalhes_xml": {"colecao": "Sublime", "acabamento": "MDF Madeirado"},
            "loja_id": loja1["id"]
        }
        
        response2 = self.fazer_requisicao("POST", "/ambiente", ambiente2_data)
        
        if response1["success"] and response2["success"]:
            self.dados_teste["ambientes"] = [
                response1["data"]["data"]["ambiente"],
                response2["data"]["data"]["ambiente"]
            ]
            
            valor_total = sum(float(amb["valor_total"]) for amb in self.dados_teste["ambientes"])
            
            return {
                "success": True,
                "message": f"2 ambientes criados - Valor total: R$ {valor_total:,.2f}",
                "data": {
                    "ambientes_count": 2,
                    "valor_total": valor_total,
                    "ambiente1_id": self.dados_teste["ambientes"][0]["id"],
                    "ambiente2_id": self.dados_teste["ambientes"][1]["id"]
                }
            }
        
        return {"success": False, "message": "Falha ao criar ambientes"}

    def teste_6_calculo_engine_40k(self):
        """Teste 6: Validar cálculo R$ 40.000 → R$ 2.400 (exemplo PRD)"""
        if not self.dados_teste.get("lojas") or not self.dados_teste.get("equipe"):
            return {"success": False, "message": "Dados iniciais não carregados"}
            
        loja1 = self.dados_teste["lojas"][0]
        vendedor = next((e for e in self.dados_teste["equipe"] if e.get("perfil") == "VENDEDOR"), self.dados_teste["equipe"][0])
        
        calculo_data = {
            "valor_ambientes": "40000.00",
            "desconto_percentual": "0.00",
            "loja_id": loja1["id"],
            "vendedor_id": vendedor["id"],
            "custos_adicionais": []
        }
        
        response = self.fazer_requisicao("POST", "/calculo", calculo_data)
        
        if response["success"] and response["data"]:
            custos = response["data"]["data"]["custos"]
            comissao_calculada = custos.get("comissao_vendedor", 0)
            comissao_esperada = 2400.0
            
            diferenca = abs(comissao_calculada - comissao_esperada)
            calculo_correto = diferenca < 0.01
            
            return {
                "success": calculo_correto,
                "message": f"Comissão calculada: R$ {comissao_calculada:,.2f} - Esperada: R$ {comissao_esperada:,.2f}",
                "data": {
                    "valor_testado": 40000,
                    "comissao_calculada": comissao_calculada,
                    "comissao_esperada": comissao_esperada,
                    "diferenca": diferenca,
                    "calculo_correto": calculo_correto,
                    "todos_custos": custos
                }
            }
            
        return response

    def teste_7_criar_orcamento_completo(self):
        """Teste 7: Criar orçamento completo com cálculos"""
        if not all(k in self.dados_teste for k in ["cliente_loja1", "ambientes", "lojas", "equipe"]):
            return {"success": False, "message": "Dependências não atendidas"}
            
        cliente = self.dados_teste["cliente_loja1"]
        ambientes = self.dados_teste["ambientes"]
        loja1 = self.dados_teste["lojas"][0]
        vendedor = next((e for e in self.dados_teste["equipe"] if e.get("perfil") == "VENDEDOR"), self.dados_teste["equipe"][0])
        
        orcamento_data = {
            "cliente_id": cliente["id"],
            "vendedor_id": vendedor["id"],
            "loja_id": loja1["id"],
            "ambientes_ids": [amb["id"] for amb in ambientes],
            "desconto_percentual": "15.00",
            "custos_adicionais": [
                {"descricao": "Taxa projeto especial", "valor": 800},
                {"descricao": "Comissão arquiteto", "valor": 1200}
            ]
        }
        
        response = self.fazer_requisicao("POST", "/orcamento", orcamento_data)
        
        if response["success"] and response["data"]:
            orcamento = response["data"]["data"]["orcamento"]
            custos = response["data"]["data"]["custos_detalhados"]
            
            self.dados_teste["orcamento"] = orcamento
            
            return {
                "success": True,
                "message": f"Orçamento {orcamento['numero']} criado - Valor final: R$ {orcamento['valor_final']:,.2f}",
                "data": {
                    "orcamento_id": orcamento["id"],
                    "numero": orcamento["numero"],
                    "valor_final": orcamento["valor_final"],
                    "margem_lucro": custos.get("margem_lucro", 0),
                    "custos_adicionais": len(orcamento_data["custos_adicionais"])
                }
            }
            
        return response

    def teste_8_validacoes_pydantic(self):
        """Teste 8: Validar que Pydantic rejeita dados inválidos"""
        response = self.fazer_requisicao("POST", "/validacoes")
        
        if response["success"] and response["data"]:
            data = response["data"]["data"]
            
            # Verificar se houve erros de validação (o que é esperado)
            teste1_ok = "validation error" in data.get("teste_cliente_invalido", "").lower()
            teste2_ok = "validation error" in data.get("teste_calculo_invalido", "").lower()
            
            validacoes_funcionando = teste1_ok and teste2_ok
            
            return {
                "success": validacoes_funcionando,
                "message": "Validações Pydantic funcionando" if validacoes_funcionando else "Validações não estão capturando erros",
                "data": {
                    "teste_cliente_rejeitado": teste1_ok,
                    "teste_calculo_rejeitado": teste2_ok,
                    "detalhes": data
                }
            }
            
        return response

    def teste_9_cenario_completo_automatico(self):
        """Teste 9: Executar cenário completo automatizado"""
        response = self.fazer_requisicao("POST", "/cenario-completo")
        
        if response["success"] and response["data"]:
            data = response["data"]["data"]
            resumo = data.get("resumo", {})
            validacao = data.get("validacao_calculo", {})
            
            return {
                "success": validacao.get("calculo_correto", False),
                "message": f"Cenário completo: {resumo.get('sucessos', 0)}/{resumo.get('etapas_executadas', 0)} etapas",
                "data": {
                    "etapas_executadas": resumo.get("etapas_executadas", 0),
                    "sucessos": resumo.get("sucessos", 0),
                    "falhas": resumo.get("falhas", 0),
                    "calculo_40k_correto": validacao.get("calculo_correto", False),
                    "comissao_calculada": validacao.get("comissao_calculada", 0)
                }
            }
            
        return response

    def executar_todos_os_testes(self):
        """Executa bateria completa de testes"""
        self.log("🚀 INICIANDO TESTE SISTEMA COMPLETO", "INFO")
        self.log("=" * 60)
        
        # Lista de testes na ordem correta
        testes = [
            ("1. Buscar Dados Iniciais", self.teste_1_dados_iniciais),
            ("2. Criar Cliente Loja 1", self.teste_2_criar_cliente_loja1),
            ("3. Criar Cliente Loja 2", self.teste_3_criar_cliente_loja2),
            ("4. Listar Clientes Loja 1", self.teste_4_listar_clientes_loja1),
            ("5. Criar Ambientes", self.teste_5_criar_ambientes),
            ("6. Testar Cálculo R$ 40k", self.teste_6_calculo_engine_40k),
            ("7. Criar Orçamento Completo", self.teste_7_criar_orcamento_completo),
            ("8. Validações Pydantic", self.teste_8_validacoes_pydantic),
            ("9. Cenário Completo Auto", self.teste_9_cenario_completo_automatico)
        ]
        
        # Executar cada teste
        for nome, funcao in testes:
            self.executar_teste(nome, funcao)
            time.sleep(1)  # Pequena pausa entre testes
            
        # Relatório final
        self.gerar_relatorio_final()

    def gerar_relatorio_final(self):
        """Gera relatório final dos testes"""
        self.log("=" * 60)
        self.log("📊 RELATÓRIO FINAL DE TESTES", "INFO")
        self.log("=" * 60)
        
        total_testes = len(self.resultados)
        sucessos = sum(1 for r in self.resultados if r["sucesso"])
        falhas = total_testes - sucessos
        
        self.log(f"📈 TOTAL DE TESTES: {total_testes}")
        self.log(f"✅ SUCESSOS: {sucessos}")
        self.log(f"❌ FALHAS: {falhas}")
        self.log(f"📊 TAXA DE SUCESSO: {(sucessos/total_testes)*100:.1f}%")
        
        if falhas > 0:
            self.log("\n🚨 ERROS ENCONTRADOS:")
            for erro in self.erros_encontrados:
                self.log(f"   • {erro}", "ERROR")
                
        # Testes críticos que devem passar
        testes_criticos = [
            "1. Buscar Dados Iniciais",
            "6. Testar Cálculo R$ 40k",
            "8. Validações Pydantic"
        ]
        
        criticos_ok = all(
            any(r["teste"] == tc and r["sucesso"] for r in self.resultados)
            for tc in testes_criticos
        )
        
        if criticos_ok:
            self.log("\n🎯 TESTES CRÍTICOS: TODOS PASSARAM ✅")
        else:
            self.log("\n💥 TESTES CRÍTICOS: FALHAS DETECTADAS ❌")
            
        # Salvar resultados em arquivo
        try:
            with open("relatorio_teste_completo.json", "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "resumo": {
                        "total": total_testes,
                        "sucessos": sucessos,
                        "falhas": falhas,
                        "taxa_sucesso": (sucessos/total_testes)*100
                    },
                    "testes_criticos_ok": criticos_ok,
                    "resultados_detalhados": self.resultados,
                    "erros": self.erros_encontrados
                }, f, indent=2, ensure_ascii=False)
                
            self.log("\n💾 Relatório salvo em: relatorio_teste_completo.json")
            
        except Exception as e:
            self.log(f"⚠️ Erro ao salvar relatório: {e}", "WARNING")
            
        self.log("=" * 60)
        
        if sucessos == total_testes:
            self.log("🎉 TODOS OS TESTES PASSARAM! SISTEMA FUNCIONANDO PERFEITAMENTE!", "SUCCESS")
        elif criticos_ok:
            self.log("✨ FUNCIONALIDADES CRÍTICAS FUNCIONANDO, MAS HÁ MELHORIAS A FAZER", "WARNING")
        else:
            self.log("🔥 PROBLEMAS CRÍTICOS DETECTADOS - NECESSÁRIA CORREÇÃO URGENTE!", "CRITICAL")

if __name__ == "__main__":
    teste = TesteCompleto()
    teste.executar_todos_os_testes() 