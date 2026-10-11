# ⚽ Pesquisa de Futebol

Repositório para usar com o **Claude Code**: pesquisa estatística de jogos,
cálculo de probabilidade por mercado e filtro de **oportunidades de ouro**
(probabilidade ≥ 60% **e** valor na odd). Jogos com previsão de chuva saem da lista.

Mercados: gols (under/over, ambas marcam, dupla chance), escanteios (jogo inteiro e
primeiros 10 minutos), cartões (com árbitro), chutes.
Competições: Brasileirão A/B/C, Libertadores, Copa do Nordeste, amistosos.

## Comandos

Digite no Claude Code (ou peça com suas palavras, ele entende):

| Comando | Exemplo |
|---|---|
| `/peneira` | `/peneira` · `/peneira amanhã`: triagem barata, só jogos com valor |
| `/aprofundar` | `/aprofundar` · `/aprofundar 1,3`: análise completa só dos candidatos |
| `/rodada` | `/rodada hoje` · `/rodada amanhã Série B` |
| `/analisar-jogo` | `/analisar-jogo Bahia x Vitória` (pode colar as odds da Betano junto) |
| `/defesa-fraca` | `/defesa-fraca hoje` |
| `/sistema` | `/sistema duplas 5` |
| `/registrar-aposta` | `/registrar-aposta Bahia x Vitória under 2.5 @1.72 R$10` |
| `/balanco` | `/balanco desde 2026-10-01` |

Dica: colar as odds da Betano junto com o pedido deixa o veredito completo. Sem
odds, o Claude mostra a **odd mínima** de cada pick para você conferir no app.

## Como usar pelo celular

1. **Suba este repositório para o GitHub** (pode ser privado).
2. No app do Claude, abra a aba **Code**, conecte o GitHub e escolha este repositório.
3. **Libere a internet do ambiente:** no seletor de ambiente (ícone de nuvem) →
   **Network access** → **Full**. O padrão (*Trusted*) bloqueia Sofascore, a previsão
   do tempo e o histórico. Se preferir restringir, use **Custom** e inclua pelo menos
   `api.open-meteo.com`, `geocoding-api.open-meteo.com`, `www.football-data.co.uk`
   e os sites de estatística que você usa.
4. Mande `/rodada hoje`.

No computador: instale o Claude Code, entre na pasta e rode `claude`.

**Varredura automática:** dá para criar uma rotina do Claude Code com o prompt
`/rodada hoje` nos horários que você quiser (ex.: 8h, 13h e 18h).

## Configuração (`config.json`)

| Campo | Padrão | O que faz |
|---|---|---|
| `criterios.prob_minima` | 0.60 | probabilidade mínima para entrar |
| `criterios.ev_minimo` | 0.03 | valor mínimo (3% de lucro esperado) |
| `banca.valor_banca` | 0 | sua banca em R$ (para sugerir stake em reais) |
| `banca.kelly_fracao` | 0.25 | fração do Kelly usada na stake |
| `banca.stake_max_pct` | 0.02 | teto por aposta (2% da banca) |
| `chuva.janela` | `"dia"` | `"dia"` = chuva em qualquer hora do dia exclui; `"jogo"` = só perto do horário |

Detalhes dos cálculos em [`docs/metodologia.md`](docs/metodologia.md);
fontes de dados em [`docs/fontes.md`](docs/fontes.md).

## Estrutura

```
CLAUDE.md                 regras e fluxo que o Claude segue em toda sessão
config.json               seus critérios, banca e regra de chuva
.claude/skills/           os comandos /rodada, /analisar-jogo, ...
.claude/agents/           pesquisador-jogo (coleta dados de vários jogos em paralelo)
ferramentas/              cálculos em Python (sem instalar nada)
  prob.py                 probabilidades por mercado + veredito
  valor.py                EV, odd justa, odd mínima, Kelly
  historico.py            médias da Série A pelo histórico (football-data.co.uk)
  clima.py                previsão de chuva (Open-Meteo)
  sistema.py              simulação de Duplas/Triplas
  registro.py             registro de apostas, ROI, CLV e calibração
  varredura.py            peneira do dia (Sofascore + modelos + testes de robustez)
analises/                 análises salvas (uma por jogo/rodada)
dados/registro-apostas.csv  seu histórico de apostas
docs/                     metodologia e fontes
testes/                   python3 -m unittest discover testes
```

## Use com os pés no chão

As probabilidades são estimativas: um pick de 65% perde 35% das vezes. O `/balanco`
mostra se as estimativas estão acertando na prática — confie nele mais do que em
qualquer sequência boa ou ruim. Aposte só o que pode perder.
