# F1 Telemetry Analytics Suite

**Comparação de telemetria em tempo real entre seu carro e o piloto Max Verstappen (FIA Formula 1).**

![Max Verstappen GIF](https://media.giphy.com/media/JziiO62XpYDl1e0Cdl/giphy.gif)

---

## 📌 Visão Geral

Este projeto transforma dados de telemetria F1 (via protocolo UDP do *Telemetry Workshop* do jogo) em uma análise visual completa, comparando seus tempos e desempenho contra a volta mais rápida do Max Verstappen usando dados oficiais do FastF1.

A arquitetura foi reestruturada seguindo princípios de **Software Engineering** para portfólio técnico:
- **Layered Architecture** (Arquitetura em Camadas)
- **Repository Pattern** (Padrão Repositório)
- **Dependency Injection**
- **SOLID Principles**

## 🏗️ Arquitetura do Projeto

```
ProjetoF1/
├── config.py              # Constantes centralizadas
├── main.py                # Entry point enxusto (DI + loop)
├── requirements.txt       # Dependências com versões fixadas
├── database/              # Camada de persistência (SQLite + SQLAlchemy)
│   ├── __init__.py
│   ├── connection.py      # Engine/sessão do banco
│   ├── models.py          # Tabelas: Laps e TelemetrySamples
│   └── lap_repository.py  # CRUD operations
├── ingestion/             # Camada de ingestão de dados
│   ├── protocol_constants.py  # Offsets e IDs de pacotes UDP
│   ├── packet_parser.py       # Funções puras de desempacotamento struct
│   └── udp_listener.py        # Thread UDP com callbacks observador
├── services/              # Camada de serviços de negócio
│   ├── fastf1_service.py    # Ingestão FastF1 + cache
│   └── telemetry_analyzer.py # Cálculos: delta, interpolação, smooth
└── ui/                    # Interface gráfica Tkinter
    ├── __init__.py
    ├── app_window.py        # Main application window (injeção de dependência)
    ├── components/
    │   ├── delta_hud.py     # Widget Delta isolado (tk.Frame)
    │   ├── sidebar.py       # Sidebar com seletores e histórico
    │   └── telemetry_plots.py # Canvas Matplotlib integrado
```

## 🛠️ Funcionalidades

- **Ingestão UDP em tempo real** - Recebe dados do protocolo F1 2020+
- **Carregamento oficial FastF1** - Volta mais rápida do Verstappen por temporada/pista
- **Persistência SQLite** - Metadados e amostras de telemetria em tabelas relacionais indexadas
- **Análise de Delta** - Tempo seu vs. referência em tempo real
- **Visualização Matplotlib** - Gráficos de velocidade, throttle, brake e steer
- **Histórico de voltas** - Salvamento automático em CSV e banco de dados
- **Componentes isolados** - DeltaHUD, Sidebar e TelemetryPlates são tk.Frame reutilizáveis

## 🚀 Como Rodar

### 1. Pré-requisitos

```bash
# Recomendado: criar um ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Executar a aplicação

```bash
python main.py
```

### 3. Captura de dados do jogo

Para que o projeto funcione, você precisa transmitir dados UDP do jogo:
- **Jogo:** F1 2021-2024 (testado com 2024)
- **Porta UDP:** 20773
- **Protocolo:** Telemetry do jogo (pacotes 1, 2 e 6)

## 💾 Banco de Dados

O projeto usa **SQLite** local (`database/f1_telemetry.db`) com SQLAlchemy ORM.

**Tabelas criadas:**
- `laps` - Metadados da volta (track_name, lap_time_seconds, year_reference)
- `telemetry_samples` - Dados de alta resolução (distance, time_ms, speed, throttle, brake, steer) comForeignKey e índices

**Benefício:** Consultas complexas giram em torno de `SELECT * FROM telemetry_samples WHERE lap_id = :id ORDER BY distance ASC` - operações em milissegundos sem I/O em disco.

## 📦 Dependências (requirements.txt)

```
tkinter      # Já vem no Python (interface gráfica)
matplotlib   >=3.6.0     # Renderização de gráficos
numpy        >=1.24.0    # Processamento numérico
scipy        >=1.10.0    # Interpolação de dados
pandas       >=2.1.0     # Manipulação de dados CSV/SQL
fastf1       >=1.10.0    # Dados oficiais FIA
sqlalchemy   >=2.0.0     # ORM e migrations
```

## 📁 Estrutura de Pastas Importante

- `laps/` - CSV's de voltas salvas automaticamente
- `cache/` - Cache FastF1 (acelera carregamento de sessões)
- `database/f1_telemetry.db` - Banco de dados SQLite
- `config.py` - Configurações UDP, caminhos e constantes

## 🎮 Controles da Interface

| Controle | Função |
|----------|--------|
| **Ano** | Seletor de temporada da referência (VER) |
| **Modo Live/Histórico** | Alternar entre dados em tempo real ou análise de volta salva |
| **Analisar Volta** | Carregar volta selecionada da lista histórica |
| **Atualizar** | Atualizar lista de voltas salvas |

## 🤝 Como Contribuir

1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE] para detalhes.

## 🙏 Créditos

- **FastF1** - Dados oficiais da FIA
- **GIPHY** - GIFs do Max Verstappen
- **Protocol UDP** - Dados do Telemetry do jogo F1

---

**Projeto desenvolvido como base de código profissional para portfólio técnico.**