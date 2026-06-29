MODEL_PC_MEMORY:

    MEMORY_CORE:
        typ: RAM + struktura sznurkowa
        rola: przechowywanie pełnych stanów topologicznych i ich projekcji

        jednostka_zapisu:
            NODE256:
                skręt: S
                kierunek: K
                droga: D
                brzeg: B
                szerokość: W
                warstwa: L
                relacje: R

        format_zapisu:
            - zapis liniowy: kolejność węzłów
            - zapis warstwowy: grupowanie po L
            - zapis brzegowy: grupowanie po B
            - zapis relacyjny: macierz R

        LUT256:
            - indeks z CPU (S,K)
            - zwraca pełny NODE256
            - modyfikowalna przez GIPU/TIMDR

        ROPE256:
            - lista NODE256 w kolejności czasowej
            - relacje_globalne:
                * odległości
                * sprzężenia
                * rezonanse
                * przejścia warstw
            - walidacja_globalna:
                * zgodność skrętu
                * zgodność kierunku
                * spójność przebiegu
