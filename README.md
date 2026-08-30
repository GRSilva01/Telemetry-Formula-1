# F1 Telemetry Analytics Suite

Plataforma desktop de alta performance para captura, persistência e análise comparativa de telemetria da Fórmula 1 em tempo real contra dados oficiais de voltas de referência da FIA (Max Verstappen).

<p align="center">
  <img src="https://media.giphy.com/media/JziiO62XpYDl1e0Cdl/giphy.gif" alt="Max Verstappen F1" width="550"/>
</p>

---

## Visão Geral da Engenharia

O projeto foi desenvolvido como uma demonstração prática de arquitetura limpa em Python, processando streams de dados binários em tempo real via UDP a 60 Hz sem comprometer o ciclo de renderização gráfica da interface.

### Decisões Técnicas & Arquiteturais
- **Layered Architecture:** Separação estrita de responsabilidades entre Ingestão de Rede, Camada de Negócios/Análise, Persistência e UI.
- **Concorrência & Thread-Safety:** Isolamento do loop de captura de socket UDP em thread secundária, sincronizando mutações de estado com a thread principal de UI via *Thread Locks*.
- **Processamento Numérico Otimizado:** Interpolação e cálculo de Delta ponto a ponto vetorizados com NumPy puro (`np.interp`), garantindo desempenho em tempo real e portabilidade em ambientes Windows.
- **Repository Pattern & ORM:** Persistência relacional com SQLAlchemy/SQLite para consulta e replay instantâneo de sessões anteriores.

---

##  Estrutura do Projeto

```text
ProjetoF1/
├── config.py                 # Constantes globais e configurações de rede/API
├── main.py                   # Ponto de entrada da aplicação
├── requirements.txt          # Dependências do projeto
├── database/                 # Camada de Persistência (SQLite + SQLAlchemy)
│   ├── connection.py         # Configuração de Engine e Session
│   ├── models.py             # Modelagem de dados (Laps e TelemetrySamples)
│   └── lap_repository.py     # Padrão Repository para operações CRUD
├── ingestion/                # Camada de Ingestão de Dados
│   ├── protocol_constants.py # Estruturas binárias (struct) e mapas de circuitos
│   └── udp_listener.py       # Emissor UDP assíncrono com padrão Observer
├── services/                 # Regras de Negócio e APIs Externas
│   ├── fastf1_service.py     # Integração com FastF1, cache local e fallback
│   └── telemetry_analyzer.py # Cálculos de delta escalar e interpolação linear
└── ui/                       # Interface Gráfica e Visualização
    ├── app_window.py         # Janela principal e loop de atualização
    └── components/
        └── telemetry_plots.py # Gráficos integrados via Matplotlib (TkAgg)

## Funcionalidades
Streaming UDP em Tempo Real: Decodificação de pacotes binários de telemetria (IDs 1, 2 e 6) do protocolo oficial dos jogos da franquia F1.

Benchmark com Dados Reais da FIA: Integração com o FastF1 para download e processamento da telemetria da volta mais rápida oficial do circuito.

HUD de Delta Dinâmico: Cálculo escalar instantâneo da diferença de tempo (ganho/perda) ao longo do traçado.

Visualização Multi-Eixo: Gráficos de velocidade linear, curso de acelerador, freio e ângulo de esterçamento sincronizados por distância da pista.

Histórico & Replay de Voltas: Salvamento de voltas completadas no banco de dados local com suporte a replay analítico na interface.

## Modelagem de Dados
A persistência utiliza SQLite gerenciado pelo SQLAlchemy ORM:

laps: Armazena metadados da volta (circuito, tempo final, ano de referência e timestamp).

telemetry_samples: Registros de alta densidade (distância, tempo em milissegundos, velocidade, inputs de pedais e volante) indexados por chave estrangeira (lap_id).

## Como Executar


1. Clonar o repositório e preparar o ambiente

```
# Criar o ambiente virtual
python -m venv .venv

# Ativar o ambiente virtual (Windows)
.venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt
```

2. Configurar o jogo (F1 2021+)
Nas opções de telemetria do simulador:

UDP Telemetry: Ligado (On)

UDP IP Address: 127.0.0.1

UDP Port: 20773

UDP Send Rate: 60Hz (ou superior)

3. Iniciar a aplicação

```
python main.py
```

## Dependências Principais
- FastF1: Acesso à telemetria oficial de finais de semana de corrida da FIA.

- NumPy & Pandas: Tratamento vetorial de séries temporais e interpolação.

- Matplotlib: Renderização gráfica personalizada embarcada no Tkinter.

- SQLAlchemy: Mapeamento objeto-relacional e persistência estruturada.

---