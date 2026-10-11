# Pesquisa de futebol — instruções para o Claude

Repositório de pesquisa estatística de futebol do Daniel, focado em encontrar
**oportunidades de ouro** em mercados específicos (gols, escanteios, cartões,
chutes) para apostas na Betano. Responda sempre em **português do Brasil**,
de forma curta e direta: o Daniel costuma ler pelo celular.

## Regras de ouro (sempre valem)

1. **Só recomende pick com probabilidade estimada ≥ 60% E com valor** (EV ≥ 3%).
   Os números ficam em `config.json` (`criterios`); leia de lá, não assuma.
2. **Nunca force entrada.** "Nenhuma oportunidade de ouro hoje" é uma resposta
   válida e honesta. Não rebaixe o critério para ter o que mostrar.
3. **Exclua jogos com previsão de chuva no dia da partida** (`clima.py`). Se a
   consulta falhar, marque "chuva não verificada" e não aprove o jogo sem conferir.
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
| `python3 ferramentas/varredura.py [--data D]` | peneira do dia: todos os jogos do Sofascore → só mercados com valor |

Cada script tem `--help` com exemplos. Use `--json` quando for processar a saída.
Detalhes dos modelos e limitações: `docs/metodologia.md`.

## Fluxo diário (economia de esforço)

1. **`/peneira`** (rotina diária, barata): só roda `varredura.py`. Não pesquisa notícias.
   Avisa o Daniel (notificação) quando há candidatos.
2. **`/aprofundar`** (quando o Daniel mandar): esforço alto **só** nos candidatos. Envolve escalação,
   desfalques, ajuste explícito e veredito final pelos `criterios`.

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

- Comece pelo resultado: lista de ⭐ OURO ranqueada, ou "nenhuma oportunidade".
- Cada pick em 1–2 linhas: jogo · horário · mercado · prob · odd mínima · odd casa
  (se houver) · EV · motivo curto.
- Depois, descartados em uma linha cada, com o motivo (chuva, < 60%, sem valor,
  dado faltando, RISCO).
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
