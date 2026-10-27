#!/usr/bin/env python3
"""Times estatisticamente muito superiores para ganhar ou empatar (dupla chance) — pedido do Daniel em 27/10.

Triagem dos jogos do dia no 365Scores (sem agentes):
  - liga: modelo de dupla chance pelas tabelas casa/fora, pela tabela geral e pelos jogos recentes (vale a menor),
    teste de estresse (favorito −15%, azarão +25%), PPG e saldo por jogo dos dois, odd da bet365 sem margem e
    movimento desde a abertura;
  - copa: a liga de cada time (posição e PPG) e a dupla chance da bet365 sem margem (não há modelo entre divisões).
Critérios de corte usados em 27/10 (liga): modelo ≥ 85%, estresse ≥ 78%, PPG do favorito ao menos 0,9 acima,
saldo do favorito ≥ +0,5 por jogo, 6+ jogos, odd do favorito sem subir mais de 5% e a do azarão sem cair 10%+.
Copa: casa ≥ 90% e o favorito pelo menos 2 divisões acima.

Uso: python3 ferramentas/superior.py AAAA-MM-DD saida.json
"""
import sys, json, collections
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import plataformas as pl, defesa as df, casa as cs, varredura as v
if len(sys.argv) < 3 or sys.argv[1] in ('-h', '--help'):
    sys.exit(__doc__)
D = sys.argv[1]
api = pl.S365(D)                 # estatística com cache
viva = pl.S365(D, pasta=None)    # odds de agora
cfg = pl.config(); vr = cfg["varredura"]; K, SIG = vr["encolhimento_jogos"], vr["incerteza_sigma"]
gs = viva.jogos()
def ok(g):
    nome = g.get('competitionDisplayName') or ''
    return (g.get('statusGroup') == 2 and (g.get('odds') or {}).get('options') and not pl.amistoso(g)
            and 'Reserva' not in nome and not df.nivel_base([nome], df.DEFESA_PADRAO['palavras_base'] + cs.FEMININO,
                                                             [g['homeCompetitor']['name'], g['awayCompetitor']['name']]))
gs = [g for g in gs if ok(g)]
def odds1x2(g):
    o = {str(x['name']): ((x.get('rate') or {}).get('decimal'), (x.get('originalRate') or {}).get('decimal')) for x in g['odds']['options']}
    return o
def p_dc(lh, la, lado):
    m = v.matriz(lh, la, 0.0, SIG); r = v.resultado(m)
    return (r['1'] + r['X']) if lado == 'casa' else (r['2'] + r['X'])
def stats_liga(t, comp_rows):
    r = comp_rows.get(t)
    if not r or not r.get('gamePlayed'): return None
    gp = r['gamePlayed']
    return {'pos': r.get('position'), 'n': len(comp_rows), 'pj': gp, 'ppg': round(r.get('points', 0) / gp, 2),
            'sg_j': round((r.get('for', 0) - r.get('against', 0)) / gp, 2), 'gm': r.get('for'), 'gs': r.get('against')}
def liga_do_time(tid):
    res = [x for x in api.resultados(tid) if not pl.amistoso(x)][:12]
    for comp, _ in collections.Counter(x['competitionId'] for x in res).most_common():
        rows = api.tabela(comp, 1)
        if tid in rows and len(rows) >= 6:
            nome = next((x.get('competitionDisplayName') for x in res if x['competitionId'] == comp), '')
            return comp, nome, rows
    return None, None, {}
def analisa(g):
    h, a = g['homeCompetitor'], g['awayCompetitor']
    o = odds1x2(g)
    try:
        o1, o2 = o['1'][0], o['2'][0]
    except KeyError:
        return None
    if not o1 or not o2: return None
    lado = 'casa' if o1 < o2 else 'fora'
    if min(o1, o2) > 1.90: return None
    fav, und = (h, a) if lado == 'casa' else (a, h)
    comp = g.get('competitionId')
    rows = api.tabela(comp, 1)
    out = {'id': g['id'], 'hora': pl.hora_br(g), 'jogo': f"{h['name']} x {a['name']}", 'comp': f"{g['_pais']} · {g.get('competitionDisplayName')}",
           'lado': lado, 'fav': fav['name'], 'odd_fav': min(o1, o2), 'odd_fav_abre': (o['1'] if lado == 'casa' else o['2'])[1],
           'odd_und': max(o1, o2), 'odd_und_abre': (o['2'] if lado == 'casa' else o['1'])[1]}
    # odds bet365 dupla chance
    lns = [ln for ln in viva.get('bets/lines/', games=g['id'], userCountryId=1).get('lines', []) if ln.get('bookmakerId') == 14]
    for ln in lns:
        for s in cs.selecoes(ln, h['name'], a['name']):
            if s['mercado'] == 'dupla_chance' and s['lado'] == lado:
                out.update({'dc_odd': s['odd'], 'dc_abre': s['odd_abertura'], 'dc_p': s['p_casa']})
            if s['mercado'] == 'vence' and s['lado'] == lado:
                out.update({'v_p': s['p_casa']})
    liga = h['id'] in rows and a['id'] in rows
    out['tipo'] = 'liga' if liga else 'copa'
    if liga:
        tc, tf = api.tabela(comp, 2), api.tabela(comp, 3)
        ml = pl.medias_liga(tc, tf)
        sf, su = stats_liga(fav['id'], rows), stats_liga(und['id'], rows)
        out.update({'fav_liga': sf, 'und_liga': su})
        rh, ra = tc.get(h['id']), tf.get(a['id'])
        ps = {}
        if ml and rh and ra and min(rh.get('gamePlayed', 0), ra.get('gamePlayed', 0)) >= 3:
            th = (rh['for'] / rh['gamePlayed'], rh['against'] / rh['gamePlayed'], rh['gamePlayed'])
            ta = (ra['for'] / ra['gamePlayed'], ra['against'] / ra['gamePlayed'], ra['gamePlayed'])
            lt = pl.lambdas(th, ta, ml, K); ps['tabela_cf'] = p_dc(*lt, lado)
            # força geral (todas as partidas)
            gh, ga = rows[h['id']], rows[a['id']]
            mg = (ml[0] + ml[1]) / 2
            th2 = (gh['for'] / gh['gamePlayed'], gh['against'] / gh['gamePlayed'], gh['gamePlayed'])
            ta2 = (ga['for'] / ga['gamePlayed'], ga['against'] / ga['gamePlayed'], ga['gamePlayed'])
            lg = pl.lambdas((th2[0] * ml[0] / mg, th2[1] * ml[1] / mg, th2[2]), (ta2[0] * ml[1] / mg, ta2[1] * ml[0] / mg, ta2[2]), ml, K)
            ps['geral'] = p_dc(*lg, lado)
            base = min(lt, lg, key=lambda l: p_dc(*l, lado))
            lf, lu = (base[0], base[1]) if lado == 'casa' else (base[1], base[0])
            st = (lf * 0.85, lu * 1.25)
            ps['estresse'] = p_dc(*(st if lado == 'casa' else st[::-1]), lado)
            out['lambdas'] = [round(x, 2) for x in base]
            res_h, res_a = api.resultados(h['id']), api.resultados(a['id'])
            ch, ca = pl.condicao(res_h, h['id'], True, comp, 10), pl.condicao(res_a, a['id'], False, comp, 10)
            rec_h, rec_a = pl.medias_de(ch, True), pl.medias_de(ca, False)
            if rec_h and rec_a and min(rec_h[2], rec_a[2]) >= 3:
                ps['recentes'] = p_dc(*pl.lambdas(rec_h, rec_a, ml, K), lado)
        out['p'] = {k: round(x, 3) for k, x in ps.items()}
        out['p_min'] = round(min([x for k, x in ps.items() if k != 'estresse']), 3) if ps else None
    else:
        cf, nf, rf = liga_do_time(fav['id']); cu, nu, ru = liga_do_time(und['id'])
        out.update({'fav_liga': stats_liga(fav['id'], rf), 'fav_liga_nome': nf, 'und_liga': stats_liga(und['id'], ru), 'und_liga_nome': nu,
                    'mesma_liga': cf == cu and cf is not None})
    return out
with ThreadPoolExecutor(max_workers=8) as ex:
    res = [r for r in ex.map(analisa, gs) if r]
json.dump(res, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
print(len(gs), 'jogos;', len(res), 'com favorito ≤ 1.90;', 'falhas', viva.falhas + api.falhas)
