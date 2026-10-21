export const meta = {
  name: 'under',
  description: 'Método Under: estatístico independente, pesquisador de contexto e cético por candidato, em todas as fontes da internet; modo web quando o Sofascore cai',
  whenToUse: 'Depois de `python3 ferramentas/under.py` + `python3 ferramentas/dossie.py --sufixo under --json`: passe o JSON do dossiê como args. Sem Sofascore: args = {data, modo: "web"}. Usado pelo /under e pelo /under-top (docs/metodo-under.md).',
  phases: [
    { title: 'Descoberta', detail: 'só no modo web: acha os unders do dia sem o Sofascore' },
    { title: 'Estatística', detail: 'números de fontes independentes do Sofascore + prob.py' },
    { title: 'Contexto', detail: 'escalação, desfalques, estilo, motivação, árbitro, clima, mercado' },
    { title: 'Cético', detail: 'confere as afirmações-chave em outra fonte e tenta derrubar o under' },
  ],
}

// args = saída do dossie.py --sufixo under --json (cada candidato traz o bloco `under` do under.py)
//   ou {data, modo: 'web'} quando o Sofascore está fora do ar.
// Opcionais: criterios.prob_minima (0.70 no /under, 0.80 no /under-top), under.max_pesquisa, elite_min (0.80),
//   estatistico (false desliga o estatístico independente), max_descoberta (modo web, padrão 8).
const D = args || {}
const crit = D.criterios || { prob_minima: 0.7, ev_minimo: 0.03 }
const regra8 = D.regra8_pp || 0.1
const eliteMin = D.elite_min || 0.8
const conf = D.aprofundar || {}
const modelo = conf.modelo_agentes || undefined
const maxPesquisa = (D.under && D.under.max_pesquisa) ?? 5
const usarEstatistico = D.estatistico !== false
const web = D.modo === 'web'
let agentes = 0
const roda = (prompt, opts) => { agentes++; return agent(prompt, { model: modelo, ...opts }) }

const pct = x => (x == null ? 'N/D' : `${(100 * x).toFixed(1)}%`)
const num = { type: ['number', 'null'] }
const int = { type: ['integer', 'null'] }

const FONTES = `FONTES (docs/metodo-under.md). Não fique só no Sofascore: cada número que decide o pick precisa de 2 fontes independentes.
- Sofascore pela API, com o cliente do repositório (pode estar bloqueado com 403):
  python3 -c "import sys,json;sys.path.insert(0,'ferramentas');import varredura as v;api=v.Sofascore(None,'${D.data}');print(json.dumps(api.get('CAMINHO',cache=None),ensure_ascii=False)[:8000])"
  Caminhos: event/{id} ; event/{id}/lineups ; event/{id}/h2h ; event/{id}/odds/1/all ; team/{tid}/events/last/0 ; event/{eid}/statistics.
- 365Scores (API sem chave, abre por curl com User-Agent de navegador; datas DD/MM/AAAA):
  jogos do dia: https://webws.365scores.com/web/games/allscores/?appTypeId=5&langId=31&timezoneName=America/Sao_Paulo&userCountryId=21&sports=1&startDate=D&endDate=D&showOdds=true
  jogo: https://webws.365scores.com/web/game/?appTypeId=5&langId=31&timezoneName=America/Sao_Paulo&gameId=ID
  H2H: https://webws.365scores.com/web/games/h2h/?appTypeId=5&langId=31&timezoneName=America/Sao_Paulo&gameId=ID
- SoccerStats (curl ok): https://www.soccerstats.com/latest.asp?league=<liga> (casa/fora, over/under por time).
- Understat (curl ok, 6 grandes ligas: xG), Transfermarkt (curl ok: lesões, suspensões, árbitro), Betexplorer e Oddsportal (curl ok: odds e movimento das linhas de gols).
- FBref, FootyStats, WhoScored, WorldFootball, FotMob, FlashScore, Soccerway: WebFetch ou o trecho do WebSearch (curl daqui costuma levar 403).
- Imprensa local na língua do país, site e redes oficiais do clube (escalação, entrevista do técnico), federação (árbitro).
- Clima: python3 ferramentas/clima.py --lat <lat> --lon <lon> --data <AAAA-MM-DD> --hora <HH:MM>.
Use WebSearch e WebFetch (carregue com ToolSearch se não estiverem disponíveis) e curl pelo Bash. Site de palpite só serve de contraprova, nunca de número.
Nunca invente: cada número com fonte, recorte e data; sem fonte = N/D.`

// ---------------------------------------------------------------------------
// Candidatos: do dossiê (Sofascore) ou da descoberta na web
// ---------------------------------------------------------------------------

const linhaDe = c => {
  const k = c.chave && c.chave[1] != null ? Number(c.chave[1]) : NaN
  if (!Number.isNaN(k)) return k
  const m = String(c.mercado || '').match(/(\d+[.,]5)/)
  return m ? Number(m[1].replace(',', '.')) : null
}

const DESC = {
  type: 'object',
  properties: {
    candidatos: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          jogo: { type: 'string', description: 'Mandante x Visitante' }, competicao: { type: 'string' }, pais: { type: 'string' },
          hora: { type: 'string', description: 'HH:MM de Brasília' }, linha: { type: 'number', description: '2.5, 3.5 ou 4.5' },
          id_365: int, por_que: { type: 'string', description: 'números do perfil de under, cada um com fonte e recorte' },
          odd_under: num, odd_over: num, fontes: { type: 'array', items: { type: 'string' } },
        },
        required: ['jogo', 'competicao', 'hora', 'linha', 'por_que', 'fontes'],
      },
    },
    jogos_vistos: { type: 'integer' }, fontes_usadas: { type: 'array', items: { type: 'string' } }, lacunas: { type: 'string' },
  },
  required: ['candidatos', 'jogos_vistos', 'fontes_usadas', 'lacunas'],
}

let todos
if (web) {
  phase('Descoberta')
  const maxDesc = D.max_descoberta || 8
  log(`Modo web (sem Sofascore): descobridor procura até ${maxDesc} unders em ${D.data}`)
  const desc = await roda(`Você é o DESCOBRIDOR do Método Under do Daniel (português do Brasil). O Sofascore está fora do ar.
Ache, para ${D.data} (horário de Brasília), os jogos de ligas PROFISSIONAIS que ainda não começaram com o perfil mais forte de "menos de X.5 gols".
1) Liste os jogos do dia pela API do 365Scores (endereço abaixo) e, se precisar, por FlashScore/FotMob.
2) Para os candidatos, levante na condição do jogo (mandante em casa, visitante fora): gols marcados e sofridos por jogo, % de jogos abaixo da linha e a média de gols da liga.
   Use SoccerStats (curl), FootyStats e FBref (WebFetch/busca) e Understat para xG.
3) Fique com até ${maxDesc}, os mais fortes: os dois times com % alta de under na linha, liga de poucos gols, cauda limpa, sem favorito goleador. Prefira as linhas 2.5 e 3.5.
4) Traga a odd do under e do over dessa linha (Betexplorer/Oddsportal/365Scores) quando achar.
${FONTES}`, { label: 'descobridor', phase: 'Descoberta', schema: DESC })
  todos = ((desc && desc.candidatos) || []).map((x, i) => {
    const pm = x.odd_under && x.odd_over ? (1 / x.odd_under) / (1 / x.odd_under + 1 / x.odd_over) : null
    return {
      n: i + 1, id: x.id_365 || null, jogo: x.jogo, competicao: `${x.pais ? x.pais + ' · ' : ''}${x.competicao}`, hora: x.hora,
      mercado: `Menos de ${x.linha} gols`, chave: ['Match goals', String(x.linha), 'Under'], status: 'vivo', p_modelo: null,
      odd_agora: x.odd_under || null, prob_mercado_sem_margem: pm, web: { por_que: x.por_que, fontes: x.fontes },
    }
  })
  if (desc) log(`Descoberta: ${desc.jogos_vistos} jogos vistos, ${todos.length} candidatos (${(desc.fontes_usadas || []).join(', ')})`)
} else {
  todos = D.candidatos || []
}

let alvo = todos.filter(c => c.status === 'vivo')
const caidos = todos.filter(c => c.status !== 'vivo')
if (caidos.length) log(`Caíram na reavaliação: ${caidos.map(c => `${c.jogo} — ${c.motivo_queda}`).join(' | ')}`)
const fora = alvo.slice(maxPesquisa)
alvo = alvo.slice(0, maxPesquisa)
if (fora.length) log(`Sem pesquisa (teto de ${maxPesquisa}): ${fora.map(c => c.jogo).join(' | ')}`)
if (!alvo.length) return { data: D.data, modo: web ? 'web' : 'sofascore', agentes, resultados: [], top: [], caidos: caidos.map(c => ({ jogo: c.jogo, motivo: c.motivo_queda })) }

// ---------------------------------------------------------------------------
// Esquemas
// ---------------------------------------------------------------------------

const EST = {
  type: 'object',
  properties: {
    medias: {
      type: 'object',
      properties: {
        fonte: { type: 'string' }, recorte: { type: 'string' },
        mandante_marcados_casa: num, mandante_sofridos_casa: num, visitante_marcados_fora: num, visitante_sofridos_fora: num,
        liga_media_mandante: num, liga_media_visitante: num,
      },
      required: ['fonte', 'recorte', 'mandante_marcados_casa', 'mandante_sofridos_casa', 'visitante_marcados_fora', 'visitante_sofridos_fora', 'liga_media_mandante', 'liga_media_visitante'],
    },
    xg: { type: 'string', description: 'xG pró e contra na condição, com fonte; N/D se a liga não tiver' },
    under_pct_linha: { type: 'string', description: '% de jogos abaixo da LINHA do pick: mandante em casa, visitante fora e liga, com fonte' },
    comando_prob: { type: 'string', description: 'o comando prob.py gols exato que você rodou' },
    p_independente: { ...num, description: 'prob. do under na linha do pick saída do prob.py (0 a 1)' },
    gols_esperados_total: { ...num, description: 'soma dos λ do prob.py' },
    cauda_estouros: { ...int, description: 'nos últimos 7 oficiais de cada time, quantos passaram da linha (somando os dois)' },
    cauda_jogos: int,
    cauda_detalhe: { type: 'string' },
    h2h_estouros: { ...int, description: 'quantos dos últimos 5 confrontos passaram da LINHA exata' },
    h2h_jogos: int,
    h2h_detalhe: { type: 'string' },
    divergencias: { type: 'array', items: { type: 'string' }, description: 'número X na fonte A x na fonte B' },
    fontes_independentes: { type: 'integer', description: 'quantas fontes diferentes do Sofascore você usou de fato' },
    derruba: { type: 'boolean', description: 'true se os números independentes desmentem o under (ex.: % de under baixa nas duas condições)' },
    motivo: { type: 'string' },
    fontes: { type: 'array', items: { type: 'string' } },
    lacunas: { type: 'string' },
  },
  required: ['medias', 'xg', 'under_pct_linha', 'comando_prob', 'p_independente', 'gols_esperados_total', 'cauda_estouros', 'cauda_jogos',
    'cauda_detalhe', 'h2h_estouros', 'h2h_jogos', 'h2h_detalhe', 'divergencias', 'fontes_independentes', 'derruba', 'motivo', 'fontes', 'lacunas'],
}

const CTX = {
  type: 'object',
  properties: {
    data_hora_local: { type: 'string', description: 'data, hora (Brasília) e estádio confirmados em 2 fontes' },
    escalacao: { type: 'string', description: 'oficial ou provável dos dois, com fonte e data' },
    desfalques_ataque: { type: 'array', items: { type: 'string' }, description: 'atacantes/criadores FORA ou em dúvida (ajudam o under), com gols e fonte' },
    desfalques_defesa: { type: 'array', items: { type: 'string' }, description: 'goleiro/zagueiros/volantes titulares FORA (contra o under), com fonte' },
    defesa_titular_fora_confirmado: { type: 'boolean', description: 'goleiro ou zagueiro titular CONFIRMADO fora' },
    estilo: { type: 'string', description: 'bloco baixo, posse, contra-ataque, técnico defensivo/ofensivo, troca recente' },
    motivacao: { type: 'string', description: 'o empate serve? jogo decisivo? alguém PRECISA vencer?' },
    jogo_aberto: { type: 'boolean', description: 'true se algo abre o jogo: time que precisa vencer com ataque forte, técnico novo ofensivo, favorito goleador, clássico aberto' },
    arbitro: { type: 'string', description: 'pênaltis e expulsões por jogo, com fonte; N/D' },
    clima_gramado: { type: 'string', description: 'chuva, vento, gramado (informativo)' },
    calendario: { type: 'string', description: 'jogo no meio da semana, rodízio, cansaço' },
    mercado: { type: 'string', description: 'odd do under abertura → agora em pelo menos 2 casas (Betexplorer, Oddsportal, Sofascore, 365Scores)' },
    odd_under_subindo: { type: 'boolean', description: 'true se a odd do under subiu mais de 3% desde a abertura' },
    fatores_a_favor: { type: 'array', items: { type: 'string' } },
    fatores_contra: { type: 'array', items: { type: 'string' } },
    ajuste_pp: { type: 'number', minimum: -5, maximum: 5, description: 'p.p. na prob. do UNDER (+ = mais chance), só com fato que os números não medem' },
    motivo_ajuste: { type: 'string' },
    derruba_pick: { type: 'boolean', description: 'true só com fato forte e confirmado (jogo adiado, time reserva no gol e na zaga, etc.)' },
    fontes: { type: 'array', items: { type: 'string' } },
    lacunas: { type: 'string' },
  },
  required: ['data_hora_local', 'escalacao', 'desfalques_ataque', 'desfalques_defesa', 'defesa_titular_fora_confirmado', 'estilo', 'motivacao',
    'jogo_aberto', 'arbitro', 'clima_gramado', 'calendario', 'mercado', 'odd_under_subindo', 'fatores_a_favor', 'fatores_contra',
    'ajuste_pp', 'motivo_ajuste', 'derruba_pick', 'fontes', 'lacunas'],
}

const CET = {
  type: 'object',
  properties: {
    refutado: { type: 'boolean', description: 'true se achou motivo sólido e com fonte para NÃO ir no under' },
    motivo: { type: 'string' },
    ajuste_extra_pp: { type: 'number', minimum: -5, maximum: 5, description: 'correção ADICIONAL ao ajuste do pesquisador (0 se concorda)' },
    checagens: {
      type: 'array',
      items: { type: 'object', properties: { afirmacao: { type: 'string' }, confere: { type: 'boolean' }, fonte: { type: 'string' } }, required: ['afirmacao', 'confere', 'fonte'] },
    },
    confianca: { type: 'string', enum: ['alta', 'media', 'baixa'] },
    licao: { type: 'string', description: 'lição NOVA e geral sobre under (não repita docs/licoes.md); "" se nenhuma' },
  },
  required: ['refutado', 'motivo', 'ajuste_extra_pp', 'checagens', 'confianca', 'licao'],
}

// ---------------------------------------------------------------------------
// Prompts
// ---------------------------------------------------------------------------

const resumo = c => JSON.stringify({
  jogo: c.jogo, competicao: c.competicao, data: D.data, hora_brasilia: c.hora, id_sofascore: web ? null : c.id, id_365: web ? c.id : null,
  local: c.local, arbitro: c.arbitro, tecnicos: c.tecnicos, pick: c.mercado, linha: linhaDe(c), prob_modelo_sofascore: pct(c.p_modelo),
  prob_mercado_sem_margem: pct(c.prob_mercado_sem_margem), odd_agora: c.odd_agora, odds_movimento: c.odds_movimento,
  gols_esperados_modelo: c.gols_esperados, variantes: c.variantes, frequencia_under_nas_amostras: c.frequencia_amostras,
  requisitos_under: c.under, desfalques_sofascore: c.desfalques, artilheiros_liga: c.artilheiros, forma: c.forma,
  escalacao_confirmada: c.escalacao_confirmada, chuva: c.chuva, descoberta_web: c.web,
})

const promptEst = c => `Você é o ESTATÍSTICO INDEPENDENTE do Método Under do Daniel (português do Brasil). Pick: ${c.mercado} em ${c.jogo} (${c.competicao}), ${c.hora} de ${D.data} (Brasília).
O que já se sabe: ${resumo(c)}
Sua tarefa é refazer a conta SEM depender do Sofascore, para conferir ou desmentir o modelo:
1) Médias na condição do jogo (mandante em casa, visitante fora) na temporada atual: gols marcados e sofridos por jogo e a média de gols de mandantes e visitantes da liga. Fonte principal fora do Sofascore (SoccerStats, FBref, FootyStats, 365Scores); confira com uma 2ª.
2) Rode: python3 ferramentas/prob.py gols --casa-marcados A --casa-sofridos B --fora-marcados C --fora-sofridos D --liga-mandante E --liga-visitante F --mercados under${linhaDe(c)} --json
   (com xG na condição de uma fonte confiável, acrescente --xg-casa e --xg-fora). Copie o comando em comando_prob e a prob. do under em p_independente.
3) % de jogos abaixo da LINHA ${linhaDe(c)}: mandante em casa, visitante fora e liga.
4) Cauda: nos últimos 7 oficiais de cada time (todas as competições), quantos passaram de ${linhaDe(c)} gols. Procure goleadas recentes.
5) H2H: totais dos últimos 5 confrontos contados na LINHA exata (lição 34).
6) Liste toda divergência entre fontes (ex.: "mandante sofre 0,9 em casa no SoccerStats x 1,3 no Sofascore").
derruba = true só se os números independentes desmentem o under (ex.: os dois times estouram a linha com frequência).
Antes, leia docs/licoes.md (sobretudo 1, 3, 7, 17, 32, 33, 34, 39, 47 a 50).
${FONTES}`

const promptCtx = (c, e) => `Você é o PESQUISADOR DE CONTEXTO do Método Under do Daniel (português do Brasil). Pick: ${c.mercado} em ${c.jogo} (${c.competicao}), ${c.hora} de ${D.data} (Brasília).
O que já se sabe: ${resumo(c)}
Estatístico independente: ${JSON.stringify(e || 'não rodou')}
Os números já estão em mãos: não refaça estatística. Pesquise A FUNDO, em todas as fontes da internet (imprensa local na língua do país, site e redes oficiais dos clubes, Transfermarkt, federação, casas de aposta), o que pode abrir ou fechar o jogo HOJE:
1) Data, hora e estádio em 2 fontes.
2) Escalação provável e desfalques: atacantes e criadores fora (ajudam o under) x goleiro e zagueiros titulares fora (contra).
3) Estilo e técnico: bloco baixo, posse, contra-ataque, técnico novo.
4) Motivação: o empate serve? alguém precisa vencer (jogo aberto no fim)? clássico?
5) Árbitro (pênaltis e expulsões por jogo), clima e gramado (informativo), calendário e rodízio.
6) Mercado: odd do under abertura → agora em pelo menos 2 casas; o que o mercado pode saber.
7) Ajuste em p.p. na prob. do UNDER (−5 a +5), só com fato que os números não medem. Na dúvida, 0. Se sua leitura honesta é menor que a do modelo, o ajuste é NEGATIVO (lição 56).
Antes, leia docs/licoes.md.
${FONTES}`

const promptCet = (c, e, p) => `Você é o CÉTICO do Método Under do Daniel. Tente DERRUBAR "${c.mercado}" em ${c.jogo} (${c.competicao}), ${c.hora} de ${D.data}.
Dados: ${resumo(c)}
Estatístico independente: ${JSON.stringify(e || 'não rodou')}
Pesquisador de contexto: ${JSON.stringify(p)}
Leia docs/licoes.md antes. Confira em fonte DIFERENTE das que eles usaram as 2 ou 3 afirmações que mais pesam (médias, desfalques, escalação, H2H na linha).
Procure ativamente o que faz o under perder: favorito goleador, defesa titular desfalcada, time que precisa vencer, árbitro de pênalti ou expulsão, estilo aberto, amostra velha, fontes que divergem, odd do under subindo.
ajuste_extra_pp é ADICIONAL ao do pesquisador (total final limitado a ±5). refutado = true só com motivo sólido e com fonte. Se o caso ensinar algo novo e geral sobre under, escreva em "licao".
${FONTES}`

// ---------------------------------------------------------------------------
// Veredito (código: probabilidade, selo elite e ranking)
// ---------------------------------------------------------------------------

const ev = (p, odd) => p * (odd - 1) - (1 - p)
const oddMin = (p, evMin) => Math.ceil((1 + (evMin + 1 - p) / p) * 100 - 1e-9) / 100
const limita = x => Math.max(-5, Math.min(5, x))
const base = (c, e) => {
  const ps = [c.p_modelo, e && e.p_independente].filter(x => typeof x === 'number' && x > 0 && x <= 1)
  return ps.length ? Math.min(...ps) : null   // duas contas: vale a menor
}

function veredito(c, e, p, k) {
  const motivos = [], avisos = [], elite = []
  const linha = linhaDe(c)
  const pb = base(c, e)
  const ajuste = limita((p ? p.ajuste_pp : 0) + (k ? k.ajuste_extra_pp : 0))
  const pf = pb == null ? null : pb + ajuste / 100
  const odd = c.odd_agora
  const evf = odd && pf != null ? ev(pf, odd) : null
  const gap = c.prob_mercado_sem_margem != null && pf != null ? pf - c.prob_mercado_sem_margem : null
  const diverg = c.p_modelo != null && e && e.p_independente != null ? Math.abs(c.p_modelo - e.p_independente) : null
  const golsEsp = (e && e.gols_esperados_total) || (c.gols_esperados ? c.gols_esperados[0] + c.gols_esperados[1] : null)
  const folga = linha != null && golsEsp != null ? linha - golsEsp : null
  const caudaSofa = c.under && c.under.cauda ? (c.under.cauda.casa.acima || 0) + (c.under.cauda.fora.acima || 0) : null
  const cauda = e && e.cauda_estouros != null ? Math.max(e.cauda_estouros, caudaSofa || 0) : caudaSofa
  const fontesInd = e ? e.fontes_independentes || 0 : 0

  if (pb == null) motivos.push('sem probabilidade (nem modelo nem conta independente)')
  if (e && e.derruba) motivos.push(`estatística independente derrubou: ${e.motivo}`)
  if (!p) motivos.push('sem pesquisa de contexto')
  if (p && p.derruba_pick) motivos.push('pesquisa derrubou o pick')
  if (k && k.refutado) motivos.push(`cético refutou: ${k.motivo}`)
  if (pf != null && pf < crit.prob_minima) motivos.push(`chance ${pct(pf)} < ${pct(crit.prob_minima)}`)
  if (evf == null || evf < crit.ev_minimo) avisos.push(`EV ${evf == null ? 'N/D' : pct(evf)} < ${pct(crit.ev_minimo)} (só registro)`)
  if (gap != null && gap > regra8) avisos.push(`regra 8: ${(100 * gap).toFixed(1)} p.p. acima do mercado`)
  if (diverg != null && diverg > 0.1) avisos.push(`fontes divergem: modelo ${pct(c.p_modelo)} x independente ${pct(e.p_independente)}`)

  // selo elite (docs/metodo-under.md, seção 5)
  if (pf == null || pf < eliteMin) elite.push(`chance ${pct(pf)} < ${pct(eliteMin)}`)
  if (!k) elite.push('sem cético')
  else if (k.confianca === 'baixa') elite.push('cético com confiança baixa')
  if (cauda != null && cauda > 1) elite.push(`cauda com ${cauda} estouros`)
  if (e && e.h2h_jogos >= 3 && e.h2h_estouros > 1) elite.push(`H2H: ${e.h2h_estouros} de ${e.h2h_jogos} acima da linha`)
  if (p && p.defesa_titular_fora_confirmado) elite.push('defesa titular desfalcada')
  if (p && p.jogo_aberto) elite.push('motivo de jogo aberto')
  if (p && p.odd_under_subindo) elite.push('odd do under subindo')
  if (gap != null && gap > 0.08) elite.push(`mercado ${(100 * gap).toFixed(1)} p.p. abaixo`)
  if (diverg != null && diverg > 0.1) elite.push('fontes divergem mais de 10 p.p.')
  if (usarEstatistico && fontesInd < 2) elite.push(`só ${fontesInd} fonte(s) fora do Sofascore`)
  if (motivos.length) elite.push('não passou no veredito')

  return {
    linha, p_base: pb == null ? null : +pb.toFixed(4), ajuste_pp: ajuste, p_final: pf == null ? null : +pf.toFixed(4),
    p_independente: e ? e.p_independente : null, odd_agora: odd, ev_final: evf == null ? null : +evf.toFixed(4),
    odd_minima_final: pf ? oddMin(pf, crit.ev_minimo) : null, gap_mercado_pp: gap == null ? null : +(100 * gap).toFixed(1),
    folga: folga == null ? null : +folga.toFixed(2), cauda_estouros: cauda,
    veredito_previo: motivos.length ? 'DESCARTADO' : 'PASSA', motivos, avisos,
    selo_elite: !elite.length, elite_falhas: elite, valor: evf != null && evf >= crit.ev_minimo,
  }
}

// ---------------------------------------------------------------------------
// Pipeline: estatístico → contexto → cético, parando assim que o under morre
// ---------------------------------------------------------------------------

const vivo = (c, e, p) => {
  const pb = base(c, e)
  if (pb == null) return false
  if (e && e.derruba) return false
  if (p && p.derruba_pick) return false
  return pb + (p ? p.ajuste_pp : 0) / 100 >= crit.prob_minima - 0.05
}

const res = await pipeline(
  alvo,
  c => (usarEstatistico || web)
    ? roda(promptEst(c), { label: `estatística: ${c.jogo}`, phase: 'Estatística', schema: EST }).then(e => ({ c, e }))
    : { c, e: null },
  ({ c, e }) => {
    if ((usarEstatistico || web) && !e) return { c, e, p: null, parou: 'estatístico falhou' }
    if (!vivo(c, e, null)) return { c, e, p: null, parou: 'estatística' }
    return roda(promptCtx(c, e), { label: `contexto: ${c.jogo}`, phase: 'Contexto', schema: CTX }).then(p => ({ c, e, p }))
  },
  st => {
    if (st.parou) return { ...st, k: null }
    if (!st.p) return { ...st, k: null, parou: 'contexto falhou' }
    if (!vivo(st.c, st.e, st.p)) return { ...st, k: null, parou: 'contexto' }
    return roda(promptCet(st.c, st.e, st.p), { label: `cético: ${st.c.jogo}`, phase: 'Cético', schema: CET }).then(k => ({ ...st, k }))
  },
)

const resultados = res.filter(Boolean).map(({ c, e, p, k, parou }) => ({
  n: c.n, id: c.id, jogo: c.jogo, competicao: c.competicao, hora: c.hora, mercado: c.mercado, chave: c.chave,
  p_modelo: c.p_modelo, prob_mercado: c.prob_mercado_sem_margem, under: c.under, odds_movimento: c.odds_movimento,
  ...veredito(c, e, p, k), parou_em: parou || null,
  status: parou ? `parou: ${parou}` : (k ? 'ok' : 'cético falhou'), estatistica: e, pesquisa: p, cetico: k,
}))
const falhas = resultados.filter(r => /falhou/.test(r.status))
if (falhas.length) log(`Agentes falharam em: ${falhas.map(r => `${r.jogo} (${r.status})`).join(' | ')} — retome com resumeFromRunId`)

// ranking: chance → folga → cauda → EV; o top são os 3 primeiros com selo elite
const ordem = (a, b) => (b.p_final ?? 0) - (a.p_final ?? 0) || (b.folga ?? -9) - (a.folga ?? -9) ||
  (a.cauda_estouros ?? 9) - (b.cauda_estouros ?? 9) || (b.ev_final ?? -9) - (a.ev_final ?? -9)
const passam = resultados.filter(r => r.veredito_previo === 'PASSA').sort(ordem)
const top = passam.filter(r => r.selo_elite).slice(0, 3)
log(`${passam.length} passam (≥ ${pct(crit.prob_minima)}); ${top.length} com selo elite. Agentes: ${agentes}`)

return {
  data: D.data, modo: web ? 'web' : 'sofascore', agentes,
  top: top.map(r => ({ jogo: r.jogo, hora: r.hora, competicao: r.competicao, mercado: r.mercado, p_final: r.p_final, folga: r.folga, valor: r.valor })),
  passam: passam.map(r => r.jogo), resultados,
  sem_pesquisa: fora.map(c => c.jogo), caidos: caidos.map(c => ({ jogo: c.jogo, motivo: c.motivo_queda })),
}
