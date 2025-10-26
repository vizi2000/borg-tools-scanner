
    # Borg.tools_scan

    **Ścieżka:** `/Users/wojciechwiesner/ai/Borg.tools_scan`  
    **Języki:** python  
    **Ostatni commit:** brak  
    **Commity/gałęzie:** 0/0  

    ## Etap i ocena
    - **Etap:** idea
    - **Value:** 0/10
    - **Risk:** 6/10
    - **Priority:** 0/20
    - **Fundamentalne błędy:** brak README, brak testów, brak CI, brak LICENSE

    ## Fakty
    - README: NIE
    - LICENSE: NIE
    - Testy: NIE
    - CI: NIE
    - TODO/FIXME (próbka):
    (brak)

    ### Zależności (skrót)
    - Python: (brak)
    - Node: (brak)

    ## Umiejętności / tagi
    pandas?, poetry/pip, pytest, python

    ## AI Acceleration – najlepsze kroki
    - Użyj LLM do wygenerowania szkielety testów jednostkowych dla kluczowych modułów (max 5 plików).
- Wygeneruj minimalny workflow CI (pytest/jest + lint) i dodaj badge do README.
- Poproś LLM o wygenerowanie README z sekcjami: quickstart, scripts, architektura, TODO.

    ## TODO – na dziś (45–90 min)
    - Dodaj README: cel, instalacja, uruchomienie, testy, struktura.
- Dodaj minimalne testy jednostkowe (1-2 pliki) dla krytycznych funkcji.
- Dodaj prosty workflow CI (lint + test).

    ## TODO – następne (1–2 dni)
    - Dodaj LICENSE (MIT/Apache-2.0).
- Zamknij pętlę E2E: działający przykład od wejścia do wyniku.

    **Uzasadnienie:** Zadania priorytetyzowane pod największą dźwignię w 90 minut, najpierw błędy fundamentalne.

    ---

    ## Opis projektu (LLM)
    Borg.tools_scan to Pythonowy projekt służący do skanowania i przetwarzania danych (prawdopodobnie związany z monitoringiem systemowym), generujący raporty w formatach CSV/JSON. Brak dokumentacji utrudnia precyzyjne określenie funkcjonalności.

    ## Deklarowane funkcje vs. zastane w kodzie (LLM)
    Brak jakichkolwiek deklaracji w dokumentacji (README, LICENSE nie istnieją). Kod źródłowy składa się z pojedynczych skryptów Pythona z licznymi backupami, bez struktury projektu.

    ## Struktura projektu (snapshot)
    Płaska struktura z 9 plikami w katalogu głównym: 5 skryptów Pythona (w tym backupowe), 2 pliki markdown, 2 pliki danych. Brak modularności, __pycache__ świadczy o wykonaniu kodu bez środowiska wirtualnego.

    ## Best practices – checklist
    (brak / LLM wyłączony)

    ## "Vibe" kodowania – notatki
    Chaotyczna organizacja (liczne pliki .bak, _backup), brak spójności nazewniczej. Kod prawdopodobnie niskiej jakości (brak testów, brak obsługi błędów). UX nieistniejący - brak interfejsu użytkownika.

    ---

    ## Problem jaki rozwiązuje projekt (LLM)
    Automatyzacja przetwarzania danych technicznych (prawdopodobnie logów/systemów) dla administratorów IT. Generowanie raportów dashboardowych w formie plików CSV/JSON.

    ## Potencjał monetyzacji (LLM)
    Brak obecnie. Potencjalnie: integracja z komercyjnymi narzędziami monitorującymi, sprzedaż raportów analitycznych lub SaaS z dashboardem webowym.

    ## Realna lista TODO do uruchomienia MVP (LLM)
    - Stworzenie podstawowej dokumentacji (README.md)
- Usunięcie zbędnych plików backupowych
- Konsolidacja funkcjonalności w jednym module
- Dodanie obsługi błędów
- Utworzenie licencji projektu
- Dodanie przykładowych danych testowych
- Implementacja podstawowej logiki CLI
- Uporządkowanie zależności (requirements.txt)

    ## Frontend TODO list (LLM)
    (brak / LLM wyłączony)

    ## Portfolio suitability (LLM)
    - **Nadaje się do portfolio:** NIE

    ## Portfolio description (świadectwo umiejętności) (LLM)
    (brak / LLM wyłączony)

    ---

    ## Podobne Projekty (LLM)
    (brak)
