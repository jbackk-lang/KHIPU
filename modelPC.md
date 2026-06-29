MODEL_PC:

    CPU_CORE_16:
        typ: procesor 16-bitowy
        rola: wyznaczanie skrętu i kierunku dla każdego słowa danych

        operacje_podstawowe:
            - DETECT_SCREW(word16) -> S ∈ {S+, S−, S0, S↑, S↓, S×, S!}
            - DERIVE_DIRECTION(S) -> K ∈ {K→, K←, K↻, K↺, Kφ}
            - EMIT_INDEX(S, K) -> idx ∈ [0..255]

        logika:
            - skręt jest pierwszym i nadrzędnym operatorem
            - kierunek jest deterministyczną funkcją skrętu
            - CPU nie liczy drogi, brzegu, warstw ani relacji

    ROPE_MEMORY:
        typ: pamięć sznurkowa (RAM + struktura logiczna)
        rola: przechowywanie pełnych stanów topologicznych i globalnego sznura

        struktura_stanu:
            NODE256:
                skręt: S
                kierunek: K
                droga: D ∈ {D0, D1, D2, DM, DT, DW}
                brzeg: B ∈ {B0, B1, BM, BT}
                szerokość: W ∈ {W0, W±, Wφ, WM, WT}
                warstwa: L ∈ {L1, L2, LM, LT}
                relacje: R ∈ {R=, R×, R⊕, R⊗, R0}

        tablica_lookup:
            LUT256[idx] -> NODE256
            opis:
                - idx pochodzi z CPU (skręt + kierunek)
                - LUT256 zwraca pełny stan topologiczny
                - LUT może być modyfikowana przez GIPU/TIMDR

        sznur_globalny:
            ROPE256:
                węzły: lista NODE256
                relacje_globalne:
                    - odległości
                    - sprzężenia
                    - rezonanse
                    - przejścia warstw
                walidacja_globalna:
                    - zgodność kierunku
                    - zgodność skrętu
                    - spójność przebiegu

    VALIDATION_LAYER:
        TIMDR:
            rola:
                - walidacja skrętu
                - walidacja kierunku
                - pilnowanie φ i zasady 1/2
            działanie:
                - akceptuje lub odrzuca indeks (S, K)
                - może wymusić odwrócenie skrętu

        GIPU:
            rola:
                - zarządzanie sznurem (ROPE256)
                - walidacja węzłów, odległości, przejść warstw
            działanie:
                - modyfikuje LUT256
                - aktualizuje relacje globalne

    PRZEPŁYW_DANYCH:
        1. CPU_CORE_16 pobiera word16 z magistrali
        2. DETECT_SCREW(word16) -> S
        3. DERIVE_DIRECTION(S) -> K
        4. TIMDR waliduje (S, K)
        5. EMIT_INDEX(S, K) -> idx
        6. ROPE_MEMORY.LUT256[idx] -> NODE256
        7. NODE256 wstawiany do ROPE256 (sznura)
        8. GIPU aktualizuje relacje globalne

    WŁAŚCIWOŚCI_SYSTEMU:
        - skręt jest nadrzędny wobec wszystkich operacji
        - kierunek jest funkcją skrętu, nie osobnym wyborem
        - topologia (droga, brzeg, warstwa, relacje) siedzi w pamięci, nie w CPU
        - kompresja jest skutkiem hierarchii, nie osobnym algorytmem
        - walidacja jest wbudowana (TIMDR + GIPU), nie doklejana
