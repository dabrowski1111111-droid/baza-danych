"""
==========================================================
  EKSPORT DANYCH UŻYTKOWNIKÓW
  
  Ten moduł automatycznie zapisuje dane zarejestrowanych
  użytkowników do pliku 'zarejestrowani_uzytkownicy.txt'
  
  Wykorzystuje moduł 'time' do:
    - znaczników czasowych rejestracji
    - obliczania czasu od rejestracji
    - formatowania dat i godzin
    - generowania raportów z przedziałami czasowymi
==========================================================
"""

import time
import os


# Ścieżka do pliku z danymi użytkowników
USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zarejestrowani_uzytkownicy.txt")
USERS_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rejestracje_log.txt")


def save_user_to_file(username, email, role, user_id):
    """
    Zapisuje dane nowo zarejestrowanego użytkownika do pliku tekstowego.
    
    Wywoływane automatycznie po udanej rejestracji w auth.py.
    
    Args:
        username: Nazwa użytkownika
        email: Adres email
        role: Rola (admin/user)
        user_id: ID użytkownika w bazie danych
    """
    timestamp = time.time()
    data_rejestracji = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
    dzien_tygodnia = time.strftime("%A", time.localtime(timestamp))
    
    # Mapowanie dni tygodnia na polski
    dni_pl = {
        "Monday": "Poniedziałek",
        "Tuesday": "Wtorek",
        "Wednesday": "Środa",
        "Thursday": "Czwartek",
        "Friday": "Piątek",
        "Saturday": "Sobota",
        "Sunday": "Niedziela",
    }
    dzien_pl = dni_pl.get(dzien_tygodnia, dzien_tygodnia)
    
    # Sprawdź czy plik istnieje - jeśli nie, dodaj nagłówek
    plik_istnieje = os.path.exists(USERS_FILE)
    
    with open(USERS_FILE, "a", encoding="utf-8") as f:
        if not plik_istnieje:
            # Nagłówek pliku
            f.write("╔══════════════════════════════════════════════════════════════╗\n")
            f.write("║         BAZA ZAREJESTROWANYCH UŻYTKOWNIKÓW                  ║\n")
            f.write("║         System Logowania - Python Database                  ║\n")
            f.write(f"║         Utworzono: {data_rejestracji}                        ║\n")
            f.write("╚══════════════════════════════════════════════════════════════╝\n")
            f.write("\n")
        
        # Separator między użytkownikami
        f.write("┌──────────────────────────────────────────────────────────────┐\n")
        f.write(f"│  UŻYTKOWNIK #{user_id}\n")
        f.write("├──────────────────────────────────────────────────────────────┤\n")
        f.write(f"│  ID:                  {user_id}\n")
        f.write(f"│  Nazwa użytkownika:   {username}\n")
        f.write(f"│  Email:               {email if email else 'Nie podano'}\n")
        f.write(f"│  Rola:                {role}\n")
        f.write(f"│  Data rejestracji:    {data_rejestracji}\n")
        f.write(f"│  Dzień tygodnia:      {dzien_pl}\n")
        f.write(f"│  Timestamp (Unix):    {timestamp}\n")
        f.write("└──────────────────────────────────────────────────────────────┘\n")
        f.write("\n")
    
    # Zapisz też do logu w formacie CSV
    _save_to_log(username, email, role, user_id, timestamp)
    
    return True


def _save_to_log(username, email, role, user_id, timestamp):
    """
    Zapisuje krótki wpis do pliku logu rejestracji (format CSV).
    """
    data_rejestracji = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
    
    log_istnieje = os.path.exists(USERS_LOG_FILE)
    
    with open(USERS_LOG_FILE, "a", encoding="utf-8") as f:
        if not log_istnieje:
            f.write("# LOG REJESTRACJI UŻYTKOWNIKÓW\n")
            f.write(f"# Utworzono: {data_rejestracji}\n")
            f.write("# Format: ID | Nazwa | Email | Rola | Data rejestracji | Timestamp\n")
            f.write("#" + "=" * 80 + "\n")
        
        f.write(f"{user_id} | {username} | {email or 'brak'} | {role} | {data_rejestracji} | {timestamp}\n")


def read_users_from_file():
    """
    Odczytuje i wyświetla zawartość pliku z zarejestrowanymi użytkownikami.
    
    Returns:
        str: Zawartość pliku lub komunikat o braku pliku
    """
    if not os.path.exists(USERS_FILE):
        return "Plik z użytkownikami nie istnieje. Zarejestruj pierwszego użytkownika!"
    
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    return content


def count_registered_users():
    """
    Zlicza liczbę zarejestrowanych użytkowników na podstawie pliku logu.
    
    Returns:
        int: Liczba zarejestrowanych użytkowników
    """
    if not os.path.exists(USERS_LOG_FILE):
        return 0
    
    count = 0
    with open(USERS_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.startswith("#") and line.strip():
                count += 1
    
    return count


def get_registration_stats():
    """
    Generuje statystyki rejestracji z użyciem modułu time.
    
    Returns:
        dict: Statystyki rejestracji
    """
    if not os.path.exists(USERS_LOG_FILE):
        return {
            "total_users": 0,
            "message": "Brak danych rejestracyjnych.",
        }
    
    users = []
    with open(USERS_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.startswith("#") and line.strip():
                parts = line.strip().split(" | ")
                if len(parts) >= 6:
                    users.append({
                        "id": parts[0],
                        "username": parts[1],
                        "email": parts[2],
                        "role": parts[3],
                        "date": parts[4],
                        "timestamp": float(parts[5]),
                    })
    
    if not users:
        return {"total_users": 0, "message": "Brak zarejestrowanych użytkowników."}
    
    # Statystyki czasowe
    current_time = time.time()
    first_registration = min(u["timestamp"] for u in users)
    last_registration = max(u["timestamp"] for u in users)
    
    # Czas od pierwszej rejestracji
    time_since_first = current_time - first_registration
    days = int(time_since_first // 86400)
    hours = int((time_since_first % 86400) // 3600)
    minutes = int((time_since_first % 3600) // 60)
    
    # Czas od ostatniej rejestracji
    time_since_last = current_time - last_registration
    last_days = int(time_since_last // 86400)
    last_hours = int((time_since_last % 86400) // 3600)
    last_minutes = int((time_since_last % 3600) // 60)
    
    # Liczba adminów vs userów
    admins = sum(1 for u in users if u["role"] == "admin")
    regular = sum(1 for u in users if u["role"] == "user")
    
    # Rejestracje w ostatnich 24h
    last_24h = sum(1 for u in users if current_time - u["timestamp"] < 86400)
    
    # Rejestracje w ostatniej godzinie
    last_hour = sum(1 for u in users if current_time - u["timestamp"] < 3600)
    
    return {
        "total_users": len(users),
        "admins": admins,
        "regular_users": regular,
        "first_registration": time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(first_registration)
        ),
        "last_registration": time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(last_registration)
        ),
        "time_since_first": f"{days}d {hours}h {minutes}m",
        "time_since_last": f"{last_days}d {last_hours}h {last_minutes}m",
        "registrations_last_24h": last_24h,
        "registrations_last_hour": last_hour,
        "file_path": USERS_FILE,
        "log_path": USERS_LOG_FILE,
    }


def generate_report():
    """
    Generuje pełny raport tekstowy z danymi i statystykami.
    Wykorzystuje time do formatowania dat.
    
    Returns:
        str: Pełny raport tekstowy
    """
    stats = get_registration_stats()
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    report = []
    report.append("╔══════════════════════════════════════════════════════════════╗")
    report.append("║              RAPORT REJESTRACJI UŻYTKOWNIKÓW                ║")
    report.append(f"║              Wygenerowano: {current_time}           ║")
    report.append("╚══════════════════════════════════════════════════════════════╝")
    report.append("")
    
    if stats["total_users"] == 0:
        report.append("  Brak zarejestrowanych użytkowników.")
        return "\n".join(report)
    
    report.append(f"  📊 STATYSTYKI OGÓLNE:")
    report.append(f"  {'─' * 50}")
    report.append(f"  Łączna liczba użytkowników:   {stats['total_users']}")
    report.append(f"  Administratorzy:              {stats['admins']}")
    report.append(f"  Zwykli użytkownicy:           {stats['regular_users']}")
    report.append("")
    report.append(f"  ⏱️  DANE CZASOWE:")
    report.append(f"  {'─' * 50}")
    report.append(f"  Pierwsza rejestracja:         {stats['first_registration']}")
    report.append(f"  Ostatnia rejestracja:         {stats['last_registration']}")
    report.append(f"  Czas od pierwszej:            {stats['time_since_first']}")
    report.append(f"  Czas od ostatniej:            {stats['time_since_last']}")
    report.append("")
    report.append(f"  📈 AKTYWNOŚĆ:")
    report.append(f"  {'─' * 50}")
    report.append(f"  Rejestracje (ostatnie 24h):   {stats['registrations_last_24h']}")
    report.append(f"  Rejestracje (ostatnia godz.): {stats['registrations_last_hour']}")
    report.append("")
    report.append(f"  📂 PLIKI:")
    report.append(f"  {'─' * 50}")
    report.append(f"  Plik użytkowników:  {stats['file_path']}")
    report.append(f"  Plik logu:          {stats['log_path']}")
    report.append("")
    
    # Dodaj listę użytkowników z logu
    report.append(f"  👥 ZAREJESTROWANI UŻYTKOWNICY:")
    report.append(f"  {'─' * 50}")
    
    if os.path.exists(USERS_LOG_FILE):
        with open(USERS_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if not line.startswith("#") and line.strip():
                    parts = line.strip().split(" | ")
                    if len(parts) >= 5:
                        report.append(f"    #{parts[0]:>3} │ {parts[1]:<15} │ {parts[3]:<6} │ {parts[4]}")
    
    report.append("")
    report.append(f"  {'═' * 50}")
    report.append(f"  Koniec raportu | {current_time}")
    
    return "\n".join(report)
