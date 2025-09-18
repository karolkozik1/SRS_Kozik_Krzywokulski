from django.shortcuts import render
from django.conf import settings
import requests

def _ctx(request, **extra):
    """
    Kontekst wspólny dla szablonów.
    Dajemy oba klucze (API_BASE i API_BASE_URL), żeby nie trzeba było nic
    zmieniać w istniejących szablonach/JS.
    """
    api = getattr(settings, "API_BASE", "http://127.0.0.1:8000")
    ctx = {
        "API_BASE": api,
        "API_BASE_URL": api,
        "redirect_after_login": request.GET.get("next", "/"),
    }
    ctx.update(extra)
    return ctx


def home(request):
    return render(request, "home.html", _ctx(request))


def login_page(request):
    return render(request, "login.html", _ctx(request))


def register_page(request):
    return render(request, "register.html", _ctx(request))

def reserve_page(request):
    return render(request, "reserve.html", _ctx(request))

def rooms_page(request):
    return render(request, "rooms.html", _ctx(request))

def rooms_admin_page(request):
    return render(request, "rooms_admin.html", _ctx(request))

def rooms_eq_admin_page(request):
    return render(request, "rooms_eq_admin.html", _ctx(request))

def equipments_manage_page(request):
    return render(request, "equipments.html", _ctx(request))

# def rooms_search_page(request):
#     return render(request, "rooms_search.html", _ctx(request))

def rooms_search_page(request):
    ctx = _ctx(request)
    if request.method == "POST":
        data = request.POST.copy()
        equipment_ids = request.POST.getlist("equipment_ids")
        payload = {
            "date": data.get("date"),
            "start_hhmm": data.get("start_hhmm"),
            "end_hhmm": data.get("end_hhmm"),
            "building_id": int(data["building_id"]) if data.get("building_id") else None,
            "floor": int(data["floor"]) if data.get("floor") else None,
            "min_capacity": int(data["min_capacity"]) if data.get("min_capacity") else None,
            "equipment_ids": [int(e) for e in equipment_ids] if equipment_ids else None
        }
        try:
            r = requests.post(f"{ctx['API_BASE']}/rooms/search", json=payload)
            if r.status_code == 200:
                ctx["results"] = r.json()
            else:
                ctx["error"] = f"Błąd API: {r.status_code} – {r.text}"
        except Exception as e:
            ctx["error"] = f"Błąd połączenia z API: {e}"
    return render(request, "rooms_search.html", ctx)

def my_reservations_page(request):
    return render(request, "my_reservations.html", _ctx(request))

def all_reservations_page(request):
    return render(request, "all_reservations.html", _ctx(request))

def reservations_list_page(request):
    return render(request, "reservations_list.html", _ctx(request))

def reports_page(request):
    return render(request, "reports.html", _ctx(request))
