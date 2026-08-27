"""
serialize.py — zapis/odczyt stanu KHIPU (dodane 2026-08).

Pozwala zapisać sesję (LUT256 + ROPE256/ROPE48 z ich węzłami) do pliku
i wznowić ją później, albo wyeksportować węzły do analizy poza KHIPU
(np. `pandas.DataFrame.from_records([node_to_dict(n) for n in rope])`).

DECYZJA INTERPRETACYJNA: "relacje GIPU", o które pytał się o serializację
tej funkcji, NIE są osobnym stanem do zapisania — `GIPUIntegrator` samo
w sobie jest bezstanowe (`relation_between()`/`update_relations()`/
`extend_relations()` to czyste funkcje operujące na przekazanych węzłach,
patrz gipu.py). Cała "pamięć" relacji żyje w polu `.r` KAŻDEGO węzła
(`Node256.r`) — więc zapisanie sznura (ROPE256/ROPE48) już w pełni
zapisuje relacje, bez potrzeby osobnego formatu dla GIPU.

Co NIE jest zapisywane (celowo, bo jest tanie do odtworzenia z powrotem):
- `VisualEngine`/`FrameBuffer` (klatki FRAME) — czysto pochodne z okna
  ostatnich węzłów sznura, przeliczane w locie przy każdym `feed()`.
  Po `load_*()` bufor klatek jest pusty, aż coś znowu wywoła `feed()`.
- `TIMDRValidator`/`GIPUIntegrator` same w sobie — bezstanowe (patrz
  wyżej), rekonstruowane jako świeże obiekty przy `load_*()`.

Dwa formaty:
- JSON (`save_json`/`load_json`) — czytelny, przenośny, BEZPIECZNY do
  odczytu z niezaufanego źródła (nie wykonuje kodu przy deserializacji).
  Zalecany format domyślny.
- pickle (`save_pickle`/`load_pickle`) — szybszy, zapisuje dowolny obiekt
  Pythona bit-w-bit bez ręcznego mapowania na dict, ale odczyt pliku
  pickle z NIEZAUFANEGO źródła jest niebezpieczny (deserializacja może
  wykonać dowolny kod - to udokumentowana właściwość modułu `pickle`
  w Pythonie, nie specyfika KHIPU). Używaj tylko dla własnych plików.
"""
import json
import pickle
from dataclasses import asdict
from typing import Dict, Optional

from .node256 import Node256
from .lut256 import LUT256
from .rope import Rope256
from .rope48 import Rope48, LENGTH as ROPE48_LENGTH


# ---------------------------------------------------------------------
# Węzeł <-> dict
# ---------------------------------------------------------------------

def node_to_dict(node: Optional[Node256]) -> Optional[dict]:
    """None -> None (slot pusty w Rope48), Node256 -> dict płaski (7 pól + idx)."""
    if node is None:
        return None
    return asdict(node)


def node_from_dict(d: Optional[dict]) -> Optional[Node256]:
    if d is None:
        return None
    return Node256(**d)


# ---------------------------------------------------------------------
# LUT256 <-> dict
# ---------------------------------------------------------------------

def lut256_to_dict(lut: LUT256) -> dict:
    """Klucze idx jako string (wymóg JSON - klucze obiektu muszą być
    stringami), skonwertowane z powrotem na int w lut256_from_dict()."""
    return {str(idx): node_to_dict(node) for idx, node in lut._table.items()}


def lut256_from_dict(d: dict) -> LUT256:
    lut = LUT256()
    for idx_str, node_d in d.items():
        lut._table[int(idx_str)] = node_from_dict(node_d)
    return lut


# ---------------------------------------------------------------------
# Rope256 <-> dict
# ---------------------------------------------------------------------

def rope256_to_dict(rope: Rope256) -> dict:
    return {"nodes": [node_to_dict(n) for n in rope.nodes]}


def rope256_from_dict(d: dict) -> Rope256:
    rope = Rope256()
    rope.nodes = [node_from_dict(n) for n in d["nodes"]]
    return rope


# ---------------------------------------------------------------------
# Rope48 <-> dict
# ---------------------------------------------------------------------

def rope48_to_dict(rope: Rope48) -> dict:
    return {
        "name": rope.name,
        "slots": [node_to_dict(n) for n in rope.slots],
        "write_cursor": rope._write_cursor,
        "total_pushed": rope.total_pushed,
    }


def rope48_from_dict(d: dict) -> Rope48:
    slots = [node_from_dict(n) for n in d["slots"]]
    if len(slots) != ROPE48_LENGTH:
        raise ValueError(
            f"rope48_from_dict: oczekiwano {ROPE48_LENGTH} slotów (izometria "
            f"ROPE48), dostano {len(slots)} - dane uszkodzone albo z innej wersji"
        )
    rope = Rope48(d["name"])
    rope.slots = slots
    rope._write_cursor = d["write_cursor"]
    rope.total_pushed = d["total_pushed"]
    return rope


def _rope48_last_node(rope: Rope48) -> Optional[Node256]:
    """Węzeł najpóźniej wypchnięty na ten Rope48 (dla odtworzenia
    TetragonSystem._last_nodes po load - patrz tetragon_system_from_dict).
    Rope48 to pierścień FIFO, więc 'ostatni' to NIE koniecznie ostatni
    niepusty slot w kolejności indeksów - trzeba cofnąć się o 1 od
    _write_cursor (miejsca, gdzie trafi NASTĘPNY push)."""
    if rope.total_pushed == 0:
        return None
    last_idx = (rope._write_cursor - 1) % ROPE48_LENGTH
    return rope.slots[last_idx]


# ---------------------------------------------------------------------
# Wysokopoziomowe: cała sesja SingleCPUSystem / TetragonSystem
# ---------------------------------------------------------------------

def single_cpu_system_to_dict(system) -> dict:
    """LUT256 + ROPE256 kompletnego `SingleCPUSystem`. Nie zapisuje
    FrameBuffer/VisualEngine - patrz uwaga na górze pliku."""
    return {
        "kind": "SingleCPUSystem",
        "lut256": lut256_to_dict(system.lut),
        "rope256": rope256_to_dict(system.rope),
    }


def single_cpu_system_from_dict(d: dict, frame_buffer_size: int = 32):
    """Odtwarza `SingleCPUSystem` z dict zapisanego przez
    `single_cpu_system_to_dict()`. TIMDR/GIPU/VisualEngine/FrameBuffer są
    świeżymi obiektami (bezstanowe albo pochodne - patrz uwaga na górze
    pliku), LUT256/Rope256 są dokładnie odtworzone."""
    from .pipeline import SingleCPUSystem  # import lokalny - unika cyklu importów
    if d.get("kind") != "SingleCPUSystem":
        raise ValueError(f"single_cpu_system_from_dict: oczekiwano kind='SingleCPUSystem', dostano {d.get('kind')!r}")
    system = SingleCPUSystem(frame_buffer_size=frame_buffer_size)
    system.lut = lut256_from_dict(d["lut256"])
    system.rope = rope256_from_dict(d["rope256"])
    return system


def tetragon_system_to_dict(system) -> dict:
    """LUT256 (wspólna) + ROPE48 każdego CPU + stan NODE_AXIS kompletnego
    `TetragonSystem`. Nie zapisuje FrameBuffer/VisualEngine (ten system
    ich nie ma) ani `_last_nodes` wprost - odtwarzane z ropes przy load."""
    return {
        "kind": "TetragonSystem",
        "cpu_names": list(system.cpu_names),
        "lut256": lut256_to_dict(system.lut),
        "ropes": {name: rope48_to_dict(rope) for name, rope in system.ropes.items()},
        "axis": {
            "s_axis": system.axis.s_axis,
            "k_axis": system.axis.k_axis,
            "b_axis": system.axis.b_axis,
            "l_axis": system.axis.l_axis,
            "r_axis": system.axis.r_axis,
        },
    }


def tetragon_system_from_dict(d: dict):
    """Odtwarza `TetragonSystem` z dict zapisanego przez
    `tetragon_system_to_dict()`. `_last_nodes` jest odtworzone z ostatniego
    faktycznie wypchniętego węzła każdego Rope48 (patrz `_rope48_last_node`),
    nie zapisywane osobno."""
    from .tetragon import TetragonSystem  # import lokalny - unika cyklu importów
    if d.get("kind") != "TetragonSystem":
        raise ValueError(f"tetragon_system_from_dict: oczekiwano kind='TetragonSystem', dostano {d.get('kind')!r}")
    system = TetragonSystem(cpu_names=tuple(d["cpu_names"]))
    system.lut = lut256_from_dict(d["lut256"])
    for name, rope_d in d["ropes"].items():
        system.ropes[name] = rope48_from_dict(rope_d)

    axis_d = d["axis"]
    system.axis.s_axis = axis_d["s_axis"]
    system.axis.k_axis = axis_d["k_axis"]
    system.axis.b_axis = axis_d["b_axis"]
    system.axis.l_axis = axis_d["l_axis"]
    system.axis.r_axis = axis_d["r_axis"]

    for name, rope in system.ropes.items():
        last = _rope48_last_node(rope)
        if last is not None:
            system._last_nodes[name] = last
    return system


# ---------------------------------------------------------------------
# Zapis/odczyt plikowy (JSON i pickle) - operują na dowolnym dict lub
# obiekcie, nie tylko na systemach zdefiniowanych wyżej.
# ---------------------------------------------------------------------

def save_json(obj_dict: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj_dict, f, indent=2, ensure_ascii=False)


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_pickle(obj, path: str) -> None:
    with open(path, "wb") as f:
        pickle.dump(obj, f)


def load_pickle(path: str):
    """UWAGA BEZPIECZEŃSTWA: `pickle.load()` wykonuje dowolny kod przy
    deserializacji spreparowanego pliku - to udokumentowana właściwość
    modułu `pickle` w Pythonie (patrz oficjalna dokumentacja `pickle`),
    nie specyfika tej funkcji. Wołaj tylko na plikach zapisanych przez
    `save_pickle()` z zaufanego źródła (np. własna wcześniejsza sesja)."""
    with open(path, "rb") as f:
        return pickle.load(f)
