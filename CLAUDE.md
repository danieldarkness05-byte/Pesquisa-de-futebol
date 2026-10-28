# Pesquisa de futebol — instruções para o Claude

Repositório de pesquisa estatística de futebol do Daniel, focado em encontrar
**oportunidades de ouro** em mercados específicos (gols, escanteios, cartões,
chutes) para apostas na Betano. Responda sempre em **português do Brasil**,
de forma curta e direta: o Daniel costuma ler pelo celular.

## Regra 0 — SÓ UNDER (Daniel, 21/10: vale acima de tudo)

**"A partir de agora só me mande jogos under, nada mais. É proibido mandar qualquer outro mercado."**
- Resposta, notificação e rotina: **só "menos de X.5 gols"**. Nenhum outro mercado (vitória, dupla chance, over,
  ambas marcam, handicap, escanteios, cartões) vai para o Daniel, nem como condicional ou "quase".
- O fluxo é o `/under` (`.claude/skills/under/SKILL.md`): mapa de unders → requisitos → pesquisa a fundo → entrega dos
  que passam na análise, **sem odd na resposta** (20/10: "esquece a odd"); odd e EV continuam registrados.
- **Método Under** (`docs/metodo-under.md`, 21/10: "não foque só no Sofascore, use todas as ferramentas de pesquisa"):
  por jogo, estatístico independente (outras fontes + `prob.py`) → pesquisador de contexto → cético; cada número-chave
  em 2 fontes independentes; com o Sofascore fora do ar, o workflow roda no modo web (365Scores, SoccerStats etc.).
- **`/under-top`** (pedido de 21/10): só os **melhores** under do dia. Usa o mesmo mapa do `/under`, mas aplica o
  selo elite (chance final ≥ 80%, folga para a linha, cauda limpa, mercado a favor, cético confiante) e entrega no
  máximo 3 (`analise: "under_top"`).
- **Exceção (Daniel, 21/10): `/favorito`.** Num chat próprio, ele pediu os jogos em que o favorito PRECISA vencer e vai
  com todos os titulares (vitória ou dupla chance). Só nesse modo, e quando ele pedir; a rotina continua só under.
- **Exceção (Daniel, 25/10): `/casa`.** No mesmo chat do `/favorito`, ele trocou para "os mercados em que a casa acredita
  que vai acertar", em qualquer mercado: `casa.py` (só script, sem agentes) fica com o que a bet365 dá 75%+ e com a odd
  caindo 5%+ desde a abertura. Só quando ele pedir; a rotina continua só under.
- `/defesa-fraca`, `/azarao-forte`, `/setenta` e `/fortes` estão **suspensos**. A rotina (só duas vezes ao dia, 06:52 e 17:52; Daniel, 21/10) roda o `/under-top`.
- **1X2 despencando tira o under (Daniel, 23/10: "quando for assim, tira o under da lista"):** se a odd de vitória de
  um time cair 10% ou mais desde a abertura (pela mediana das casas, com clones contando uma vez; lição 68), ou se
  alguém precisar vencer por saldo, o under sai (lição 67). O
  `plataformas.py mapa` já corta; antes de entregar e de novo 1 a 2 h antes do jogo, rode `plataformas.py recheca` e
  avise o Daniel se algum entregue virar CORTA.
- "Continuar evoluindo": cada resultado de under vira lição em `docs/licoes.md`, e lição que se repete vira filtro no
  `under.py` (com teste).

## Regras de ouro (sempre valem)

1. **Só recomende pick com probabilidade estimada ≥ 60% E com valor** (EV ≥ 3%).
   Os números ficam em `config.json` (`criterios`); leia de lá, não assuma.
   *Exceção:* no `/fortes` a entrega é só pela probabilidade final (≥ 80%), sem odd, a pedido do Daniel (20/10:
   "esquece a odd, só me passa os que têm muita chance de bater"). Odd e EV continuam registrados.
2. **Nunca force entrada.** "Nenhuma oportunidade de ouro hoje" é uma resposta
   válida e honesta. Não rebaixe o critério para ter o que mostrar.
3. **Exclua jogos com previsão de chuva no dia da partida** (`clima.py`). Se a
   consulta falhar, marque "chuva não verificada" e não aprove o jogo sem conferir.
   *Exceção:* no `/defesa-fraca`, no `/azarao-forte` e no `/setenta` a chuva é só informativa, a pedido do Daniel
   (12/10 e 16/10: "pode mandar com chuva ou não, isso não interfere").
4. **Defesa fraca:** quando apontar o azarão com defesa muito vazada, marque como
   **⚠️ RISCO** se ele também tiver ataque forte (ex.: marca ≥ 1,3 gol/jogo na condição).
5. **Sofascore é a fonte preferida** — tente primeiro. Se a página não carregar,
   use as alternativas de `docs/fontes.md` e diga qual usou.
6. **Nunca invente estatística.** Todo número vem com fonte e recorte
   (ex.: "Sofascore, últimos 10 jogos em casa, consultado 12/10"). Sem dado
   confiável → "N/D" e o mercado fica de fora.
7. **A probabilidade sai das ferramentas** (`prob.py`, `historico.py`), não de
   palpite. Ajuste qualitativo (desfalque, rodízio, motivação, gramado) só se for
   explícito, pequeno (até ±5 p.p.) e com o motivo escrito.
8. **Sanidade com o mercado:** se sua probabilidade ficar mais de 10 p.p. acima da
   probabilidade da casa sem margem (`valor.py --mercado-odds`), desconfie.
   Procure o que o mercado pode saber (escalação, desfalque, contexto) antes de
   chamar de ouro, e avise o Daniel.
9. **Odds:** não diga que tem odd da Betano sem ter visto. Se o Daniel não colou
   as odds, entregue a **odd mínima** de cada pick para ele conferir no app.

## Ferramentas (rodar da raiz, só Python padrão — nada para instalar)

| Comando | Para quê |
|---|---|
| `python3 ferramentas/prob.py gols ...` | 1X2, dupla chance, ambas marcam, over/under de gols |
| `python3 ferramentas/prob.py contagem ...` | escanteios, cartões, chutes, inclusive janela (`--minutos 10`) |
| `python3 ferramentas/valor.py --prob P --odd O` | EV, odd justa, odd mínima, Kelly, veredito |
| `python3 ferramentas/historico.py confronto ...` | gols esperados pelo histórico da Série A (football-data.co.uk) |
| `python3 ferramentas/clima.py --cidade X --data D --hora H` | previsão de chuva (Open-Meteo) |
| `python3 ferramentas/sistema.py --sel ... --tamanhos 2` | simula Sistema (Duplas/Triplas) |
| `python3 ferramentas/registro.py add/resolver/resumo` | registro de apostas e balanço |
| `python3 ferramentas/varredura.py [--data D] [--todas] [--prob-min 0.70]` | peneira do dia: jogos das ligas do config (ou de todas, com `--todas`) → só mercados com valor |
| `python3 ferramentas/dossie.py [--numeros 1,3] [--json]` | dossiê dos candidatos: odds de agora e da abertura, vivo/caiu, desfalques com gols, forma, chuva |
| `python3 ferramentas/defesa.py [--data D] [--curto] [--json]` | defesa fraca do azarão x ataque forte do favorito em **todas** as ligas do Sofascore: triagem, estatística, alertas, prob. conservadora e odd mínima |
| `python3 ferramentas/azarao.py [--data D] [--curto]` | azarão forte: jogos em que o azarão tem boa chance de não perder (dupla chance, empate anula, vitória) com valor, em todas as ligas |
| `python3 ferramentas/under.py [--data D]` | especialista em under: filtra os "menos de X.5 gols" da peneira `--todas` pelos requisitos de under (cauda, taxa da liga, temporada atual, xG somado, favorito goleador) |
| `python3 ferramentas/casa.py [--data D] [--registrar]` | o que a casa acredita: seleções com 75%+ na bet365 sem margem e odd caindo desde a abertura, em todos os jogos do dia |
| `python3 ferramentas/plataformas.py confere/mapa/anexa [--data D]` | 2ª plataforma com os mesmos dados do Sofascore (365Scores): confirma os unders (CONFIRMADO/DIVERGENTE) e monta o mapa de under sem o Sofascore |
| `python3 ferramentas/previsoes.py add-json/resolver/resumo` | registro de TODA previsão entregue (apostada ou não), resultado automático pelo Sofascore e calibração |

Cada script tem `--help` com exemplos. Use `--json` quando for processar a saída.
Detalhes dos modelos e limitações: `docs/metodologia.md`.

## Fluxo diário (economia de esforço)

> **Desde 21/10 vale a Regra 0: só under.** Os fluxos abaixo ficam como referência; na prática roda o `/under`.

1. **`/ouro`** (rotina diária às 06:52 e às 17:52, só jogos que ainda não começaram): peneira (script) → dossiê (script) → workflow
   `.claude/workflows/aprofundar.js` só nos N melhores candidatos **vivos** → veredito pelas
   ferramentas → notifica só com OURO. Agentes só dentro do workflow: 1 pesquisador + 1 cético por
   candidato, no modelo de `config.json → aprofundar` (`max_candidatos: 0` desliga).
2. **`/defesa-fraca`** (rotina das 06:52, para os jogos de HOJE, e quando o Daniel pedir): primeiro aprende
   (`previsoes.py resolver` + `resumo` + `docs/licoes.md`), depois `defesa.py` → workflow
   `.claude/workflows/defesa.js` (pesquisador + cético, até `config.json → defesa.max_pesquisa`) → veredito →
   salva, registra as previsões e acrescenta as lições novas. Nesta análise a **chuva é só informativa**
   (pedido do Daniel em 12/10) e entram **todas as ligas** do Sofascore. **Favorito precisa de 7+ dos 15 pontos
   nos últimos 5 jogos oficiais (com 6 ou menos, sai; ajuste de 14/10)**, e **favorito cujo técnico vai poupar titulares
   também sai** (pedidos do Daniel em 13/10).
3. **`/azarao-forte`** (quando o Daniel pedir; pedido de 16/10): azarão forte que pode empatar ou ganhar.
   `azarao.py` → workflow `.claude/workflows/azarao.js` → veredito com regra 8 rigorosa → registra com
   `analise: "azarao"`. As mesmas réguas: azarão com 7+ pontos nos últimos 5; técnico do azarão poupando, sai.
4. **`/setenta`** (quando o Daniel pedir; pedido de 16/10): QUALQUER mercado com **70%+** em todas as ligas, hoje e
   amanhã. `varredura.py --todas --prob-min 0.70 --chuva-informativa` → `dossie.py --sufixo todas` → workflow `aprofundar.js` com corte de
   70% → veredito → registra com `analise: "setenta"`. Valor (EV ≥ 3%) e regra 8 continuam obrigatórios.
5. **`/under`** (quando o Daniel pedir; pedido de 17/10): especialista em under de gols, 70%+. `varredura.py --todas`
   → `under.py` (requisitos de under) → `dossie.py --sufixo under` → workflow `.claude/workflows/under.js` (checklist de
   under: desfalques no ataque e na defesa, estilo, motivação, H2H na linha certa, árbitro, mercado) → registra com
   `analise: "under"`.
6. **`/fortes`** (modo principal desde 20/10): mapa de todo mercado com 70%+ (`varredura.py --mapa` + `under.py --varrer`)
   → pesquisa a fundo dos mais fortes (cético em todos) → entrega **só os com prob. final ≥ 80%, sem odd** → registra
   com `analise: "fortes"`. "Vamos manter nesse módulo e ir aprimorando" (Daniel, 20/10).
7. **`/peneira`** (barata): só roda `varredura.py`. Não pesquisa notícias.
8. **`/aprofundar`** (quando o Daniel mandar): dossiê + workflow só nos números pedidos.

**Evolução diária:** toda previsão entregue vai para `dados/previsoes.csv` (`previsoes.py`). O resultado é
resolvido no dia seguinte, e o que cada acerto ou erro ensina vai para `docs/licoes.md`. Esse arquivo é lido
antes de cada análise. Lição que se repete vira alerta automático em `defesa.py` (com teste) ou parâmetro em
`config.json → defesa`.

## Fluxo padrão de análise

1. **Jogos:** data, horário (Brasília), competição, estádio e cidade.
2. **Chuva:** `clima.py` para cada jogo → exclua os com chuva.
3. **Dados:** para vários jogos, use o subagente `pesquisador-jogo` (um por jogo,
   em paralelo). Para um jogo só, pesquise direto.
4. **Probabilidades:** `prob.py` / `historico.py` com os números coletados.
5. **Odds e valor:** compare com as odds que o Daniel colar (ou mostre a odd mínima).
6. **Ranking:** só OURO entra na lista, ordenado por probabilidade e depois EV.
7. **Salvar:** grave a análise em `analises/AAAA-MM-DD-<slug>.md` usando
   `templates/analise.md`.

## Formato da resposta

- **Só mande ao Daniel jogos que passam no critério** (⭐ OURO: prob ≥ 60% e EV ≥ 3%, pelos `criterios`).
  Candidatos da peneira, descartados, "quase" e "mais próximos" ficam só no arquivo da análise, a não
  ser que ele peça. Sem ouro: uma linha, "Nenhuma oportunidade de ouro hoje." (sem notificação).
- Comece pelo resultado: lista de ⭐ OURO ranqueada, ou "nenhuma oportunidade".
- Cada pick em 1–2 linhas: jogo · horário · mercado · prob · odd mínima · odd casa
  (se houver) · EV · motivo curto.
- Descartados (com o motivo: chuva, < 60%, sem valor, dado faltando, RISCO) vão para o arquivo da
  análise; na mensagem, só se o Daniel pedir.
- Fontes no final. Sem textos longos.

## Banca e registro

- Stake por Kelly fracionado com teto (`config.json` → `banca`). Se `valor_banca`
  for 0, mostre a stake em % da banca, não em R$.
- Só registre aposta em `dados/registro-apostas.csv` quando o Daniel confirmar que
  apostou (`/registrar-aposta`).
- O `/balanco` mostra a calibração. Se uma faixa acerta bem menos do que o previsto
  com amostra razoável (≥ 30 apostas), proponha ficar mais conservador ali.

## Convenções

- Datas `AAAA-MM-DD`, horários de Brasília, odds com ponto decimal (`1.85`).
- Mudou algo em `ferramentas/`? Rode `python3 -m unittest discover testes`.
- Mensagens de commit em português.
