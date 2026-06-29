MODEL_PC_VISUAL:

    VISUAL_ENGINE:
        rola: tworzenie obrazu na podstawie sznura

        tryby:
            - PROJECTION_2D:
                * skręt -> kolor
                * kierunek -> wektor
                * droga -> kształt
                * brzeg -> obramowanie
                * warstwa -> głębokość
                * relacje -> linie łączące

            - PROJECTION_3D:
                * skręt -> rotacja
                * kierunek -> orientacja
                * droga -> trajektoria
                * brzeg -> powierzchnia
                * warstwa -> poziom
                * relacje -> siatka połączeń

        wejście:
            - ROPE256 (sznur)
            - LUT256 (stany)

        wyjście:
            - FRAME:
                * obraz 2D/3D
                * mapa skrętu
                * mapa kierunku
                * mapa warstw
                * mapa relacji

    FRAME_BUFFER:
        typ: pamięć podręczna obrazu
        rola:
            - przechowywanie ostatnich N klatek
            - umożliwienie analizy zmian sznura
