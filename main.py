from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum
import uuid, random, os

app = FastAPI(title="Porto do Itaqui — Simulador de Filas")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# ═══════════════════════════════════════════
#  ENUMS
# ═══════════════════════════════════════════

class TipoNavio(str, Enum):
    GRANEL       = "granel"
    CONTEINER    = "conteiner"
    COMBUSTIVEL  = "combustivel"
    MARINHA      = "marinha"
    CONT_REFRIG  = "cont_refrig"

class Politica(str, Enum):
    FIFO    = "fifo"
    PRIO_NP = "prio_np"
    SJF     = "sjf"
    LCFS    = "lcfs"

# ═══════════════════════════════════════════
#  CONFIGURAÇÃO ESTÁTICA
# ═══════════════════════════════════════════

TIPO_CFG: Dict = {
    TipoNavio.GRANEL:      {"prio": 3, "mu": 10, "bercos": ["B1", "B4"], "cor": "#1D9E75", "nome": "Granéis"},
    TipoNavio.CONTEINER:   {"prio": 3, "mu":  8, "bercos": ["B2", "B4"], "cor": "#4b9fd5", "nome": "Contêineres"},
    TipoNavio.COMBUSTIVEL: {"prio": 3, "mu": 12, "bercos": ["B3"],       "cor": "#d4a327", "nome": "Combustíveis"},
    TipoNavio.MARINHA:     {"prio": 1, "mu":  6, "bercos": ["B4", "B1", "B2", "B3"], "cor": "#e05555", "nome": "Marinha / C.Viva"},
    TipoNavio.CONT_REFRIG: {"prio": 2, "mu":  8, "bercos": ["B2", "B4"], "cor": "#8b7fd4", "nome": "Cont. Refrigerado"},
}

BERCO_CFG: Dict = {
    "B1": {"nome": "B1 — Granéis",      "desc": "Alta capacidade",          "aceita": [TipoNavio.GRANEL, TipoNavio.MARINHA]},
    "B2": {"nome": "B2 — Contêineres",  "desc": "Empresa privada",          "aceita": [TipoNavio.CONTEINER, TipoNavio.CONT_REFRIG, TipoNavio.MARINHA]},
    "B3": {"nome": "B3 — Combustíveis", "desc": "Restrição ambiental",      "aceita": [TipoNavio.COMBUSTIVEL]},
    "B4": {"nome": "B4 — Multiuso",     "desc": "Prioridade institucional", "aceita": list(TipoNavio)},
}

POL_LABEL: Dict = {
    Politica.FIFO:    "FIFO — Primeiro a Chegar",
    Politica.PRIO_NP: "Prioridade Não Preemptiva",
    Politica.SJF:     "SJF — Menor Serviço Primeiro",
    Politica.LCFS:    "LCFS — Último a Chegar",
}

PRIO_LABEL = {1: "Máxima", 2: "Alta", 3: "Normal"}

# ═══════════════════════════════════════════
#  MODELO DE DADOS
# ═══════════════════════════════════════════

@dataclass
class Navio:
    id: str
    nome: str
    tipo: TipoNavio
    prio: int
    ts: float            # tempo de serviço (horas)
    t_chegada: float     # chegada no relógio da simulação
    status: str = "fila" # fila | servico | ok
    berco: Optional[str] = None
    t_ini: Optional[float] = None   # início do serviço
    t_fim: Optional[float] = None   # conclusão do serviço
    t_rest: Optional[float] = None  # tempo restante no berço

# ═══════════════════════════════════════════
#  ENGINE DE SIMULAÇÃO
# ═══════════════════════════════════════════

class Sim:
    def __init__(self):
        self.reset()

    def reset(self):
        self.clock   = 0.0
        self.pol     = Politica.PRIO_NP
        self.navios:  Dict[str, Navio]           = {}
        self.bercos:  Dict[str, Optional[str]]   = {b: None for b in BERCO_CFG}
        self.events:  List[dict]                 = []
        self.n_ok    = 0      # total atendidos
        self.sum_wq  = 0.0   # soma das esperas
        self.sum_w   = 0.0   # soma dos tempos no sistema
        self.n_arr   = 0      # total de chegadas

    def _ev(self, msg: str):
        self.events.append({"t": round(self.clock, 1), "msg": msg})
        if len(self.events) > 200:
            self.events = self.events[-200:]

    # ── Ordenação da fila conforme política ──────────────────
    def _queue(self) -> List[Navio]:
        q = [n for n in self.navios.values() if n.status == "fila"]
        if self.pol == Politica.FIFO:
            return sorted(q, key=lambda n: n.t_chegada)
        if self.pol == Politica.PRIO_NP:
            return sorted(q, key=lambda n: (n.prio, n.t_chegada))
        if self.pol == Politica.SJF:
            return sorted(q, key=lambda n: (n.ts, n.t_chegada))
        if self.pol == Politica.LCFS:
            return sorted(q, key=lambda n: -n.t_chegada)
        return sorted(q, key=lambda n: n.t_chegada)

    # ── Alocação: tenta encaixar navios da fila em berços livres ──
    def _allocate(self):
        # OTIMIZAÇÃO: Se houver 3+ navios de combustível na fila e B4 está ocioso,
        # aloca o primeiro navio de combustível ao B4
        fila_combustivel = [n for n in self._queue() if n.tipo == TipoNavio.COMBUSTIVEL]
        if len(fila_combustivel) >= 3 and self.bercos["B4"] is None:
            navio = fila_combustivel[0]
            if navio.tipo in BERCO_CFG["B4"]["aceita"]:
                self.bercos["B4"]       = navio.id
                navio.status            = "servico"
                navio.berco             = "B4"
                navio.t_ini             = self.clock
                navio.t_rest            = navio.ts
                wq = self.clock - navio.t_chegada
                self._ev(f"{navio.nome} → B4 (espera {wq:.1f}h) [OTIMIZAÇÃO: 3+ combustível]")
        
        # Alocação normal da fila
        for navio in self._queue():
            for b_id in TIPO_CFG[navio.tipo]["bercos"]:
                if self.bercos[b_id] is None and navio.tipo in BERCO_CFG[b_id]["aceita"]:
                    self.bercos[b_id]       = navio.id
                    navio.status            = "servico"
                    navio.berco             = b_id
                    navio.t_ini             = self.clock
                    navio.t_rest            = navio.ts
                    wq = self.clock - navio.t_chegada
                    self._ev(f"{navio.nome} → {b_id} (espera {wq:.1f}h)")
                    break  # navio alocado, próximo da fila

    # ── Adicionar navio ──────────────────────────────────────
    def add(self, nome: str, tipo: TipoNavio, ts_ov: Optional[float]) -> Navio:
        cfg = TIPO_CFG[tipo]
        mu  = cfg["mu"]
        if ts_ov and ts_ov > 0:
            ts = round(ts_ov, 1)
        else:
            # distribuição exponencial com cap (0.3× a 3× a média)
            ts = round(max(mu * 0.3, min(mu * 3.0, random.expovariate(1.0 / mu))), 1)

        n = Navio(
            id=str(uuid.uuid4())[:6].upper(),
            nome=nome, tipo=tipo,
            prio=cfg["prio"], ts=ts,
            t_chegada=self.clock,
        )
        self.navios[n.id] = n
        self.n_arr += 1
        self._ev(f"{nome} chegou | {cfg['nome']} | Prio: {PRIO_LABEL[cfg['prio']]} | Serviço: {ts}h")
        self._allocate()
        return n

    # ── Remover navio da fila ────────────────────────────────
    def remove(self, nid: str):
        n = self.navios.get(nid)
        if not n:
            raise HTTPException(404, "Navio não encontrado")
        if n.status != "fila":
            raise HTTPException(400, "Só é possível remover navios na fila")
        del self.navios[nid]
        self._ev(f"{n.nome} removido da fila")

    # ── Avançar relógio (orientado a eventos) ────────────────
    def advance(self, h: float):
        """
        Processa o intervalo de tempo em fatias: cada fatia termina no
        próximo evento de conclusão de serviço, garantindo que navios
        em cadeia (A libera berço → B entra → B conclui) sejam
        tratados corretamente mesmo em avanços longos.
        """
        target = self.clock + h

        while True:
            window = target - self.clock

            # Encontra a próxima conclusão dentro da janela restante
            nxt: Optional[tuple] = None
            for b_id, nid in self.bercos.items():
                if nid is None:
                    continue
                t_rest = self.navios[nid].t_rest or 0
                if 0 < t_rest <= window + 1e-9:
                    if nxt is None or t_rest < nxt[0]:
                        nxt = (t_rest, b_id)

            if nxt is None:
                # Sem conclusões na janela — avança até o target e sai
                for nid in self.bercos.values():
                    if nid:
                        self.navios[nid].t_rest = (self.navios[nid].t_rest or 0) - window
                self.clock = target
                break

            dt, b_id = nxt
            nid = self.bercos[b_id]
            n   = self.navios[nid]

            # Avança todos os t_rest pelo intervalo até este evento
            for nid2 in self.bercos.values():
                if nid2:
                    self.navios[nid2].t_rest = (self.navios[nid2].t_rest or 0) - dt
            self.clock = round(self.clock + dt, 6)

            # Registra conclusão
            n.t_fim           = self.clock
            n.status          = "ok"
            n.berco           = None
            self.bercos[b_id] = None

            wq = round((n.t_ini or 0) - n.t_chegada, 2)
            w  = round(n.t_fim - n.t_chegada, 2)
            self.n_ok   += 1
            self.sum_wq += max(0.0, wq)
            self.sum_w  += max(0.0, w)
            self._ev(f"{n.nome} concluído em {b_id} | Espera: {wq:.1f}h | Sistema: {w:.1f}h")

            # Tenta alocar fila ao berço recém-liberado
            self._allocate()

    # ── Métricas da Teoria das Filas ─────────────────────────
    def metrics(self) -> dict:
        in_s = sum(1 for n in self.navios.values() if n.status == "servico")
        in_q = sum(1 for n in self.navios.values() if n.status == "fila")
        Wq   = round(self.sum_wq / self.n_ok, 2) if self.n_ok else 0.0
        W    = round(self.sum_w  / self.n_ok, 2) if self.n_ok else 0.0
        rho  = round(sum(1 for v in self.bercos.values() if v) / 4 * 100, 1)
        return {
            "L":  in_s + in_q,
            "Lq": in_q,
            "W":  W,
            "Wq": Wq,
            "rho": rho,
            "atendidos": self.n_ok,
            "em_servico": in_s,
            "na_fila": in_q,
        }

    # ── Estado completo para o frontend ─────────────────────
    def state(self) -> dict:
        fila = []
        for i, n in enumerate(self._queue()):
            fila.append({
                "id": n.id, "nome": n.nome, "pos": i + 1,
                "tipo": n.tipo.value,
                "tipo_nome": TIPO_CFG[n.tipo]["nome"],
                "prio": n.prio,
                "prio_label": PRIO_LABEL[n.prio],
                "ts": round(n.ts, 1),
                "t_espera": round(self.clock - n.t_chegada, 1),
                "cor": TIPO_CFG[n.tipo]["cor"],
                "bercos_previstos": TIPO_CFG[n.tipo]["bercos"],
            })

        bercos = {}
        for b_id in BERCO_CFG:
            nid = self.bercos[b_id]
            n   = self.navios.get(nid) if nid else None
            bercos[b_id] = {
                "nome": BERCO_CFG[b_id]["nome"],
                "desc": BERCO_CFG[b_id]["desc"],
                "navio": {
                    "id": n.id,
                    "nome": n.nome,
                    "tipo_nome": TIPO_CFG[n.tipo]["nome"],
                    "prio_label": PRIO_LABEL[n.prio],
                    "ts":  round(n.ts, 1),
                    "t_rest": round(max(0.0, n.t_rest or 0), 1),
                    "progresso": round(max(0.0, min(100.0, (1 - (n.t_rest or 0) / n.ts) * 100)), 1),
                    "cor": TIPO_CFG[n.tipo]["cor"],
                } if n else None,
            }

        return {
            "clock":     round(self.clock, 1),
            "politica":  self.pol.value,
            "pol_label": POL_LABEL[self.pol],
            "bercos":    bercos,
            "fila":      fila,
            "events":    list(reversed(self.events[-20:])),
            "metricas":  self.metrics(),
        }

# ═══════════════════════════════════════════
#  INSTÂNCIA GLOBAL
# ═══════════════════════════════════════════

sim = Sim()

# ═══════════════════════════════════════════
#  SCHEMAS DE REQUISIÇÃO
# ═══════════════════════════════════════════

class AddReq(BaseModel):
    nome: str
    tipo: TipoNavio
    ts: Optional[float] = None   # override do tempo de serviço

class AdvReq(BaseModel):
    horas: float

class PolReq(BaseModel):
    politica: Politica

# ═══════════════════════════════════════════
#  ENDPOINTS
# ═══════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
def index():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend.html")
    with open(p, encoding="utf-8") as f:
        return f.read()

@app.get("/state")
def get_state():
    return sim.state()

@app.post("/ships")
def add_ship(r: AddReq):
    n = sim.add(r.nome, r.tipo, r.ts)
    return {"id": n.id, "ts": n.ts}

@app.delete("/ships/{nid}")
def del_ship(nid: str):
    sim.remove(nid)
    return {"ok": True}

@app.post("/advance")
def advance(r: AdvReq):
    if r.horas <= 0:
        raise HTTPException(400, "horas deve ser > 0")
    sim.advance(r.horas)
    return {"clock": sim.clock}

@app.post("/policy")
def set_pol(r: PolReq):
    sim.pol = r.politica
    sim._ev(f"Política alterada: {POL_LABEL[r.politica]}")
    return {"label": POL_LABEL[r.politica]}

@app.post("/reset")
def reset_sim():
    sim.reset()
    return {"ok": True}

@app.post("/demo")
def demo():
    """Carrega cenário demo com 9 navios representativos."""
    ships = [
        ("MV Amazonas",     TipoNavio.GRANEL,      None),
        ("MT BrasPetro 5",  TipoNavio.COMBUSTIVEL, None),
        ("CV Santos Star",  TipoNavio.CONTEINER,   None),
        ("NE Constituição", TipoNavio.MARINHA,      None),
        ("MV Cerrado",      TipoNavio.GRANEL,      None),
        ("CV Nórdica Fria", TipoNavio.CONT_REFRIG, None),
        ("MT Petrobras 3",  TipoNavio.COMBUSTIVEL, None),
        ("MV Pampa",        TipoNavio.GRANEL,      None),
        ("CV Global Box",   TipoNavio.CONTEINER,   None),
    ]
    for nome, tipo, ts in ships:
        sim.add(nome, tipo, ts)
    return {"ok": True, "count": len(ships)}

# ═══════════════════════════════════════════
#  INICIALIZAÇÃO PARA RENDER (entrada do gunicorn/hypercorn)
# ═══════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
