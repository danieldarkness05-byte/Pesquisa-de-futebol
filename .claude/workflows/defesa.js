export const meta = {
  name: 'defesa',
  description: 'Defesa fraca x ataque forte: 1 pesquisador (Sofascore + imprensa) e 1 cético por candidato do defesa.py',
  whenToUse: 'Depois de `python3 ferramentas/defesa.py --json`: passe o JSON inteiro como args (opcional: args.ids para escolher). Usado pelo /defesa-fraca.',
  phases: [
    { title: 'Pesquisa', detail: 'defesa do azarão, ataque do favorito, desfalques, mando, calendário' },
    { title: 'Cético', detail: 'tenta derrubar a tese e fecha o mercado e o ajuste' },
  ],
}

// args = saída de `python3 ferramentas/defesa.py --json`
const D = args || {}
const conf = D.defesa || {}
const crit = D.criterios || { prob_minima: 0.6, ev_minimo: 0.03 }
const modelo = conf.modelo_agentes || undefined
const maxPesquisa = conf.max_pesquisa ?? 4
const dia = D.data || ''
if (maxPesquisa <= 0) { log('defesa.max_pesquisa = 0: pesquisa com agentes desligada'); return { resultados: [], agentes: 0 } }
let alvo = (D.candidatos || []).filter(c => c.passa && !c.risco && !c.erro)
const ids = (Array.isArray(D.ids) ? D.ids : String(D.ids || '').split(',')).map(Number).filter(Boolean)
if (ids.length) {
  alvo = (D.candidatos || []).filter(c => ids.includes(c.id) || ids.includes(c.n))
  if (!alvo.length) { log(`Nenhum candidato com os ids/números ${ids.join(',')}`); return { resultados: [], agentes: 0, aviso: 'ids não encontrados' } }
}
const fora = alvo.slice(maxPesquisa)
alvo = alvo.slice(0, maxPesquisa)
if (fora.length) log(`Sem pesquisa (passou do teto de ${maxPesquisa}): ${fora.map(c => c.jogo).join(' | ')}`)
if (!alvo.length) return { resultados: [], agentes: 0 }

const SOFA = `Sofascore pela API pública, com o cliente do repositório (rode da raiz do repositório):
python3 -c "import sys,json;sys.path.insert(0,'ferramentas');import varredura as v;api=v.Sofascore(None,'${dia}');print(json.dumps(api.get('CAMINHO',cache=None),ensure_ascii=False)[:8000])"
Caminhos úteis: event/{id} (venue, árbitro) ; event/{id}/lineups (confirmed, missingPlayers) ; event/{id}/pregame-form ; event/{id}/h2h ; team/{tid}/events/last/0 ; team/{tid}/events/next/0 ; event/{eid}/statistics ; event/{eid}/incidents ; team/{tid}/unique-tournament/{ut}/season/{sid}/statistics/overall ; team/{tid}/unique-tournament/{ut}/season/{sid}/top-players/overall ; unique-tournament/{ut}/season/{sid}/standings/total|home|away.`

const LICOES = `ANTES de pesquisar, leia docs/licoes.md (lições de casos anteriores) e confira cada uma que se aplica a este jogo.`

const PESQ = {
  type: 'object',
  properties: {
    local_confirmado: { type: 'string', description: 'estádio e cidade REAIS (site da liga/clube), e se o mando do Sofascore está certo' },
    mando_invertido: { type: 'boolean', description: 'true se o jogo é na casa do time que o Sofascore lista como visitante' },
    defesa_azarao: { type: 'string', description: 'números com fonte e recorte: na condição e geral, contra quem sofreu, tendência, técnico novo, expulsões' },
    defesa_extremamente_fraca: { type: 'boolean' },
    desfalques_defesa_azarao: { type: 'array', items: { type: 'string' } },
    ataque_azarao: { type: 'string' },
    ataque_favorito: { type: 'string', description: 'gols e xG na condição, artilheiros (participação nos gols) e se jogam, tendência' },
    ataque_favorito_forte: { type: 'boolean' },
    desfalques_ataque_favorito: { type: 'array', items: { type: 'string' } },
    contexto: { type: 'string', description: 'calendário/rodízio, pausa, motivação, técnico, árbitro, altitude, gramado, escalação — no máximo 8 linhas' },
    poupa_titulares: { type: 'string', enum: ['SIM_CONFIRMADO', 'PROVAVEL', 'NAO', 'N/D'],
      description: 'o técnico do FAVORITO vai poupar titulares? SIM_CONFIRMADO = declaração/escalação; PROVAVEL = imprensa confiável diz que vai rodar (jogo decisivo logo depois, sequência pesada); NAO = disse que vai com força máxima ou não há motivo; N/D = sem informação' },
    poupa_evidencia: { type: 'string', description: 'fonte e data da informação sobre poupar (ou N/D)' },
    ajuste_pp: { type: 'number', minimum: -5, maximum: 5, description: 'ajuste em p.p. na prob. do mercado sugerido pelo defesa.py (melhor_mercado), com motivo no contexto' },
    fontes: { type: 'array', items: { type: 'string' } },
  },
  required: ['local_confirmado', 'mando_invertido', 'defesa_azarao', 'defesa_extremamente_fraca', 'desfalques_defesa_azarao',
    'ataque_azarao', 'ataque_favorito', 'ataque_favorito_forte', 'desfalques_ataque_favorito', 'contexto', 'poupa_titulares',
    'poupa_evidencia', 'ajuste_pp', 'fontes'],
}

const CET = {
  type: 'object',
  properties: {
    refutado: { type: 'boolean', description: 'true se a tese (defesa do azarão muito fraca E favorito com ataque forte) não se sustenta' },
    risco_azarao_marca: { type: 'boolean', description: 'azarão marca ≥ 1,3 gol/jogo na condição ou está no top 30% de ataques' },
    poupa_titulares_final: { type: 'string', enum: ['SIM_CONFIRMADO', 'PROVAVEL', 'NAO', 'N/D'],
      description: 'conferência própria: o favorito vai poupar titulares? (regra do Daniel: SIM_CONFIRMADO ou PROVAVEL tira o jogo)' },
    mercado_final: { type: 'string', enum: ['fav_marca_1', 'fav_marca_2', 'fav_marca_3', 'fav_vence', 'fav_dc', 'nenhum'],
      description: 'o mercado mais seguro que ainda tem ≥ 60% depois de tudo (pode rebaixar 2+ para 1+)' },
    ajuste_final_pp: { type: 'number', minimum: -5, maximum: 5, description: 'ajuste TOTAL em p.p. sobre a prob. do defesa.py para o mercado_final' },
    pontos_contra: { type: 'array', items: { type: 'string' } },
    pontos_a_favor: { type: 'array', items: { type: 'string' } },
    licao: { type: 'string', description: 'lição NOVA e geral que este caso ensina (não repita docs/licoes.md); "" se nenhuma' },
    veredito: { type: 'string', description: '1-2 frases' },
  },
  required: ['refutado', 'risco_azarao_marca', 'poupa_titulares_final', 'mercado_final', 'ajuste_final_pp', 'pontos_contra', 'pontos_a_favor', 'licao', 'veredito'],
}

const resumo = c => {
  const { mercado_odds, fora_do_corte, ...resto } = c
  return JSON.stringify(resto)
}

const res = await pipeline(
  alvo,
  c => agent(`Você é pesquisador de futebol. Jogo de ${dia} (horários de Brasília): ${c.jogo} (${c.pais} · ${c.competicao}), ${c.hora}, id Sofascore ${c.id}, ids dos times ${JSON.stringify(c.ids)}.
Tese: o AZARÃO (${c.azarao}, ${c.fav_casa ? 'fora' : 'em casa'}) tem defesa EXTREMAMENTE fraca e o FAVORITO (${c.favorito}) tem ataque forte e boa chance de marcar.
${LICOES}
Dados do ferramentas/defesa.py (Sofascore; tabela da temporada + últimos jogos de liga na condição; mercados com prob. conservadora; alertas automáticos): ${resumo(c)}
Pesquise A FUNDO, começando pelo Sofascore e depois imprensa local, site da liga e dos clubes:
1) Defesa do azarão: números na condição e geral, contra quem sofreu, tendência, técnico novo (recorte depois da troca), goleiro e zagueiros fora, expulsões que inflaram os gols.
2) Ataque do favorito: gols e xG na condição, artilheiros (participação nos gols) e se jogam, rodízio, pausa, motivação.
3) Ataque do azarão (risco de jogo aberto).
4) Escalação (event/${c.id}/lineups) e o MANDO REAL do jogo (site da liga/clube).
5) O técnico do FAVORITO vai POUPAR titulares? Procure entrevista coletiva, escalação provável na imprensa, jogo decisivo nos dias seguintes (copa, continental, clássico), sequência pesada. Regra do Daniel: se for poupar, o jogo sai da lista. Responda poupa_titulares com a fonte.
Nunca invente número: todo número com fonte e recorte. Sem dado → N/D.
${SOFA}`, { label: `pesq:${c.favorito}`, phase: 'Pesquisa', schema: PESQ, model: modelo }),
  (p, c) => !p ? { id: c.id, n: c.n, jogo: c.jogo, hora: c.hora, pesquisa: null, cetico: null, status: 'pesquisa falhou' } : agent(`Você é o CÉTICO. Tente DERRUBAR a tese "${c.azarao} tem defesa extremamente fraca e ${c.favorito} tem ataque forte e deve marcar" no jogo ${c.jogo} (${c.pais} · ${c.competicao}), ${c.hora} de ${dia}, id Sofascore ${c.id}, ids ${JSON.stringify(c.ids)}.
${LICOES}
Dados do defesa.py: ${resumo(c)}
Relatório do pesquisador: ${JSON.stringify(p)}
REGRA DO DANIEL: se o técnico do favorito for poupar titulares (confirmado ou provável por fonte confiável), o jogo sai — confira isso por conta própria (poupa_titulares_final), não só pelo calendário.
Confira por conta própria os pontos frágeis: amostra pequena; média inflada por goleadas (veja a mediana); gols sofridos x xG cedido (regressão); melhora recente (técnico novo); expulsões; o favorito marca acima do xG ou depende de 1 jogador ausente; rodízio e calendário; mando real; o azarão ataca bem (RISCO); regra 8 (modelo > mercado + 10 p.p.).
Feche o mercado_final: o mais seguro com ≥ ${Math.round(crit.prob_minima * 100)}% depois do ajuste (pode rebaixar "marca 2+" para "marca 1+"), e o ajuste_final_pp (−5 a +5) sobre a prob. do defesa.py para ESSE mercado. Se a defesa do azarão for só mediana para a liga, refutado=true.
Se o caso ensinar algo NOVO e geral que não esteja em docs/licoes.md, escreva em "licao".
${SOFA}`, { label: `cetico:${c.favorito}`, phase: 'Cético', schema: CET, model: modelo })
    .then(t => ({ id: c.id, n: c.n, jogo: c.jogo, hora: c.hora, pesquisa: p, cetico: t, status: t ? 'ok' : 'cetico falhou' })),
)
const ok = res.filter(Boolean)
const falhas = ok.filter(r => r.status !== 'ok')
if (falhas.length) log(`Agentes falharam em: ${falhas.map(r => `${r.jogo} (${r.status})`).join(' | ')} — retome com resumeFromRunId`)
return { resultados: ok, agentes: alvo.length * 2, sem_pesquisa: fora.map(c => c.jogo) }
