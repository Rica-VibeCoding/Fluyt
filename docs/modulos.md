# 📦 Visão Modular do Sistema Fluyt (Versão Atualizada)

Este documento descreve a estrutura modular do sistema Fluyt, com foco em oferecer uma plataforma SaaS all-in-one e modular para lojistas de móveis planejados. Cada módulo pode ser ativado de forma independente, conforme a necessidade do cliente.

---

## 🧲 Módulo Comercial

### Objetivo:

Gerenciar o processo comercial completo — desde a captação do lead até o fechamento do contrato. Este módulo é dividido em dois submódulos principais: **CRM** (gestão de leads e pré-venda) e **CPQ** (configuração, precificação e propostas).

---

### 🔹 Submódulo CRM (Customer Relationship Management)

#### Funções:

* Captação e qualificação de leads
* Gestão de funil de vendas (Kanban)
* Histórico de contatos e interações
* Anotações e tarefas associadas ao lead
* Conversão de lead em cliente formal

#### Observação:

Este submódulo é opcional. Alguns lojistas preferem usar ferramentas externas para gestão de leads e iniciam o uso do sistema a partir do cliente formal.

---

### 🔹 Submódulo CPQ (Configure, Price, Quote)

#### Funções:

* Cadastro de cliente e informações comerciais
* Criação e simulação de ambientes/projetos
* Definição de preços, margens e comissões
* Validação de condições comerciais
* Geração de propostas e fechamento de contrato

#### Observação:

Este submódulo é obrigatório para operar no fluxo principal do sistema.

---

### Integração entre CRM e CPQ:

A integração entre os submódulos permite:

* Redução de retrabalho e erros
* Visão unificada do processo comercial
* Transição fluida do lead para a proposta
* Agilidade na geração de orçamentos

**Referências de mercado** recomendam fortemente essa integração como uma melhor prática em sistemas comerciais SaaS:

* [BillingPlatform](https://billingplatform.com/blog/how-does-cpq-crm-integration-work)
* [TechGrid](https://techgrid.com/blog/15-cpq-process-best-practices-for-msps)
* [NetSuite](https://www.netsuite.com/portal/resource/articles/crm/cpq-best-practices.shtml)

---

## 💰 Módulo Financeiro

### Objetivo:

Gerenciar o fluxo financeiro da loja com clareza e inteligência.

### Funções:

* Importação de extrato bancário (.OFX)
* Lançamento manual de receitas e despesas
* Classificação por categorias e centros de custo
* Associação de fornecedores
* Relatórios de entrada, saída e saldo
* Regras de automação e limpeza de descrição

---

## 📦 Módulo de Estoque

### Objetivo:

Controlar o estoque de materiais utilizados nos projetos dos clientes.

### Funções:

* Entrada de materiais (compras, entregas)
* Saída de materiais por requisição de cliente
* Controle de status (em compra, aguardando, disponível)
* Alertas de estoque (crítico, baixo, normal)
* Relatórios de movimentação

---

## 🔧 Módulo de Pós-venda

### Objetivo:

Acompanhar a execução dos projetos após a venda, mantendo o cliente informado e o cronograma sob controle.

### Funções:

* Painel de andamento por cliente
* Cronograma de obra (etapas: medição, corte, entrega, montagem)
* Histórico de comunicação
* Requisição de materiais
* Controle de assistências e manutenções

---

## ⚙️ Módulo de Configurações

### Objetivo:

Centralizar os cadastros básicos, regras e permissões do sistema.

### Funções:

* Cadastros: categorias, centros de custo, fornecedores, bancos
* Regras de comissão, metas e repasse
* Controle de usuários e permissões
* Integrações futuras (ex: plataformas externas)
* Configurações inteligentes (limpeza automática, sensibilidade, aplicação)

---

## 📌 Observações Finais

* O Fluyt permite ativação separada dos módulos conforme o plano do cliente.
* A arquitetura modular permite que o sistema seja adaptado às preferências de cada lojista.
* Todos os módulos compartilham o mesmo banco de dados (Supabase), garantindo consistência e integração entre as áreas.

---
