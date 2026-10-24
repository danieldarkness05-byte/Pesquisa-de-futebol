export const meta = {
  name: 'favorito',
  description: 'Favorito que precisa vencer: pesquisador (importância, titulares, dados em todas as fontes, prob. independente) e cético por jogo',
  whenToUse: 'Modo "favorito precisa vencer" (pedido do Daniel em 21/10). args = {data, criterios, candidatos} com mercado sem margem e modelo do 365Scores por jogo.',
  phases: [
    { title: 'Pesquisa', detail: 'o que está em jogo, escalação e titulares, desfalques, dados cruzados, prob. independente' },
    { title: 'Cético', detail: 'confere importância e titulares em outra fonte e tenta derrubar' },
  ],
}

const D = args || {}
const crit = D.criterios || { prob_minima: 0.6, ev_minimo: 0.03 }
const alvo = D.candidatos || []
let agentes = 0
const roda = (prompt, opts) => { agentes++; return agent(prompt, opts) }
const pct = x => (x == null ? 'N/D' : `${(100 * x).toFixed(1)}%`)
const num = { type: ['number', 'null'] }
const NIVEL = { type: 'string', enum: ['MUITO_ALTA', 'ALTA', 'MEDIA', 'BAIXA'] }
const TITULARES = { type: 'string', enum: ['TODOS', 'QUASE_TODOS', 'RODIZIO', 'ND'] }
const MERCADO = { type: 'string', enum: ['vitoria', 'dupla_chance', 'nenhum'] }

const FONTES = `FONTES: use todas as que existirem e cruze cada fato-chave em 2 fontes independentes.
- Sofascore costuma responder 403 daqui. 365Scores abre por curl com User-Agent de navegador:
  https://webws.365scores.com/web/game/?appTypeId=5&langId=1&timezoneName=America/Sao_Paulo&gameId=ID (jogo, escalação provável quando houver)
  https://webws.365scores.com/web/games/h2h/?appTypeId=5&langId=1&timezoneName=America/Sao_Paulo&gameId=ID
  https://webws.365scores.com/web/standings/?appTypeId=5&langId=1&timezoneName=America/Sao_Paulo&competitions=CID (type=2 casa, type=3 fora)
- Escalação e desfalques: site e redes oficiais do clube, imprensa local (ge.globo, Lance, UOL, Gazzetta, Corriere dello Sport, Sky Sport, Marca, AS, ESPN, Récord, El Tiempo, TSN, MLSsoccer.com...), Transfermarkt (lesões e suspensões), FotMob, FlashScore.
- Dados: FBref, FootyStats, SoccerStats, Understat, WhoScored e FotMob (WebFetch ou o trecho do WebSearch; curl daqui leva 403 em vários).
- Odds e movimento: Betexplorer e Oddsportal (abrem por curl).
- Probabilidade: python3 ferramentas/prob.py gols --casa-marcados A --casa-sofridos B --fora-marcados C --fora-sofridos D --liga-mandante E --liga-visitante F --mercados 1,X,2,1X,X2 --json
Use WebSearch e WebFetch (carregue com ToolSearch se precisar) e curl pelo Bash. Nunca invente: cada fato com fonte e data; sem fonte = N/D.`

const PESQ = {
  type: 'object',
  properties: {
    o_que_esta_em_jogo: { type: 'string', description: 'para o FAVORITO, com números: tabela e distância para o objetivo, resultado da ida, eliminação, final, classificação' },
    importancia: { ...NIVEL, description: 'MUITO_ALTA = decisivo (final, mata-mata, precisa vencer para não cair/classificar); ALTA = muito relevante; MEDIA/BAIXA = não precisa' },
    empate_serve: { type: 'string', description: 'o empate serve ao favorito? e ao adversário?' },
    escalacao_provavel: { type: 'string', description: 'XI provável do favorito, com fonte e data' },
    titulares: { ...TITULARES, description: 'TODOS = força máxima; QUASE_TODOS = 1 ou 2 titulares fora por lesão/suspensão; RODIZIO = técnico vai poupar; ND' },
    desfalques_favorito: { type: 'array', items: { type: 'string' }, description: 'jogador, posição, motivo, status, fonte' },
    adversario: { type: 'string', description: 'motivação, desfalques, estilo (retranca?), momento' },
    dados_cruzados: { type: 'string', description: 'forma, casa/fora, H2H, xG — cada número em 2 fontes; divergências' },
    comando_prob: { type: 'string' },
    p_vitoria_independente: num,
    p_empate_independente: num,
    mercado_movimento: { type: 'string', description: 'odd do favorito abertura → agora em 2+ casas' },
    mercado_recomendado: { ...MERCADO, description: 'vitoria (precisa e consegue ganhar) ou dupla_chance (o empate também serve / mais seguro)' },
    ajuste_pp: { type: 'number', minimum: -5, maximum: 5, description: 'p.p. no mercado recomendado, só por fato que os números não medem (motivação, desfalque, rodízio)' },
    motivo_ajuste: { type: 'string' },
    derruba: { type: 'boolean', description: 'true se o favorito não precisa vencer, vai poupar, ou fato forte contra' },
    fontes: { type: 'array', items: { type: 'string' } },
    lacunas: { type: 'string' },
  },
  required: ['o_que_esta_em_jogo', 'importancia', 'empate_serve', 'escalacao_provavel', 'titulares', 'desfalques_favorito', 'adversario',
    'dados_cruzados', 'comando_prob', 'p_vitoria_independente', 'p_empate_independente', 'mercado_movimento', 'mercado_recomendado',
    'ajuste_pp', 'motivo_ajuste', 'derruba', 'fontes', 'lacunas'],
}

const CET = {
  type: 'object',
  properties: {
    refutado: { type: 'boolean', description: 'true com motivo sólido e com fonte para NÃO entrar' },
    motivo: { type: 'string' },
    importancia_final: NIVEL,
    titulares_final: TITULARES,
    mercado_final: MERCADO,
    ajuste_extra_pp: { type: 'number', minimum: -5, maximum: 5 },
    checagens: { type: 'array', items: { type: 'object', properties: { afirmacao: { type: 'string' }, confere: { type: 'boolean' }, fonte: { type: 'string' } }, required: ['afirmacao', 'confere', 'fonte'] } },
    confianca: { type: 'string', enum: ['alta', 'media', 'baixa'] },
    licao: { type: 'string' },
  },
  required: ['refutado', 'motivo', 'importancia_final', 'titulares_final', 'mercado_final', 'ajuste_extra_pp', 'checagens', 'confianca', 'licao'],
}

const resumo = c => JSON.stringify({ ...c, data: D.data })

const promptPesq = c => `Você é o pesquisador do modo "FAVORITO QUE PRECISA VENCER" do Daniel (português do Brasil).
Jogo de ${D.data} (horário de Brasília): ${resumo(c)}
O Daniel só quer jogos em que o favorito (${c.favorito}) PRECISA MUITO vencer (ou, no mínimo, não perder) e vai com TODOS os titulares.
Pesquise a fundo, em todas as fontes:
1) O que está em jogo para o favorito, com números (tabela, distância para o objetivo, resultado da ida, final). O empate serve?
2) Escalação provável e titulares: o técnico vai poupar alguém (jogo importante no fim de semana ou no meio da semana)? Desfalques por lesão ou suspensão, com status.
3) Adversário: motivação, desfalques, estilo (fecha a casinha?), momento.
4) Dados cruzados: forma, casa/fora, H2H e xG, cada número em 2 fontes. Confira os números do 365Scores que vieram no resumo.
5) Rode o prob.py com as médias da temporada (casa do mandante, fora do visitante, médias da liga; para Champions/copas use a liga nacional de cada um e diga isso) e copie p_vitoria e p_empate do favorito.
6) Odds do favorito em 2+ casas e o movimento desde a abertura.
7) Recomende o mercado: "vitoria" (precisa e consegue ganhar) ou "dupla_chance" (empate também serve ou é o mais seguro), ou "nenhum".
Antes, leia docs/licoes.md (lições 8, 9, 11, 15, 16, 26, 29 e 58 tratam de favorito, rodízio, motivação e mercado).
${FONTES}`

const promptCet = (c, p) => `Você é o CÉTICO do modo "favorito que precisa vencer". Tente DERRUBAR a entrada no favorito ${c.favorito} em ${c.jogo} (${c.competicao}), ${c.hora} de ${D.data}.
Dados: ${resumo(c)}
Pesquisador: ${JSON.stringify(p)}
Confira em fonte DIFERENTE: (a) se o jogo é mesmo decisivo para o favorito (o empate não basta? a tabela está certa?), (b) se vai mesmo com os titulares (notícia de rodízio, entrevista do técnico, lesões de última hora), (c) os 2 ou 3 números que mais pesam.
Procure o que faz o favorito tropeçar: adversário que também precisa, retranca, desgaste, viagem, clima, árbitro, mercado indo contra.
Dê importancia_final, titulares_final e mercado_final. ajuste_extra_pp é adicional ao do pesquisador (total ±5). refutado = true só com motivo sólido e com fonte.
${FONTES}`

const ev = (p, odd) => p * (odd - 1) - (1 - p)
const oddMin = p => Math.ceil((1 + crit.ev_minimo) / p * 100 - 1e-9) / 100
const limita = x => Math.max(-5, Math.min(5, x))

function veredito(c, p, k) {
  const motivos = []
  const merc = (k && k.mercado_final) || (p && p.mercado_recomendado) || 'nenhum'
  const imp = (k && k.importancia_final) || (p && p.importancia)
  const tit = (k && k.titulares_final) || (p && p.titulares)
  const pInd = !p ? null : merc === 'vitoria' ? p.p_vitoria_independente
    : (p.p_vitoria_independente != null && p.p_empate_independente != null ? p.p_vitoria_independente + p.p_empate_independente : null)
  const pMod = c.modelo_365 ? (merc === 'vitoria' ? c.modelo_365.vitoria : c.modelo_365.dupla_chance) : null
  const pMerc = merc === 'vitoria' ? c.mercado_sem_margem.vitoria : c.mercado_sem_margem.dupla_chance
  const contas = [pInd, pMod].filter(x => typeof x === 'number' && x > 0 && x <= 1)
  const pb = contas.length ? Math.min(...contas) : pMerc   // duas contas: vale a menor; sem conta, o mercado
  const ajuste = limita((p ? p.ajuste_pp : 0) + (k ? k.ajuste_extra_pp : 0))
  const pf = merc === 'nenhum' ? null : pb + ajuste / 100
  const odd = merc === 'vitoria' ? c.odds_1x2[c.fav_casa ? 0 : 2] : c.odd_dupla_chance_aprox
  const evf = pf != null && odd ? ev(pf, odd) : null
  const gap = pf != null ? pf - pMerc : null
  if (!p) motivos.push('pesquisa falhou')
  if (!k) motivos.push('cético falhou')
  if (p && p.derruba) motivos.push('pesquisa derrubou')
  if (k && k.refutado) motivos.push(`cético refutou: ${k.motivo}`)
  if (merc === 'nenhum') motivos.push('sem mercado')
  if (!['MUITO_ALTA', 'ALTA'].includes(imp)) motivos.push(`importância ${imp || 'N/D'}`)
  if (!['TODOS', 'QUASE_TODOS'].includes(tit)) motivos.push(`titulares: ${tit || 'N/D'}`)
  if (pf != null && pf < crit.prob_minima) motivos.push(`prob. ${pct(pf)} < ${pct(crit.prob_minima)}`)
  const avisos = []
  if (gap != null && gap > 0.1) avisos.push(`regra 8: ${(100 * gap).toFixed(1)} p.p. acima do mercado`)
  if (evf != null && evf < crit.ev_minimo) avisos.push(`sem valor na odd de referência (${odd}): EV ${pct(evf)}`)
  return {
    mercado: merc, importancia: imp, titulares: tit, p_independente: pInd, p_modelo_365: pMod, p_mercado: pMerc,
    p_base: pb == null ? null : +pb.toFixed(4), ajuste_pp: ajuste, p_final: pf == null ? null : +pf.toFixed(4),
    odd_referencia: odd, ev: evf == null ? null : +evf.toFixed(4), odd_minima: pf ? oddMin(pf) : null,
    gap_mercado_pp: gap == null ? null : +(100 * gap).toFixed(1), passa: !motivos.length, motivos, avisos,
  }
}

const res = await pipeline(
  alvo,
  c => roda(promptPesq(c), { label: `pesquisa: ${c.jogo}`, phase: 'Pesquisa', schema: PESQ }).then(p => ({ c, p })),
  ({ c, p }) => {
    if (!p) return { c, p, k: null }
    if (p.derruba || ['MEDIA', 'BAIXA'].includes(p.importancia) || p.titulares === 'RODIZIO') {
      log(`${c.jogo}: sem cético (${p.derruba ? 'pesquisa derrubou' : p.titulares === 'RODIZIO' ? 'rodízio' : 'importância ' + p.importancia})`)
      return { c, p, k: null, parou: true }
    }
    return roda(promptCet(c, p), { label: `cético: ${c.jogo}`, phase: 'Cético', schema: CET }).then(k => ({ c, p, k }))
  },
)

const resultados = res.filter(Boolean).map(({ c, p, k, parou }) => ({
  jogo: c.jogo, hora: c.hora, competicao: c.competicao, favorito: c.favorito, ...veredito(c, p, k), parou: !!parou, pesquisa: p, cetico: k,
}))
const passam = resultados.filter(r => r.passa).sort((a, b) => (b.p_final ?? 0) - (a.p_final ?? 0))
log(`${passam.length} de ${resultados.length} passam. Agentes: ${agentes}`)
return { data: D.data, agentes, passam: passam.map(r => r.jogo), resultados }
