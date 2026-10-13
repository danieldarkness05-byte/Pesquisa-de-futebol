# Metodologia

## Critério de "oportunidade de ouro"

Uma seleção só é ouro quando as duas condições valem ao mesmo tempo:

- **Probabilidade estimada ≥ `criterios.prob_minima`** (padrão 60%)
- **Valor esperado ≥ `criterios.ev_minimo`** (padrão 3%)

EV = prob × (odd − 1) − (1 − prob). A **odd mínima** é a menor odd que entrega
o EV mínimo: abaixo dela a aposta não entra, mesmo com probabilidade alta.

## Gols — Poisson

Cada time faz gols segundo uma Poisson com média λ (gols esperados).

- **Com médias da liga (método de força):**
  λ mandante = (gols marcados pelo mandante em casa × gols sofridos pelo visitante fora) ÷ média de gols dos mandantes na liga.
  λ visitante = (gols marcados pelo visitante fora × gols sofridos pelo mandante em casa) ÷ média de gols dos visitantes na liga.
- **Sem médias da liga:** média simples entre o ataque de um e a defesa do outro.
- **xG:** se tiver gols esperados confiáveis, passe direto (`--xg-casa`, `--xg-fora`).

Da matriz de placares saem 1X2, dupla chance, ambas marcam e over/under.
`rho_dixon_coles` (ex.: −0.05) corrige a Poisson nos placares baixos (0x0, 1x0,
0x1, 1x1); deixe 0 até ter base para calibrar.

## Escanteios, cartões, chutes — contagem

- **Média do jogo pelos times:** (a favor do mandante em casa + contra o visitante fora) ÷ 2
  + (a favor do visitante fora + contra o mandante em casa) ÷ 2.
- **Cartões:** a média dos times é misturada com a do árbitro (`peso_arbitro_cartoes`).
- **Cartão vermelho:** use a média de vermelhos por jogo com `--linhas 0.5 --lado over`.
- **Dispersão:** muitos mercados de contagem variam mais do que a Poisson prevê.
  Com uma amostra de jogos (`--amostra`), a ferramenta mede variância ÷ média; acima
  de 1 usa binomial negativa (caudas mais largas = estimativas mais prudentes).
- **Janela do início do jogo** (ex.: escanteios nos primeiros 10 min): média do jogo ×
  minutos ÷ `duracao_partida_min` (95, contando acréscimos) × `--fator`. Se houver dado
  real de escanteios no início dos jogos, use-o direto em `--media`.

### Linhas inteiras

Linha `.5` não tem devolução. Linha inteira (ex.: "menos de 2"): por padrão é tratada
como **asiática** (o valor exato devolve). Se na Betano "menos de 2" for simplesmente
"0 ou 1", use `--sem-devolucao` — equivale a under 1.5.

## Chuva

`config.json → chuva`. Com `janela: "dia"` (regra do Daniel), qualquer hora do dia com
probabilidade ≥ `prob_limiar`% ou soma ≥ `mm_limiar` mm exclui o jogo. Com
`janela: "jogo"`, olha só de `horas_antes` antes a `horas_depois` depois do início.

## Banca

Kelly cheio = (prob × (odd − 1) − (1 − prob)) ÷ (odd − 1). Usamos uma fração
(`kelly_fracao`, padrão 25%) com teto (`stake_max_pct`, padrão 2% da banca), porque
as probabilidades são estimativas e erram. Preencha `valor_banca` para ver a stake
em R$.

## Sistema (Duplas, Triplas)

`sistema.py` enumera todas as combinações e todos os cenários de acerto, assumindo
seleções independentes. Seleções do mesmo jogo são correlacionadas — a ferramenta avisa.
Combinar seleções sem valor não cria valor.

## Limitações (leia antes de confiar demais)

- Amostras pequenas (começo de temporada, Série C, Copa do Nordeste) geram médias instáveis.
- O modelo não vê escalação, rodízio, clima, gramado, motivação — isso entra como ajuste
  explícito e pequeno, com motivo escrito.
- Uma probabilidade de 65% erra 35% das vezes. Só o registro ao longo de muitas apostas
  mostra se as estimativas estão calibradas: use `registro.py resumo`.
- **CLV** (sua odd vs. odd de fechamento) positivo de forma consistente é o melhor sinal
  de que a vantagem é real. Anote a odd de fechamento ao resolver as apostas.

## Peneira diária (`varredura.py`)

Triagem automática de todos os jogos das competições em `config.json → varredura`.
Usa a API pública do Sofascore: calendário, estatísticas por jogo, árbitro e odds da bet365.

- **Amostra:** últimos `jogos_amostra` (10) jogos **da mesma liga na condição** (mandante em casa,
  visitante fora). Com menos de `amostra_minima` (5), o jogo fica de fora.
- **Gols:** método de força com 50% gols + 50% xG (quando há xG em ≥ 70% dos jogos). As médias são
  encolhidas para a média da liga (peso de `encolhimento_jogos`). Médias da liga: temporada atual +
  anterior.
- **Escanteios e cartões:** `media_confronto`, com dispersão medida nas amostras. Os cartões entram
  misturados com a média de carreira do árbitro (≥ 15 jogos).
- **Todos os mercados com odd:** 1X2, dupla chance, empate anula, ambas marcam, mais/menos de gols,
  handicap asiático, 1º tempo, primeiro a marcar, escanteios e cartões.
- **Passa só o que tiver prob ≥ `prob_triagem` e EV ≥ `ev_minimo`:**
  - na base, com incerteza nas médias (σ = `incerteza_sigma`) e com Dixon-Coles `rho_variante`;
  - nas demais variantes (sem os 2 últimos jogos, amostra geral, só gols, só xG), com tolerância de
    `tolerancia_variantes`;
  - sem divergência > `regra8_pp` com o mercado sem margem (regra 8);
  - com frequência real nas amostras ≥ triagem − `tolerancia_frequencia`;
  - com a taxa-base da liga a favor. O 1/2/12/empate anula é refeito com a taxa real de empates,
    porque a Poisson subestima empates. Gols com prob ≥ 80% precisam acontecer na liga em pelo menos
    (prob − 10 p.p.).
  - Linhas com odd < `odd_minima_mercado` (ex.: menos de 5.5 a 1.10) são ignoradas: a cauda do modelo
    é pouco confiável e a margem é grande.
- **Chuva:** `clima.py`, só para os jogos que passaram.
- É **triagem**: não vê escalação nem notícia. O veredito vem do `/aprofundar`.

## Defesa fraca x ataque forte (`defesa.py` + `/defesa-fraca`)

Análise diária pedida pelo Daniel em 12/10. Procura jogos em que o **azarão sofre muito gol** e o
**favorito marca muito**, em **todas** as ligas do Sofascore. Parâmetros em `config.json → defesa`.

1. **Triagem:** todo jogo não iniciado com tabela casa/fora.
   - Azarão = pior odd. Sem odds, é o que tem menos pontos por jogo, se a diferença for ≥ `diferenca_ppg_sem_odds`.
   - Passa se o azarão sofre ≥ `indice_defesa_min` × a média da liga **na condição** e o favorito marca
     ≥ `indice_ataque_min` × a média.
   - Ligas profissionais com amostra boa são aprofundadas primeiro.
2. **Estatística** dos `max_aprofundar` melhores: últimos `jogos_amostra` jogos de liga na condição,
   com gols, xG, chutes, mediana, frequência de k+ gols, tendência dos últimos 5, expulsões, calendário,
   odds bet365 e λ implícito do mercado (1X2 + over 2,5).
3. **Probabilidade** dos mercados "favorito marca 1+/2+/3+", vitória e dupla chance:
   - É o **menor** valor entre três caminhos:
     - tabela da temporada (método de força);
     - λ encolhido por gols;
     - λ encolhido gols+xG.
     Todos com Dixon-Coles ρ e incerteza σ.
   - Depois, é **limitada pela frequência real + `tolerancia_frequencia`**, porque o Poisson exagera
     quando a média vem de goleadas. Na vitória, a frequência é a de vitórias do favorito e de derrotas do
     azarão.
   - Na vitória, a Poisson subestima empates: com a taxa real de empates da liga maior que a do modelo,
     a vitória é reescalada.
   - Tabela com vários grupos ou fases: vale o grupo em que os dois times jogaram.
   - Sem amostra recente (menos de 3 jogos na condição): o jogo não passa (regra 6).
   - **Forma do favorito** (pedido do Daniel em 13/10):
     - conta os últimos `forma_jogos` (5) jogos **oficiais**, em todas as competições, sem amistosos, pelo placar dos 90 min;
     - com **mais derrotas que vitórias**, o jogo sai da lista;
     - o empate é neutro.
   - **Regra 8 por mercado:**
     - nos gols, compara com o λ implícito do 1X2 e das linhas de gols da bet365;
     - na vitória e na dupla chance, com o 1X2/DC sem margem.
4. **Alertas automáticos** (lições de `docs/licoes.md`):
   - ⚠️ RISCO (o azarão também marca);
   - amostra pequena; liga amadora/base;
   - gols sofridos ≫ xG cedido; favorito acima do xG;
   - defesa melhorando nos últimos 5; média inflada por goleadas;
   - calendário apertado ou pausa longa; expulsões;
   - defesa dos últimos jogos melhor que a da tabela;
   - regra 8.
5. **Pesquisa** (`.claude/workflows/defesa.js`), em até `max_pesquisa` candidatos:
   - 1 pesquisador (Sofascore + imprensa + site da liga, incluindo o mando real);
   - 1 cético, que fecha o mercado final e o ajuste (±5 p.p.) e escreve uma lição nova, se houver.
6. **Aprendizado:**
   - toda previsão entregue vai para `dados/previsoes.csv`;
   - `previsoes.py resolver` busca o placar e `previsoes.py resumo` mostra a calibração por faixa;
   - com ≥ 30 resolvidas numa faixa que acerta 5 p.p. ou mais abaixo do previsto, a análise fica mais
     conservadora ali;
   - o que cada caso ensina vai para `docs/licoes.md`, lido antes de cada análise.

**Chuva:** aqui é só informativa (pedido do Daniel). No /ouro, a regra 3 continua valendo.
