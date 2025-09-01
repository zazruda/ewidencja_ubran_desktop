Ewidencja Ubrań ZAZ — Desktop (Tkinter + SQLite)
=================================================

Opis
----
Lekka, prosta aplikacja desktopowa do ewidencji ubrań roboczych dla jednego komputera.
- GUI: Tkinter (wbudowany w Pythona)
- Baza: SQLite (plik tworzy się w: %USERPROFILE%/EwidencjaUbran/ewidencja.db)

Instalacja (Windows)
--------------------
1) Zainstaluj Python 3.11+ z https://python.org i zaznacz „Add Python to PATH”.
2) W katalogu projektu wykonaj:
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
3) Uruchom aplikację:
   python app.py

Pakowanie do EXE (PyInstaller)
------------------------------
Po aktywacji venv:
   pip install pyinstaller
   pyinstaller --noconsole --onefile --name EwidencjaUbran --add-data "templates;templates" app.py

Powstanie plik dist/EwidencjaUbran.exe. Pierwsze uruchomienie utworzy bazę w katalogu domowym użytkownika.

Funkcje
-------
- Pracownicy: dodawanie, przegląd, eksport CSV, import CSV.
- Ubrania: dodawanie, przyjęcia na stan (z zapisem ruchu), eksport/import CSV.
- Wydania/Zwroty: wydanie po numerze ewidencyjnym, walidacja stanu, planowana data zwrotu, lista otwartych wydań, zwrot z automatycznym zapisem ruchu.
- Stany i braki: widok zapasów z filtrem na braki i wyszukiwarką, eksport CSV, raport PDF, backup DB.
- Ruchy: zakładka z historią ruchów (Przyjęcie/Wydanie/Zwrot) z filtrami (typ, zakres dat, szukaj) i eksportem CSV.
- Sortowanie: wszystkie tabele mają klikalne nagłówki do sortowania.

Import/Export
-------------
- Szablony CSV znajdują się w folderze `templates/`.
- Import Pracowników: kolumny `name,department,position,active,email,phone` (wartości aktywne: 1/tak/true/yes).
- Import Ubrań: kolumny `name,type,size,color,inv_number,min_stock,stock,location,active`.
  - Jeżeli `inv_number` istnieje, import traktowany jest jako przyjęcie na istniejący towar (stock +=). Dodawany jest wpis w „Ruchach”.
- Eksporty CSV dostępne są z poziomu odpowiednich zakładek.

Backup
------
Kopia zapasowa to skopiowanie pliku bazy: `%USERPROFILE%/EwidencjaUbran/ewidencja.db`.
W zakładce „Stany i braki” jest przycisk „Backup DB”, który zapisuje kopię do pliku `backup_ewidencja_YYYYMMDD_HHMMSS.db` w katalogu aplikacji.

Raport PDF
----------
W „Stanach i braki” dostępny jest przycisk „Raport PDF” generujący `raport_stany.pdf` (wymaga `reportlab`).
Instalacja: `pip install reportlab`.

Uwagi techniczne
----------------
- Operacje wydania/zwrotu/przyjęcia są wykonywane w transakcjach (spójność danych).
- Dodano indeksy przyspieszające typowe widoki i filtry.
- Plik logów: `%USERPROFILE%/EwidencjaUbran/app.log`.

Uwaga
-----
To nadal MVP. Potencjalne rozszerzenia:
- Role użytkowników (lokalne loginy),
- Kody QR/skanery (wklejanie numeru ewidencyjnego już działa),
- Edycja/archiwizacja rekordów,
- Druk etykiet.
