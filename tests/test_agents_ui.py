"""Lógica de expansão de votos da tela /agents (dashboard/agents.html).

A mesma estrutura de resultado é executada em node contra a função `expand`
extraída da própria página, para que o HTML não possa divergir silenciosamente
do contrato selado de scripts/multiasset_radar.detail(). Skip onde node não
existe (deploy Railway).

Forma simulada = documentada em scripts/multiasset_radar.py: comitê devolve
``votes`` (5, ``require_all_votes=True``), cada voto
``{analyst_id, temperature, seed, signal:{signal, confidence, evidence:[...]}}``.
"""

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "dashboard" / "agents.html"

NODE_CHECK = """
const {expand} = (() => {
  const src = require('fs').readFileSync(process.argv[2], 'utf8');
  const m = src.match(/function expand\\(items\\) \\{[\\s\\S]*?\\n  \\}/);
  if (!m) throw new Error('expand ausente na página');
  const fn = eval('(' + m[0].replace('function expand(items) {', '(items)=>{')
    .replace(/\\n  \\}$/, '}') + ')');
  return {expand: fn};
})();
const items = [
  {ticker:'PETR4', session:'2026-10-29', status:'COMPLETED', mode:'live',
   votes:[
    {analyst_id:1, temperature:1, seed:1,
     signal:{signal:'COMPRA', confidence:0.78,
             evidence:[{code:'CLOSE_ABOVE_SMA50', role:'SUPPORTS_COMPRA'}]}},
    {analyst_id:2, temperature:1, seed:2,
     signal:{signal:'VENDA', confidence:0.6,
             evidence:[{code:'RSI_CURRENT', role:'CAUTION'}]}},
   ],
   consensus:{winning_signal:'COMPRA', consensus_reached:true},
   risk:{verdict:'APROVADO'}, recommendation:'COMPRA'},
  {ticker:'PETR4', session:'2026-10-29', status:'COMPLETED', mode:'live',
   votes:[
    {analyst_id:2, temperature:1, seed:2,
     signal:{signal:'COMPRA', confidence:0.9,
             evidence:[{code:'MACD_ABOVE_SIGNAL', role:'SUPPORTS_COMPRA'}]}},
   ],
   consensus:{winning_signal:'MANTER', consensus_reached:false},
   risk:{verdict:'VETADO'}, recommendation:'MANTER'},
];
const rows = expand(items);
if (rows.length !== 3) throw new Error('esperado 3 linhas, obtidas ' + rows.length);
const r0 = rows[0];
if (r0.signal !== 'COMPRA' || r0.confidence !== 0.78)
  throw new Error('voto 1 incompleto');
if (r0.evidence[0].code !== 'CLOSE_ABOVE_SMA50')
  throw new Error('evidência perdida');
if (r0.consensus.winning_signal !== 'COMPRA' || r0.risk.verdict !== 'APROVADO')
  throw new Error('consenso/risco do parecer perdidos');
if (rows[2].consensus.consensus_reached !== false)
  throw new Error('consenso dividido perdido');
const empty = expand([
  {ticker:'X', session:'2026-10-30', status:'PREPARED', mode:'live'},
]);
if (empty.length !== 1 || empty[0].signal !== null || empty[0].analyst_id !== '—')
  throw new Error('parecer preparado deve aparecer sem voto fabricado');
console.log('OK: 3 linhas, parecer preparado sem voto fabricado');
"""


@unittest.skipUnless(shutil.which("node"), "node indisponível")
class Expand(unittest.TestCase):
    def test_vote_rows_follow_sealed_contract(self):
        source = PAGE.read_text(encoding="utf-8")
        self.assertIn("function expand(items)", source)
        self.assertIn('STATUS', source)  # rótulos de estado na mesma página
        with tempfile.TemporaryDirectory(prefix="hfl-agents-") as tmp_dir:
            script = Path(tmp_dir) / "agents_expand_check.js"
            script.write_text(NODE_CHECK, encoding="utf-8")
            result = subprocess.run(
                ["node", str(script), str(PAGE)], capture_output=True, text=True
            )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertIn("OK: 3 linhas", result.stdout)


if __name__ == "__main__":
    unittest.main()
