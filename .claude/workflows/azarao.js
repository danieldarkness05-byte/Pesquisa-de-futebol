export const meta = {
  name: 'azarao',
  description: 'Azarão forte: 1 pesquisador (Sofascore + imprensa) e 1 cético por candidato do azarao.py',
  whenToUse: 'Depois de `python3 ferramentas/azarao.py`: passe o JSON de dados/cache/sofascore/azarao-<D>.json como args (opcional: args.ids). Usado pelo /azarao-forte.',
  phases: [
    { title: 'Pesquisa', detail: 'força real do azarão, fraquezas do favorito, desfalques, rodízio, o que o mercado sabe' },
    { title: 'Cético', detail: 'tenta derrubar "o azarão não perde" e fecha mercado e ajuste' },
  ],
}

// args = JSON do ferramentas/azarao.py
const D = args || {}
const conf = D.azarao || {}
const crit = D.criterios || { prob_minima: 0.6, ev_minimo: 0.03 }
const maxPesquisa = conf.max_pesquisa ?? 4
const dia = D.data || ''
if (maxPesquisa <= 0) { log('azarao.max_pesquisa = 0: pesquisa desligada'); return { resultados: [], agentes: 0 } }
let alvo = (D.candidatos || []).filter(c => c.passa && !c.risco && !c.erro)
const ids = (Array.isArray(D.ids) ? D.ids : String(D.ids || '').split(',')).map(Number).filter(Boolean)
if (ids.length) {
  alvo = (D.candidatos || []).filter(c => ids.includes(c.id) || ids.includes(c.n))
  if (!alvo.length) { log(`Nenhum candidato com os ids ${ids.join(',')}`); return { resultados: [], agentes: 0 } }
}
const fora = alvo.slice(maxPesquisa)
alvo = alvo.slice(0, maxPesquisa)
if (fora.length) log(`Sem pesquisa (teto de ${maxPesquisa}): ${fora.map(c => c.jogo).join(' | ')}`)
if (!alvo.length) return { resultados: [], agentes: 0 }

const SOFA = `Sofascore pela API pública, com o cliente do repositório (rode da raiz do repositório):
python3 -c "import sys,json;sys.path.insert(0,'ferramentas');import varredura as v;api=v.Sofascore(None,'${dia}');print(json.dumps(api.get('CAMINHO',cache=None),ensure_ascii=False)[:8000])"
Caminhos úteis: event/{id} ; event/{id}/lineups ; event/{id}/pregame-form ; event/{id}/h2h ; event/{id}/odds/1/all ; team/{tid}/events/last/0 ; team/{tid}/events/next/0 ; event/{eid}/statistics ; event/{eid}/incidents ; team/{tid}/unique-tournament/{ut}/season/{sid}/statistics/overall ; team/{tid}/unique-tournament/{ut}/season/{sid}/top-players/overall ; unique-tournament/{ut}/season/{sid}/standings/total|home|away.`
const LICOES = 'ANTES de pesquisar, leia docs/licoes.md (lições de casos anteriores) e confira cada uma que se aplica.'

const PESQ = {
  type: 'object',
  properties: {
    data_confirmada: { type: 'string', description: 'data, hora (Brasília) e estádio reais numa 2ª fonte (365Scores, Flashscore, site da liga)' },
    data_diferente: { type: 'boolean' },
    mando_invertido: { type: 'boolean' },
    forca_azarao: { type: 'string', description: 'números com fonte e recorte: pontos/jogo e saldo na condição, xG pró e contra, contra quem pontuou (fortes ou fracos), tendência, técnico' },
    azarao_forte_de_verdade: { type: 'boolean' },
    fraquezas_favorito: { type: 'string', description: 'forma, rendimento na condição, xG, crise, desfalques' },
    desfalques_azarao: { type: 'array', items: { type: 'string' } },
    desfalques_favorito: { type: 'array', items: { type: 'string' } },
    poupa_titulares_azarao: { type: 'string', enum: ['SIM_CONFIRMADO', 'PROVAVEL', 'NAO', 'N/D'], description: 'o técnico do AZARÃO vai poupar titulares? (se sim, o jogo sai)' },
    poupa_titulares_favorito: { type: 'string', enum: ['SIM_CONFIRMADO', 'PROVAVEL', 'NAO', 'N/D'], description: 'o favorito vai poupar? (ajuda o azarão)' },
    odd_real: { type: 'string', description: 'se o JSON não tem odd_casa para o mercado do azarão (dupla chance, empate anula): odd real em outra casa (Flashscore/Oddsportal/365Scores), com a casa e a fonte; senão "bet365 do JSON"; ou N/D' },
    explica_mercado: { type: 'string', description: 'por que o mercado dá menos chance ao azarão que o modelo (regra 8): notícia, desfalque, motivação, movimento de odds; ou N/D' },
    contexto: { type: 'string', description: 'motivação, calendário, clássico/derby, árbitro, gramado — no máximo 8 linhas' },
    ajuste_pp: { type: 'number', minimum: -5, maximum: 5, description: 'ajuste em p.p. na prob. do mercado do azarão (melhor_mercado), com motivo em contexto' },
    fontes: { type: 'array', items: { type: 'string' } },
  },
  required: ['data_confirmada', 'data_diferente', 'mando_invertido', 'forca_azarao', 'azarao_forte_de_verdade', 'fraquezas_favorito',
    'desfalques_azarao', 'desfalques_favorito', 'poupa_titulares_azarao', 'poupa_titulares_favorito', 'odd_real', 'explica_mercado', 'contexto', 'ajuste_pp', 'fontes'],
}

const CET = {
  type: 'object',
  properties: {
    refutado: { type: 'boolean', description: 'true se a tese "o azarão é forte e não perde (empate ou vitória)" não se sustenta' },
    poupa_titulares_azarao_final: { type: 'string', enum: ['SIM_CONFIRMADO', 'PROVAVEL', 'NAO', 'N/D'] },
    mercado_final: { type: 'string', enum: ['az_dc', 'az_dnb', 'az_vence', 'nenhum'], description: 'mercado do azarão mais seguro que ainda tem prob ≥ 60% e valor' },
    ajuste_final_pp: { type: 'number', minimum: -5, maximum: 5, description: 'ajuste TOTAL em p.p. sobre a prob. do azarao.py para o mercado_final' },
    regra8_explicada: { type: 'boolean', description: 'se o modelo está > 10 p.p. acima do mercado: existe explicação sólida para o mercado estar errado? (false = desconfiar)' },
    pontos_contra: { type: 'array', items: { type: 'string' } },
    pontos_a_favor: { type: 'array', items: { type: 'string' } },
    licao: { type: 'string', description: 'lição NOVA e geral (não repita docs/licoes.md); "" se nenhuma' },
    veredito: { type: 'string' },
  },
  required: ['refutado', 'poupa_titulares_azarao_final', 'mercado_final', 'ajuste_final_pp', 'regra8_explicada', 'pontos_contra', 'pontos_a_favor', 'licao', 'veredito'],
}

const resumo = c => { const { mercado_odds, ...resto } = c; return JSON.stringify(resto) }

const res = await pipeline(
  alvo,
  c => agent(`Você é pesquisador de futebol. Jogo de ${dia} (Brasília): ${c.jogo} (${c.pais} · ${c.competicao}), ${c.hora}, id Sofascore ${c.id}, ids ${JSON.stringify(c.ids)}.
Tese: o AZARÃO (${c.azarao}, ${c.az_casa ? 'em casa' : 'fora'}, odd de vitória ${c.odd_az}) é FORTE e tem boa chance de NÃO PERDER (empate ou vitória) contra o favorito ${c.favorito}.
${LICOES}
Dados do ferramentas/azarao.py (Sofascore; tabela casa/fora e geral, últimos jogos na condição, forma, mercados do azarão com prob. conservadora, odds bet365, prob. do mercado sem margem, alertas): ${resumo(c)}
Pesquise A FUNDO (Sofascore primeiro, depois imprensa local, site da liga e dos clubes):
1) Força real do azarão: pontos/jogo e saldo na condição, xG pró e contra, contra quem pontuou, tendência, técnico, artilheiros disponíveis.
2) Fraquezas do favorito: forma, rendimento na condição, xG, desfalques, crise, motivação.
3) Desfalques dos dois lados e escalação (event/${c.id}/lineups).
4) Rodízio: o técnico do AZARÃO vai poupar titulares? (regra do Daniel: se sim, o jogo sai). E o do favorito?
5) Por que o mercado dá menos chance ao azarão que o modelo (regra 8)? Procure notícia, desfalque, movimento das odds (odds/1/all, abertura x agora).
6) Confirme data, hora e estádio numa 2ª fonte.
7) Se o JSON não tem odd da bet365 para a dupla chance (odd_casa nulo), procure a odd real desse mercado em outra casa (odd_real).
8) Confira o teste de chão só com xG (lição 24): a variante "xg" já está no mínimo do azarao.py quando há xG; sem xG no Sofascore, procure xG em outra fonte (FotMob, FBref) ou diga N/D.
Nunca invente número: todo número com fonte e recorte. Sem dado → N/D.
${SOFA}`, { label: `pesq:${c.azarao}`, phase: 'Pesquisa', schema: PESQ }),
  (p, c) => !p ? { id: c.id, n: c.n, jogo: c.jogo, pesquisa: null, cetico: null, status: 'pesquisa falhou' } : agent(`Você é o CÉTICO. Tente DERRUBAR a tese "${c.azarao} é forte e não perde (empate ou vitória) contra ${c.favorito}" no jogo ${c.jogo} (${c.pais} · ${c.competicao}), ${c.hora} de ${dia}, id Sofascore ${c.id}.
${LICOES}
Dados do azarao.py: ${resumo(c)}
Relatório do pesquisador: ${JSON.stringify(p)}
Confira por conta própria: o azarão pontuou contra quem (fracos?); defesa com sorte (gols sofridos bem abaixo do xG cedido); amostra curta; o favorito em fase ruim só por azar (xG alto)?; desfalques; rodízio do azarão (se for poupar, o jogo sai); e principalmente a REGRA 8: se o modelo está mais de 10 p.p. acima do mercado, quase sempre o mercado sabe algo — só mantenha se houver explicação sólida (regra8_explicada).
Feche o mercado_final (az_dc = empate ou vitória; az_dnb = empate anula; az_vence = vitória) e o ajuste_final_pp (−5 a +5) sobre a prob. do azarao.py para ESSE mercado. Se o modelo estiver > 10 p.p. acima do mercado sem explicação, refutado=true.
Se o caso ensinar algo NOVO e geral que não esteja em docs/licoes.md, escreva em "licao".
${SOFA}`, { label: `cetico:${c.azarao}`, phase: 'Cético', schema: CET })
    .then(t => ({ id: c.id, n: c.n, jogo: c.jogo, hora: c.hora, pesquisa: p, cetico: t, status: t ? 'ok' : 'cetico falhou' })),
)
return { resultados: res.filter(Boolean), agentes: alvo.length * 2, sem_pesquisa: fora.map(c => c.jogo) }
