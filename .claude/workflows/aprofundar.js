export const meta = {
  name: 'aprofundar',
  description: 'Pesquisa de imprensa + checagem cética dos candidatos vivos da peneira (econômico: 1 pesquisador e no máximo 1 cético por candidato)',
  whenToUse: 'Depois de `python3 ferramentas/dossie.py --json`: passe o JSON inteiro como args. Usado pelo /ouro e pelo /aprofundar.',
  phases: [
    { title: 'Pesquisa', detail: 'escalação, desfalques, contexto e o que o mercado sabe' },
    { title: 'Cético', detail: 'tenta derrubar o pick e confere as afirmações-chave' },
  ],
}

// args = saída do dossie.py --json; args.investigar_caidos = true pesquisa também os que caíram
const D = args || {}
const crit = D.criterios || { prob_minima: 0.6, ev_minimo: 0.03 }
const regra8 = D.regra8_pp || 0.1
const conf = D.aprofundar || {}
const modelo = conf.modelo_agentes || undefined
const todos = D.candidatos || []
const alvo = todos.filter(c => c.status === 'vivo' || D.investigar_caidos)
const pulados = todos.filter(c => !alvo.includes(c))
if (pulados.length) log(`Sem pesquisa (caíram na reavaliação): ${pulados.map(c => `${c.n}) ${c.jogo} — ${c.motivo_queda}`).join(' | ')}`)
for (const f of D.fora || []) log(`Fora: ${f.n}) ${f.jogo} — ${f.motivo}`)
if (!alvo.length) return { resultados: [], pulados: pulados.map(c => ({ n: c.n, jogo: c.jogo, motivo: c.motivo_queda })), agentes: 0 }

const PESQUISA = {
  type: 'object',
  properties: {
    escalacao: { type: 'string', description: 'oficial ou provável dos dois times, com fonte e data' },
    desfalques: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          time: { type: 'string' }, jogador: { type: 'string' }, posicao: { type: 'string' },
          status: { type: 'string', enum: ['CONFIRMADO', 'PROVAVEL', 'RUMOR', 'VOLTOU'] },
          titular: { type: 'boolean' }, fonte: { type: 'string' },
        },
        required: ['time', 'jogador', 'status', 'fonte'],
      },
    },
    contexto: { type: 'string', description: 'técnicos, tabela/motivação, calendário/rodízio, árbitro — no máximo 6 linhas, com fonte' },
    fatores_a_favor: { type: 'array', items: { type: 'string' } },
    fatores_contra: { type: 'array', items: { type: 'string' } },
    explica_mercado: { type: 'string', description: 'o que explica o movimento das odds / a diferença modelo x mercado, ou N/D' },
    ajuste_pp: { type: 'number', minimum: -5, maximum: 5, description: 'pontos percentuais na prob. DO PICK (+ = mais chance de bater)' },
    motivo_ajuste: { type: 'string' },
    derruba_pick: { type: 'boolean', description: 'true só com fato forte e confirmado que mata a tese' },
    fontes: { type: 'array', items: { type: 'string' } },
    lacunas: { type: 'string' },
  },
  required: ['escalacao', 'desfalques', 'contexto', 'fatores_a_favor', 'fatores_contra', 'explica_mercado',
    'ajuste_pp', 'motivo_ajuste', 'derruba_pick', 'fontes', 'lacunas'],
}

const CETICO = {
  type: 'object',
  properties: {
    refutado: { type: 'boolean', description: 'true se achou motivo sólido e com fonte para NÃO entrar' },
    motivo: { type: 'string' },
    ajuste_extra_pp: { type: 'number', minimum: -5, maximum: 5, description: 'correção ADICIONAL ao ajuste do pesquisador (0 se concorda)' },
    checagens: {
      type: 'array',
      items: {
        type: 'object',
        properties: { afirmacao: { type: 'string' }, confere: { type: 'boolean' }, fonte: { type: 'string' } },
        required: ['afirmacao', 'confere', 'fonte'],
      },
    },
    confianca: { type: 'string', enum: ['alta', 'media', 'baixa'] },
  },
  required: ['refutado', 'motivo', 'ajuste_extra_pp', 'checagens', 'confianca'],
}

const pct = x => (x == null ? 'N/D' : `${(100 * x).toFixed(1)}%`)
const resumo = c => JSON.stringify({
  jogo: c.jogo, competicao: c.competicao, data: D.data, hora_brasilia: c.hora, min_para_inicio: c.min_para_inicio,
  local: c.local, arbitro: c.arbitro, tecnicos: c.tecnicos, pick: c.mercado, status: c.status, motivo_queda: c.motivo_queda,
  prob_modelo: pct(c.p_modelo), prob_mercado_sem_margem: pct(c.prob_mercado_sem_margem), odd_agora: c.odd_agora,
  odds_movimento: c.odds_movimento, gols_esperados_modelo: c.gols_esperados, variantes: c.variantes,
  frequencia_nas_amostras: c.frequencia_amostras, desfalques_sofascore: c.desfalques, artilheiros_liga: c.artilheiros,
  gols_liga: c.gols_liga, forma: c.forma, escalacao_confirmada: c.escalacao_confirmada, chuva: c.chuva,
})

const promptPesquisa = c => `Você é o pesquisador de imprensa do /aprofundar (apostas do Daniel, português do Brasil).
Jogo e pick (dados do Sofascore e do modelo JÁ EM MÃOS, não pesquise estatística):
${resumo(c)}

ANTES de pesquisar, leia docs/licoes.md (lições de casos anteriores) e confira as que se aplicam a este pick.
Pesquise na imprensa local/esportiva confiável (use WebSearch e WebFetch; carregue com ToolSearch se não estiverem disponíveis):
1. Escalação oficial ou provável dos dois times.
2. Desfalques: confirme os do Sofascore (priorize quem tem gols na liga ou é titular) e ache outros (suspensões, convocações, dúvidas). Status CONFIRMADO / PROVAVEL / RUMOR / VOLTOU.
3. Técnicos (troca recente? pressão?), tabela e motivação, calendário/rodízio (copa no meio da semana, data FIFA), árbitro.
4. O que o mercado pode saber: explique o movimento das odds (abertura → agora) ou a diferença modelo x mercado.
5. Ajuste em p.p. na probabilidade DO PICK (−5 a +5; + = mais chance de o pick bater), só com motivo concreto e sem contar de novo o que o modelo já mede (forma e médias). Na dúvida, 0.

Economia: no máximo ~8 buscas/páginas; pare quando os itens estiverem respondidos. Prefira matérias de ontem e de hoje.
Regras: nunca invente; cada fato com fonte e data; sem fonte = N/D. derruba_pick = true só com fato forte e confirmado (ex.: time reserva confirmado, jogo adiado).`

const promptCetico = (c, p) => `Você é o CÉTICO do /aprofundar. Seu trabalho é tentar DERRUBAR este pick antes de o Daniel apostar.
Jogo e pick:
${resumo(c)}

O pesquisador trouxe:
${JSON.stringify(p)}

Leia docs/licoes.md antes (lições de casos anteriores: data e mando em 2ª fonte, regressão pelo xG, amostra recente, liga amadora).
Faça (WebSearch/WebFetch; carregue com ToolSearch se preciso):
1. Confira em fonte independente as 2 ou 3 afirmações que mais pesam na tese (sobretudo desfalques e escalação).
2. Procure ativamente o que faria o pick perder: o que o mercado sabe, rodízio, motivação, estilo de jogo, clima/gramado, árbitro.
3. Diga se o ajuste do pesquisador tem o sinal e o tamanho certos. ajuste_extra_pp é ADICIONAL ao dele (0 se concorda; total final limitado a ±5 p.p.).

Economia: no máximo ~5 buscas/páginas. refutado = true só com motivo sólido e com fonte; sem nada sólido, refutado = false. Nunca invente.`

const ev = (p, odd, dev) => p * (odd - 1) - (1 - p - dev)
const oddMin = (p, evMin, dev) => 1 + (evMin + 1 - p - dev) / p
const limita = x => Math.max(-5, Math.min(5, x))

function veredito(c, p, k) {
  const motivos = []
  const ajuste = limita((p ? p.ajuste_pp : 0) + (k ? k.ajuste_extra_pp : 0))
  const dev = c.devolucao || 0
  const pf = c.p_modelo + ajuste / 100
  const odd = c.odd_agora
  const evf = odd ? ev(pf, odd, dev) : null
  const pCond = dev ? pf / (1 - dev) : pf
  const gap = c.prob_mercado_sem_margem != null ? pCond - c.prob_mercado_sem_margem : null
  if (c.status !== 'vivo') motivos.push(`caiu na reavaliação: ${c.motivo_queda}`)
  if (!p) motivos.push('pesquisa falhou')
  if (p && p.derruba_pick) motivos.push('pesquisa derrubou o pick')
  if (k && k.refutado) motivos.push(`cético refutou: ${k.motivo}`)
  if (pf < crit.prob_minima) motivos.push(`prob. ${pct(pf)} < ${pct(crit.prob_minima)}`)
  if (evf == null || evf < crit.ev_minimo) motivos.push(`EV ${evf == null ? 'N/D' : pct(evf)} < ${pct(crit.ev_minimo)}`)
  if (gap != null && gap > regra8) motivos.push(`regra 8: ${(100 * gap).toFixed(1)} p.p. acima do mercado`)
  return {
    ajuste_pp: ajuste, p_final: +pf.toFixed(4), odd_agora: odd, ev_final: evf == null ? null : +evf.toFixed(4),
    odd_minima_final: +oddMin(pf, crit.ev_minimo, dev).toFixed(3), gap_mercado_pp: gap == null ? null : +(100 * gap).toFixed(1),
    veredito_previo: motivos.length ? 'DESCARTADO' : 'OURO', motivos,
  }
}

let agentes = 0
const resultados = await pipeline(
  alvo,
  c => { agentes++; return agent(promptPesquisa(c), { label: `pesquisa: ${c.jogo}`, phase: 'Pesquisa', schema: PESQUISA, model: modelo, effort: 'medium' }) },
  (p, c) => {
    const previo = veredito(c, p, null)
    // cético só quando ainda pode virar ouro (com 1 p.p. de folga) — economiza agente
    // cético só quando ainda pode virar ouro (com 1 p.p. de folga) — economiza agente; args.cetico_sempre (análise
    // profunda de todos, pedido do Daniel em 20/10) roda o cético mesmo sem valor
    const vale = conf.cetico !== false && c.status === 'vivo' && p && !p.derruba_pick &&
      (D.cetico_sempre || (previo.p_final >= crit.prob_minima - 0.01 && (previo.ev_final ?? -1) >= crit.ev_minimo - 0.01))
    if (!vale) return { c, p, k: null, cetico: 'pulado' }
    agentes++
    return agent(promptCetico(c, p), { label: `cético: ${c.jogo}`, phase: 'Cético', schema: CETICO, model: modelo, effort: 'medium' })
      .then(k => ({ c, p, k, cetico: k ? 'feito' : 'falhou' }))
  },
)

return {
  data: D.data,
  agentes,
  pulados: pulados.map(c => ({ n: c.n, jogo: c.jogo, motivo: c.motivo_queda })),
  fora: D.fora || [],
  resultados: resultados.filter(Boolean).map(({ c, p, k, cetico }) => ({
    n: c.n, id: c.id, jogo: c.jogo, competicao: c.competicao, hora: c.hora, mercado: c.mercado, status: c.status,
    p_modelo: c.p_modelo, prob_mercado: c.prob_mercado_sem_margem, devolucao: c.devolucao,
    variantes: c.variantes, frequencia: c.frequencia_amostras, odds_movimento: c.odds_movimento,
    ...veredito(c, p, k), cetico_status: cetico, pesquisa: p, cetico: k,
  })),
}
