export const meta = {
  name: 'under',
  description: 'Especialista em under: 1 pesquisador (checklist de under) e 1 cético por candidato do under.py',
  whenToUse: 'Depois de `python3 ferramentas/under.py` + `python3 ferramentas/dossie.py --sufixo under --json`: passe o JSON do dossiê como args. Usado pelo /under.',
  phases: [
    { title: 'Pesquisa', detail: 'desfalques no ataque e na defesa, estilo, motivação, H2H, clima, árbitro, cauda, mercado' },
    { title: 'Cético', detail: 'tenta derrubar o under e confere as afirmações-chave' },
  ],
}

// args = saída do dossie.py --sufixo under --json (cada candidato traz o bloco `under` do under.py)
const D = args || {}
const crit = D.criterios || { prob_minima: 0.7, ev_minimo: 0.03 }
const regra8 = D.regra8_pp || 0.1
const conf = D.aprofundar || {}
const modelo = conf.modelo_agentes || undefined
const maxPesquisa = (D.under && D.under.max_pesquisa) ?? 6
let alvo = (D.candidatos || []).filter(c => c.status === 'vivo')
const caidos = (D.candidatos || []).filter(c => c.status !== 'vivo')
if (caidos.length) log(`Caíram na reavaliação: ${caidos.map(c => `${c.jogo} — ${c.motivo_queda}`).join(' | ')}`)
const fora = alvo.slice(maxPesquisa)
alvo = alvo.slice(0, maxPesquisa)
if (fora.length) log(`Sem pesquisa (teto de ${maxPesquisa}): ${fora.map(c => c.jogo).join(' | ')}`)
if (!alvo.length) return { resultados: [], agentes: 0, caidos: caidos.map(c => ({ jogo: c.jogo, motivo: c.motivo_queda })) }

const PESQ = {
  type: 'object',
  properties: {
    data_hora_local: { type: 'string', description: 'data, hora (Brasília) e estádio confirmados numa 2ª fonte' },
    escalacao: { type: 'string', description: 'oficial ou provável dos dois, com fonte e data' },
    desfalques_ataque: { type: 'array', items: { type: 'string' }, description: 'atacantes/criadores FORA ou em dúvida (ajudam o under), com gols na temporada e fonte' },
    desfalques_defesa: { type: 'array', items: { type: 'string' }, description: 'goleiro/zagueiros/volantes titulares FORA (contra o under), com fonte' },
    estilo: { type: 'string', description: 'como cada time joga: bloco baixo, posse, contra-ataque, técnico defensivo; troca de técnico recente' },
    motivacao: { type: 'string', description: 'o empate serve? jogo decisivo (cautela) ou alguém PRECISA vencer (jogo aberto no fim)? clássico?' },
    h2h_totais: { type: 'string', description: 'totais de gols dos últimos 5 a 10 confrontos, comparados com a LINHA do pick' },
    cauda: { type: 'string', description: 'nos últimos 7 oficiais (todas as competições), quantas vezes cada time passou da linha; goleadas recentes' },
    clima_gramado: { type: 'string', description: 'chuva forte, vento, frio, gramado pesado/sintético, altitude (informativo)' },
    arbitro: { type: 'string', description: 'pênaltis e expulsões por jogo do árbitro (expulsão abre o jogo); N/D se não achar' },
    calendario: { type: 'string', description: 'jogo no meio da semana antes/depois, rodízio, cansaço' },
    mercado: { type: 'string', description: 'movimento da linha de gols (odd do under caindo = dinheiro no under) e o que o mercado pode saber' },
    fatores_a_favor: { type: 'array', items: { type: 'string' } },
    fatores_contra: { type: 'array', items: { type: 'string' } },
    ajuste_pp: { type: 'number', minimum: -5, maximum: 5, description: 'p.p. na prob. do UNDER (+ = mais chance de bater), só com fato que o modelo não mede' },
    motivo_ajuste: { type: 'string' },
    derruba_pick: { type: 'boolean', description: 'true só com fato forte e confirmado (ex.: jogo adiado, time reserva)' },
    fontes: { type: 'array', items: { type: 'string' } },
    lacunas: { type: 'string' },
  },
  required: ['data_hora_local', 'escalacao', 'desfalques_ataque', 'desfalques_defesa', 'estilo', 'motivacao', 'h2h_totais', 'cauda',
    'clima_gramado', 'arbitro', 'calendario', 'mercado', 'fatores_a_favor', 'fatores_contra', 'ajuste_pp', 'motivo_ajuste', 'derruba_pick', 'fontes', 'lacunas'],
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

const pct = x => (x == null ? 'N/D' : `${(100 * x).toFixed(1)}%`)
const resumo = c => JSON.stringify({
  jogo: c.jogo, competicao: c.competicao, data: D.data, hora_brasilia: c.hora, min_para_inicio: c.min_para_inicio,
  local: c.local, arbitro: c.arbitro, tecnicos: c.tecnicos, pick: c.mercado, prob_modelo: pct(c.p_modelo),
  prob_mercado_sem_margem: pct(c.prob_mercado_sem_margem), odd_agora: c.odd_agora, odds_movimento: c.odds_movimento,
  gols_esperados_modelo: c.gols_esperados, variantes: c.variantes, frequencia_under_nas_amostras: c.frequencia_amostras,
  requisitos_under: c.under, desfalques_sofascore: c.desfalques, artilheiros_liga: c.artilheiros, gols_liga: c.gols_liga,
  forma: c.forma, escalacao_confirmada: c.escalacao_confirmada, chuva: c.chuva,
})

const SOFA = `Sofascore pela API pública, com o cliente do repositório (rode da raiz):
python3 -c "import sys,json;sys.path.insert(0,'ferramentas');import varredura as v;api=v.Sofascore(None,'${D.data}');print(json.dumps(api.get('CAMINHO',cache=None),ensure_ascii=False)[:8000])"
Caminhos úteis: event/{id} ; event/{id}/lineups ; event/{id}/h2h ; event/{id}/odds/1/all ; event/{customId}/h2h/events ; team/{tid}/events/last/0 ; event/{eid}/statistics ; event/{eid}/incidents.`

const promptPesquisa = c => `Você é o pesquisador ESPECIALISTA EM UNDER do Daniel (português do Brasil). Pick: ${c.mercado} em ${c.jogo} (${c.competicao}), ${c.hora} de ${D.data} (Brasília), id Sofascore ${c.id}.
Dados do modelo e dos requisitos de under (Sofascore, já em mãos): ${resumo(c)}
ANTES, leia docs/licoes.md (sobretudo 1, 3, 7, 11, 17, 32, 33 e 34) e confira as que se aplicam.
Pesquise A FUNDO (Sofascore primeiro, depois imprensa local; WebSearch/WebFetch, carregue com ToolSearch se preciso) o checklist do under:
1) Data, hora e estádio numa 2ª fonte.
2) Escalação provável e DESFALQUES: atacantes e criadores fora (ajudam o under) x goleiro e zagueiros titulares fora (contra).
3) Estilo e técnico: bloco baixo, posse, contra-ataque; técnico novo.
4) Motivação: o empate serve? alguém precisa vencer (jogo aberto no fim)? clássico?
5) H2H: totais dos últimos 5 a 10 confrontos comparados com a LINHA exata do pick (lição 34: "2+ gols" não é over 2.5).
6) Cauda: confirme a contagem do under.py (últimos 7 oficiais de cada time acima da linha) e procure goleadas recentes.
7) Clima e gramado (informativo; o Daniel não exclui por chuva), árbitro (pênaltis/expulsões), calendário e rodízio.
8) Mercado: movimento da odd do under (abertura → agora) e o que o mercado pode saber.
9) Ajuste em p.p. na prob. do UNDER (−5 a +5), só com fato que o modelo não mede. Na dúvida, 0.
   O ajuste é somado à prob. DO MODELO: se a sua leitura honesta é menor que a do modelo, o ajuste é NEGATIVO até chegar nela (lição 56).
Nunca invente: cada fato com fonte e data; sem fonte = N/D.
${SOFA}`

const promptCetico = (c, p) => `Você é o CÉTICO do especialista em under. Tente DERRUBAR "${c.mercado}" em ${c.jogo} (${c.competicao}), ${c.hora} de ${D.data}, id Sofascore ${c.id}.
Dados: ${resumo(c)}
Pesquisador: ${JSON.stringify(p)}
Leia docs/licoes.md antes. Confira em fonte independente as 2 ou 3 afirmações que mais pesam (desfalques, escalação, H2H na linha certa).
Procure ativamente o que faz o under perder: favorito goleador (cauda), defesa titular desfalcada, time que precisa vencer, árbitro de pênalti/expulsão, jogo aberto no estilo, modelo apoiado em amostra velha, mercado indo contra (odd do under subindo).
ajuste_extra_pp é ADICIONAL ao do pesquisador (total final limitado a ±5). refutado = true só com motivo sólido e com fonte. Se o caso ensinar algo novo e geral sobre under, escreva em "licao".
${SOFA}`

const ev = (p, odd, dev) => p * (odd - 1) - (1 - p - dev)
const oddMin = (p, evMin, dev) => Math.ceil((1 + (evMin + 1 - p - dev) / p) * 100 - 1e-9) / 100
const limita = x => Math.max(-5, Math.min(5, x))

function veredito(c, p, k) {
  const motivos = []
  const ajuste = limita((p ? p.ajuste_pp : 0) + (k ? k.ajuste_extra_pp : 0))
  const pf = c.p_modelo + ajuste / 100
  const odd = c.odd_agora
  const evf = odd ? ev(pf, odd, 0) : null
  const gap = c.prob_mercado_sem_margem != null ? pf - c.prob_mercado_sem_margem : null
  if (!p) motivos.push('pesquisa falhou')
  if (p && p.derruba_pick) motivos.push('pesquisa derrubou o pick')
  if (k && k.refutado) motivos.push(`cético refutou: ${k.motivo}`)
  if (pf < crit.prob_minima) motivos.push(`prob. ${pct(pf)} < ${pct(crit.prob_minima)}`)
  if (evf == null || evf < crit.ev_minimo) motivos.push(`EV ${evf == null ? 'N/D' : pct(evf)} < ${pct(crit.ev_minimo)}`)
  if (gap != null && gap > regra8) motivos.push(`regra 8: ${(100 * gap).toFixed(1)} p.p. acima do mercado`)
  return {
    ajuste_pp: ajuste, p_final: +pf.toFixed(4), odd_agora: odd, ev_final: evf == null ? null : +evf.toFixed(4),
    odd_minima_final: oddMin(pf, crit.ev_minimo, 0), gap_mercado_pp: gap == null ? null : +(100 * gap).toFixed(1),
    veredito_previo: motivos.length ? 'DESCARTADO' : 'PASSA', motivos,
  }
}

const res = await pipeline(
  alvo,
  c => agent(promptPesquisa(c), { label: `pesq: ${c.jogo}`, phase: 'Pesquisa', schema: PESQ, model: modelo }),
  (p, c) => !p ? { c, p: null, k: null } : agent(promptCetico(c, p), { label: `cético: ${c.jogo}`, phase: 'Cético', schema: CET, model: modelo })
    .then(k => ({ c, p, k })),
)

const resultados = res.filter(Boolean).map(({ c, p, k }) => ({
  n: c.n, id: c.id, jogo: c.jogo, competicao: c.competicao, hora: c.hora, mercado: c.mercado, chave: c.chave,
  p_modelo: c.p_modelo, prob_mercado: c.prob_mercado_sem_margem, under: c.under, odds_movimento: c.odds_movimento,
  ...veredito(c, p, k), status: p && k ? 'ok' : (p ? 'cetico falhou' : 'pesquisa falhou'), pesquisa: p, cetico: k,
}))
const falhas = resultados.filter(r => r.status !== 'ok')
if (falhas.length) log(`Agentes falharam em: ${falhas.map(r => `${r.jogo} (${r.status})`).join(' | ')} — retome com resumeFromRunId`)
return { data: D.data, agentes: alvo.length * 2, resultados, sem_pesquisa: fora.map(c => c.jogo), caidos: caidos.map(c => ({ jogo: c.jogo, motivo: c.motivo_queda })) }
