# System Rezerwacji Sal

System Rezerwacji Sal to aplikacja webowa umożliwiająca zarządzanie salami dydaktycznymi, wyposażeniem oraz rezerwacjami w środowisku uczelnianym. Projekt został przygotowany jako aplikacja trójwarstwowa, składająca się z frontendu Django, backendu FastAPI oraz bazy danych SQL Server.

Projekt powstał w ramach zaliczenia przedmiotu **Systemy szkieletowe**.

## Autorzy

- Karol Kozik
- Adrian Krzywokulski

## Cel projektu

Celem projektu jest stworzenie aplikacji webowej pozwalającej na rezerwację sal na uczelni. System umożliwia użytkownikom przeglądanie sal, sprawdzanie ich dostępności, tworzenie rezerwacji, anulowanie rezerwacji oraz przeglądanie danych zależnie od przypisanej roli użytkownika.

Aplikacja została zaprojektowana jako alternatywa dla tradycyjnych, papierowych systemów rezerwacji sal, które są podatne na błędy, trudne w archiwizacji i nie pozwalają na szybkie sprawdzenie dostępności pomieszczeń.

## Najważniejsze funkcje

- rejestracja i logowanie użytkowników,
- uwierzytelnianie z użyciem tokenów JWT,
- obsługa ról użytkowników,
- lista sal dydaktycznych,
- wyszukiwanie sal według kryteriów,
- zarządzanie salami przez administratora,
- zarządzanie wyposażeniem sal,
- przypisywanie wyposażenia do sal,
- tworzenie rezerwacji,
- sprawdzanie konfliktów terminów,
- anulowanie rezerwacji,
- automatyczna aktualizacja statusów rezerwacji,
- generowanie raportów CSV/PDF,
- monitoring zdrowia aplikacji,
- dashboard prezentujący stan systemu,
- testy jednostkowe i integracyjne backendu,
- testy widoków frontendu Django,
- konteneryzacja z użyciem Docker Compose.

## Technologie

### Backend

- Python 3.9.13
- FastAPI
- Uvicorn
- SQLAlchemy
- Pydantic
- pyodbc
- python-jose
- passlib / bcrypt
- APScheduler
- ReportLab
- pytest
- pytest-cov

### Frontend

- Python 3.9.13
- Django
- HTML
- CSS
- TailwindCSS
- JavaScript
- Fetch API
- FullCalendar

### Baza danych

- Microsoft SQL Server
- SQLAlchemy ORM
- ODBC Driver for SQL Server

### Konteneryzacja i uruchamianie

- Docker
- Docker Compose

## Architektura systemu

Aplikacja została zaprojektowana w architekturze trójwarstwowej:

```text
Użytkownik / przeglądarka
        |
        v
Frontend Django
        |
        v
Backend FastAPI REST API
        |
        v
SQL Server
```

### Frontend

Frontend został przygotowany w Django. Odpowiada za renderowanie stron HTML, obsługę formularzy, wyświetlanie kalendarza rezerwacji oraz komunikację z backendem FastAPI.

Przykładowe widoki frontendu:

- strona główna,
- logowanie,
- rejestracja,
- lista sal,
- wyszukiwarka sal,
- formularz rezerwacji,
- moje rezerwacje,
- wszystkie rezerwacje,
- zarządzanie salami,
- zarządzanie wyposażeniem,
- raporty,
- dashboard zdrowia systemu.

### Backend

Backend został wykonany w FastAPI. Udostępnia REST API odpowiedzialne za logikę biznesową aplikacji.

Główne routery backendu:

```text
/users
/rooms
/equipment
/room-equipment
/reservations
/reports
/health
```

Backend obsługuje m.in.:

- użytkowników,
- uwierzytelnianie,
- role i autoryzację,
- sale,
- wyposażenie,
- rezerwacje,
- raporty,
- monitoring zdrowia systemu,
- scheduler aktualizujący statusy rezerwacji.

### Baza danych

Baza danych przechowuje informacje o użytkownikach, rolach, salach, budynkach, typach sal, dostępności, wyposażeniu oraz rezerwacjach.

Najważniejsze tabele:

```text
Users
Roles
Rooms
Buildings
RoomTypes
Accessibility
Equipment
Room_Equipment
Reservations
ReservationStatuses
```

Najważniejsze relacje:

- użytkownik może posiadać wiele rezerwacji,
- sala może posiadać wiele rezerwacji,
- sala może mieć wiele elementów wyposażenia,
- wyposażenie może występować w wielu salach,
- użytkownik posiada jedną rolę,
- sala jest powiązana z budynkiem, typem sali i statusem dostępności.

## Role użytkowników

System wykorzystuje role użytkowników, które decydują o dostępie do funkcji aplikacji.

Przykładowy podział:

- student / zwykły użytkownik,
- nauczyciel / prowadzący,
- administrator.

Administrator posiada dostęp do funkcji zarządzania salami, wyposażeniem, raportami oraz przeliczania statusów rezerwacji.

## Autoryzacja i bezpieczeństwo

Autoryzacja w backendzie opiera się na tokenach JWT. Hasła użytkowników są przechowywane w formie zahashowanej.

Klucz JWT nie powinien być przechowywany bezpośrednio w kodzie źródłowym. W projekcie należy używać zmiennej środowiskowej:

```env
SECRET_KEY=...
```

Do wygenerowania losowego klucza można użyć polecenia:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Plik `.env` nie powinien być dodawany do repozytorium. W repozytorium powinien znajduje się wyłącznie plik `.envexample`.

## Konfiguracja środowiska

Przed uruchomieniem projektu należy utworzyć plik `.env` w głównym katalogu projektu.

Przykład:

```env
SQLSERVER_DB=SystemRezerwacjiSal
SQLSERVER_USER=sa
SQLSERVER_PASSWORD=change_me
SQLSERVER_HOST=db
SQLSERVER_PORT=1433

BACKEND_URL=http://backend:8000

SECRET_KEY=change_me_generate_random_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Przykładowy plik `.envexample` może zostać umieszczony w repozytorium, natomiast właściwy plik `.env` powinien pozostać lokalny.

## Uruchomienie aplikacji przez Docker

Aby uruchomić aplikację, należy wykonać:

```bash
docker compose up --build
```

Po uruchomieniu aplikacja będzie dostępna pod adresami:

```text
Frontend Django:
http://localhost:8080

Backend FastAPI:
http://localhost:8000

Dokumentacja Swagger:
http://localhost:8000/docs

Healthcheck backendu:
http://localhost:8000/health

Dashboard zdrowia systemu:
http://localhost:8080/system-health/
```

## Podstawowe komendy Docker

Uruchomienie projektu:

```bash
docker compose up --build
```

Uruchomienie w tle:

```bash
docker compose up -d --build
```

Zatrzymanie kontenerów:

```bash
docker compose down
```

Zatrzymanie kontenerów i usunięcie wolumenów:

```bash
docker compose down -v
```

Uwaga: polecenie `docker compose down -v` usuwa dane zapisane w wolumenie SQL Servera.

Podgląd logów:

```bash
docker compose logs
```

Podgląd logów backendu:

```bash
docker compose logs backend
```

Podgląd logów frontendu:

```bash
docker compose logs frontend
```

## Testy

Projekt zawiera testy jednostkowe oraz integracyjne backendu FastAPI, a także testy widoków frontendu Django.

### Testy backendu

Testy backendu obejmują m.in.:

- haszowanie i weryfikację haseł,
- generowanie i dekodowanie tokenów JWT,
- walidację schematów Pydantic,
- endpoint główny `/`,
- endpoint `/health`,
- endpointy użytkowników,
- endpointy sal,
- endpointy wyposażenia,
- endpointy rezerwacji,
- wykrywanie konfliktów rezerwacji,
- generowanie raportu CSV.

Uruchomienie testów backendu:

```bash
docker compose --profile tests run --rm backend-tests
```

Przykładowy wynik:

```text
19 passed, 11 warnings
TOTAL coverage: 72%
```

### Testy frontendu

Testy frontendu Django obejmują m.in.:

- sprawdzenie, czy strona główna zwraca kod 200,
- sprawdzenie, czy strona logowania działa,
- sprawdzenie, czy formularz logowania jest renderowany,
- sprawdzenie, czy widok listy sal działa,
- sprawdzenie dodatkowych widoków aplikacji.

Uruchomienie testów frontendu:

```bash
docker compose --profile tests run --rm frontend-tests
```

Przykładowy wynik:

```text
7 passed
```

## Monitoring zdrowia systemu

Projekt zawiera mechanizm monitoringu zdrowia aplikacji.

Backend udostępnia endpoint:

```text
GET /health
```

Endpoint zwraca m.in.:

- status backendu,
- status połączenia z bazą danych,
- status schedulera,
- liczbę użytkowników,
- liczbę sal,
- liczbę rezerwacji,
- liczbę aktywnych rezerwacji,
- czas wykonania sprawdzenia,
- czas odpowiedzi.

Frontend zawiera dashboard dostępny pod adresem:

```text
http://localhost:8080/system-health/
```

Dashboard prezentuje stan systemu w czytelnej formie i może być używany do szybkiej kontroli działania aplikacji.

## Scheduler rezerwacji

Backend korzysta z APScheduler do automatycznej aktualizacji statusów rezerwacji.

Mechanizm cyklicznie sprawdza, czy istnieją aktywne rezerwacje, których termin zakończenia już minął. Takie rezerwacje otrzymują status zakończonych.

Dodatkowo dostępny jest ręczny endpoint administracyjny:

```text
POST /reservations/_recalc
```

Pozwala on wymusić przeliczenie statusów rezerwacji.

## Raporty

System umożliwia generowanie raportów dotyczących rezerwacji.

Dostępne są m.in.:

```text
GET /reports/reservations.csv
GET /reports/reports/reservations.pdf
```

Raporty są przeznaczone dla użytkowników z odpowiednimi uprawnieniami, w szczególności administratora.

## Struktura projektu

Przykładowa struktura katalogów:

```text
SRS_Kozik_Krzywokulski_JEE/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── auth.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── scheduler.py
│   │   └── routers/
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .dockerignore
│
├── frontend/
│   ├── manage.py
│   ├── ui/
│   ├── web/
│   ├── templates/
│   ├── static/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .dockerignore
│
├── database/
│   └── ...
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## Import starej bazy danych do Dockera

Jeżeli projekt korzysta z backupu SQL Server, można przywrócić bazę do kontenera SQL Server.

Przykładowy przebieg:

```bash
docker compose up -d db
docker cp "SystemRezerwacjiSal.bak" room_reservation_db:/var/opt/mssql/backup/SystemRezerwacjiSal.bak
```

Następnie w `sqlcmd`:

```sql
RESTORE FILELISTONLY
FROM DISK = '/var/opt/mssql/backup/SystemRezerwacjiSal.bak';
GO
```

Po sprawdzeniu logicznych nazw plików:

```sql
RESTORE DATABASE SystemRezerwacjiSal
FROM DISK = '/var/opt/mssql/backup/SystemRezerwacjiSal.bak'
WITH
MOVE 'SystemRezerwacjiSal' TO '/var/opt/mssql/data/SystemRezerwacjiSal.mdf',
MOVE 'SystemRezerwacjiSal_log' TO '/var/opt/mssql/data/SystemRezerwacjiSal_log.ldf',
REPLACE;
GO
```

Nazwy logiczne w sekcji `MOVE` należy dopasować do wyniku `RESTORE FILELISTONLY`.

## Dokumentacja API

Po uruchomieniu backendu dokumentacja API jest dostępna pod adresem:

```text
http://localhost:8000/docs
```

FastAPI automatycznie generuje dokumentację Swagger na podstawie zdefiniowanych endpointów i schematów Pydantic.

## Znane ograniczenia

Aktualna wersja projektu jest wersją zaliczeniową i demonstracyjną. Znane ograniczenia:

- brak pełnej integracji z rzeczywistym systemem uczelnianym,
- brak produkcyjnej konfiguracji HTTPS,
- brak mechanizmu potwierdzania rejestracji przez e-mail,
- ograniczony mechanizm weryfikacji użytkowników,
- część elementów interfejsu wymaga dalszej optymalizacji UX,
- brak pełnej paginacji w wybranych widokach,
- scheduler aplikacyjny nie jest rozwiązaniem rekomendowanym dla produkcji,
- środowisko Docker jest przygotowane głównie na potrzeby uruchomienia i prezentacji projektu.

## Dalszy rozwój

Możliwe kierunki rozwoju projektu:

- integracja z systemem kont uczelnianych,
- potwierdzanie rejestracji przez e-mail,
- powiadomienia e-mail o rezerwacjach,
- wdrożenie HTTPS,
- rozbudowa panelu administratora,
- pełna paginacja list,
- poprawa spójności interfejsu użytkownika,
- integracja z planem zajęć uczelni,
- rozbudowa raportów,
- wdrożenie produkcyjnego monitoringu, np. Prometheus i Grafana,
- migracja do nowszej wersji Pythona,
- przeniesienie mechanizmu aktualizacji statusów rezerwacji do bardziej niezawodnego schedulera systemowego lub mechanizmu bazodanowego.

## Bibliografia i inspiracje

Projekt był inspirowany istniejącymi systemami rezerwacji sal oraz rozwiązaniami kalendarzowymi, takimi jak:

- CollegeNET / 25Live,
- systemy rezerwacji sal University of Michigan,
- Microsoft Outlook Room Finder,
- USOS System Rezerwacji Sal,
- rozwiązania OPTeam,
- monday.com.

Szczegółowa bibliografia znajduje się w dokumentacji projektowej.
