COMPRESSOR256:
    wejście: NODE256
    operacje:
        - klasyfikacja po skręcie
        - redukcja po kierunku
        - redukcja po drodze
        - redukcja po brzegu
        - redukcja po szerokości
        - redukcja po warstwie
        - redukcja po relacjach
    walidacja:
        - TIMDER: skręt, kierunek, φ
        - GIPU: sznur, węzły, odległości
    wyjście:
        - stan skompresowany (NODE256)
        - lub stan pełny (jeśli walidacja odrzuci)
