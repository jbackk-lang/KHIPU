🌀 1. SKRĘT (warstwa nadrzędna)
Skręt decyduje o wszystkim.
Każdy stan należy do jednej klasy:

S+ — prawoskrętny

S− — lewoskrętny

S0 — neutralny φ

S↑ — skręt rosnący

S↓ — skręt malejący

S× — odwracalny

S! — nieodwracalny

Walidacja: TIMDER pilnuje zasady 1/2 i φ jako środka.
GIPU może wymusić odwrócenie.

➡️ 2. KIERUNEK (wynika ze skrętu)
Kierunek nie jest osobnym wyborem — jest konsekwencją skrętu.

K→ — wynik S+

K← — wynik S−

K↻ — wynik S↑

K↺ — wynik S↓

Kφ — wynik S0

Walidacja: zgodność ze sznurem gipu.

🧭 3. DROGA (wynika z kierunku)
Droga to przebieg po torusie/Möbiusie.

D0 — prosta

D1 — jedna pętla

D2 — dwie pętle

DM — przejście Möbiusa

DT — przejście torusa

DW — przejście warstwy

Walidacja: TIMDER pilnuje dynamiki.

🪢 4. BRZEG (wynika z drogi)
B0 — otwarty

B1 — sklejony

BM — Möbius

BT — torus

Walidacja: węzły brzegowe gipu.

📏 5. SZEROKOŚĆ (wynika z brzegu)
W0 — stała

W± — zmienna

Wφ — minimalna

WM — Möbius

WT — torus

Walidacja: TIMDER pilnuje φ.

🧱 6. WARSTWA (wynika z szerokości)
L1 — jedna

L2 — dwie

LM — Möbius

LT — torus

Walidacja: przejścia warstw gipu.

🔗 7. RELACJE (wynikają z warstwy)
R= — równoległe

R× — przecinające

R⊕ — sprzężone

R⊗ — rezonans

R0 — niezależne

Walidacja: TIMDER + GIPU pilnują odległości.

🔥 8. KOMPresor (logika działania)
Bajt → stan topologiczny

Stan wpada do klasy skrętu

Kierunek, droga, brzeg, szerokość, warstwa, relacje wynikają automatycznie

Kompresor zbija równoważne stany

Walidacja TIMDER + GIPU sprawdza poprawność

Jeśli poprawny → kompresja

Jeśli nie → stan zostaje w pełnej postaci
