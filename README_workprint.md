\## Uruchomienie projektu



```bash

docker compose up --build







\## Testy



Projekt zawiera testy backendu FastAPI oraz frontendu Django.



\### Testy backendu



Testy backendu obejmują m.in.:



\- mechanizm haszowania haseł,

\- generowanie i dekodowanie tokenów JWT,

\- walidację schematów Pydantic,

\- endpoint `/health`,

\- endpointy użytkowników,

\- endpointy sal,

\- endpointy wyposażenia,

\- endpointy rezerwacji,

\- generowanie raportu CSV.



Uruchomienie testów backendu:



```bash

docker compose --profile tests run --rm backend-tests

