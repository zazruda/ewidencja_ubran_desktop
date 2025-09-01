Ewidencja Ubrań ZAZ — Desktop (Tkinter + SQLite)
=================================================

Opis
----
Lekka, prosta aplikacja desktopowa do ewidencji ubrań roboczych dla jednego komputera.
- GUI: Tkinter (wbudowany w Pythona)
- Baza: SQLite (plik tworzy się w: %USERPROFILE%/EwidencjaUbran/ewidencja.db)

Instalacja (Windows)
--------------------
1) Zainstaluj Python 3.11+ z https://python.org i zaznacz "Add Python to PATH".
2) Rozpakuj paczkę, w konsoli w folderze projektu wykonaj:
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
3) Uruchom:
   python app.py

Pakowanie do EXE (PyInstaller)
------------------------------
Po aktywacji venv:
   pip install pyinstaller
   pyinstaller --noconsole --onefile --name EwidencjaUbran app.py

Powstanie plik dist/EwidencjaUbran.exe. Pierwsze uruchomienie utworzy bazę w katalogu domowym użytkownika.

Funkcje
-------
- Pracownicy: dodawanie i przegląd.
- Ubrania: dodawanie i przyjęcia na stan (z zapisem ruchu).
- Wydania: wydanie po numerze ewidencyjnym, walidacja stanu, lista otwartych wydań.
- Zwrot: z listy otwartych wydań, automatyczna aktualizacja stanu i ruch "Zwrot".
- Stany i braki: widok zapasów + filtr na braki, eksport CSV.

Import startowy (opcjonalnie)
-----------------------------
Przygotuj dane w CSV zgodnie z szablonami w folderze templates.
W przyszłości można dodać guzik "Import CSV" — baza jest już gotowa na takie operacje.

Backup
------
Kopia zapasowa to po prostu skopiowanie pliku bazy:
%USERPROFILE%/EwidencjaUbran/ewidencja.db

Uwaga
-----
To podstawowy MVP. Rozszerzenia możliwe:
- role użytkowników (lokalne loginy),
- kody QR/skanery (wklejanie numeru ewidencyjnego już działa),
- edycja/archiwizacja rekordów,
- raporty PDF,
- druk etykiet.