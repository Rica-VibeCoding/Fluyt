flowchart TD
    %% Definição de estilos
    classDef inicio fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
    classDef processo fill:#2196F3,stroke:#1565C0,stroke-width:2px,color:#fff
    classDef decisao fill:#FF9800,stroke:#E65100,stroke-width:2px,color:#fff
    classDef sistema fill:#9C27B0,stroke:#6A1B9A,stroke-width:2px,color:#fff
    classDef database fill:#607D8B,stroke:#37474F,stroke-width:2px,color:#fff
    classDef final fill:#F44336,stroke:#C62828,stroke-width:3px,color:#fff

    %% INÍCIO
    START([VENDEDOR INICIA]):::inicio
    
    %% FASE 1: CLIENTE
    C1[Cadastrar Cliente]:::processo
    C2[Salvar na Base]:::database
    C3[Ir para Ambientes]:::processo
    
    %% FASE 2: AMBIENTES
    A1[Upload XML Promob]:::processo
    A2[Sistema Processa XML]:::sistema
    A3[Cria Lista de Ambientes]:::sistema
    A4[Soma Total Automática]:::sistema
    A5[Ir para Orçamento]:::processo
    
    %% FASE 3: ORÇAMENTO
    O1[Inclui TODOS Ambientes]:::sistema
    O2[Criar Plano Pagamento]:::processo
    O3[Aplicar Desconto]:::processo
    O4{Desconto > Limite?}:::decisao
    
    %% CÁLCULOS AUTOMÁTICOS
    CALC[Sistema Calcula Custos e Margem]:::sistema
    
    %% SISTEMA DE APROVAÇÃO
    AP1[Solicitar Aprovação]:::sistema
    AP2{Vendedor Aprova?}:::decisao
    AP3{Gerente Aprova?}:::decisao
    AP4[Admin Visualiza Custos e Margem]:::sistema
    AP5{Admin Master Decide}:::decisao
    AP6[APROVADO]:::final
    AP7[NEGADO - Revisar]:::final
    
    %% GESTÃO DE STATUS
    ST1[Alterar Status]:::processo
    ST2[Adicionar Observação]:::processo
    ST3{Status = Perdido?}:::decisao
    ST4[Bloquear Edição]:::sistema
    
    %% CONTRATO
    CT1[Gerar Contrato]:::sistema
    CT2[Apresentar ao Cliente]:::processo
    CT3[Editar se Necessário]:::processo
    CT4[Assinatura]:::processo
    CT5[Salvar Contrato]:::database
    
    FIM([PROCESSO CONCLUÍDO]):::final
    
    %% FLUXO PRINCIPAL
    START --> C1
    C1 --> C2
    C2 --> C3
    C3 --> A1
    A1 --> A2
    A2 --> A3
    A3 --> A4
    A4 --> A5
    A5 --> O1
    O1 --> O2
    O2 --> O3
    O3 --> O4
    
    %% FLUXO DE APROVAÇÃO
    O4 -->|SIM| AP1
    O4 -->|NÃO| CALC
    
    AP1 --> AP2
    AP2 -->|SIM| AP6
    AP2 -->|NÃO| AP3
    AP3 -->|SIM| AP6
    AP3 -->|NÃO| AP4
    AP4 --> AP5
    AP5 -->|APROVA| AP6
    AP5 -->|NEGA| AP7
    
    %% RETORNO PARA AJUSTES
    AP2 -->|NEGA| AP7
    AP3 -->|NEGA| AP7
    AP7 --> O3
    
    %% APÓS APROVAÇÃO
    AP6 --> CALC
    CALC --> ST1
    ST1 --> ST2
    ST2 --> ST3
    
    ST3 -->|SIM| ST4
    ST3 -->|NÃO| CT1
    ST4 --> FIM
    
    %% FINALIZAÇÃO
    CT1 --> CT2
    CT2 --> CT3
    CT3 --> CT4
    CT4 --> CT5
    CT5 --> FIM