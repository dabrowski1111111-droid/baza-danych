"""
==========================================================
  GŁÓWNA APLIKACJA - Interaktywna konsola bazodanowa
  z systemem logowania i panelem administracyjnym.

  Wykorzystuje moduł 'time' do:
    - wyświetlania aktualnego czasu
    - mierzenia czasu operacji
    - animacji w konsoli
    - sesji z automatycznym wygasaniem
==========================================================
"""

import time
import os
import sys
from database import Database
from auth import AuthSystem
from user_data_export import (
    read_users_from_file,
    count_registered_users,
    get_registration_stats,
    generate_report,
)


# ========================================
#  KOLORY I FORMATOWANIE KONSOLI
# ========================================

class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_slow(text, delay=0.02):
    """Wyświetla tekst z efektem pisania (używa time.sleep)."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def print_header(title):
    """Wyświetla ozdobny nagłówek."""
    width = 60
    print(f"\n{Colors.CYAN}{'═' * width}")
    print(f"║  {Colors.BOLD}{title.center(width - 6)}{Colors.END}{Colors.CYAN}  ║")
    print(f"{'═' * width}{Colors.END}")


def print_subheader(title):
    """Wyświetla mniejszy nagłówek."""
    print(f"\n{Colors.BLUE}{'─' * 50}")
    print(f"  {Colors.BOLD}{title}{Colors.END}")
    print(f"{Colors.BLUE}{'─' * 50}{Colors.END}")


def print_success(msg):
    print(f"  {Colors.GREEN}✅ {msg}{Colors.END}")


def print_error(msg):
    print(f"  {Colors.RED}❌ {msg}{Colors.END}")


def print_info(msg):
    print(f"  {Colors.YELLOW}ℹ️  {msg}{Colors.END}")


def print_time():
    """Wyświetla aktualny czas z modułu time."""
    current = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"  {Colors.DIM}🕐 {current}{Colors.END}")


def countdown(seconds, message=""):
    """Odliczanie z użyciem time.sleep."""
    for i in range(seconds, 0, -1):
        sys.stdout.write(f"\r  {Colors.YELLOW}⏳ {message} {i}s...{Colors.END}")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write(f"\r  {Colors.GREEN}✅ Gotowe!{' ' * 30}{Colors.END}\n")


def loading_animation(duration=2, message="Ładowanie"):
    """Animacja ładowania z użyciem time.sleep."""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    start = time.time()
    i = 0
    while time.time() - start < duration:
        sys.stdout.write(f"\r  {Colors.CYAN}{frames[i % len(frames)]} {message}...{Colors.END}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    sys.stdout.write(f"\r  {Colors.GREEN}✅ {message} - zakończono!{' ' * 20}{Colors.END}\n")


# ========================================
#  BANNER POWITALNY
# ========================================

def show_banner():
    """Wyświetla banner powitalny."""
    clear_screen()
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║    ██████╗  █████╗ ███████╗ █████╗                       ║
    ║    ██╔══██╗██╔══██╗╚══███╔╝██╔══██╗                      ║
    ║    ██████╔╝███████║  ███╔╝ ███████║                      ║
    ║    ██╔══██╗██╔══██║ ███╔╝  ██╔══██║                      ║
    ║    ██████╔╝██║  ██║███████╗██║  ██║                      ║
    ║    ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝                      ║
    ║                                                          ║
    ║     ██████╗  █████╗ ███╗   ██╗██╗   ██╗ ██████╗██╗  ██╗ ║
    ║     ██╔══██╗██╔══██╗████╗  ██║╚██╗ ██╔╝██╔════╝██║  ██║ ║
    ║     ██║  ██║███████║██╔██╗ ██║ ╚████╔╝ ██║     ███████║ ║
    ║     ██║  ██║██╔══██║██║╚██╗██║  ╚██╔╝  ██║     ██╔══██║ ║
    ║     ██████╔╝██║  ██║██║ ╚████║   ██║   ╚██████╗██║  ██║ ║
    ║     ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝╚═╝  ╚═╝ ║
    ║                                                          ║
    ║          🐍 Python Database System v2.0                  ║
    ║          ⏱️  Powered by: moduł time                      ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
{Colors.END}"""
    print(banner)
    print_time()
    print()


# ========================================
#  EKRAN LOGOWANIA
# ========================================

def login_screen(auth):
    """Ekran logowania / rejestracji."""
    while True:
        print_header("🔐 SYSTEM LOGOWANIA")
        print_time()
        print(f"""
  {Colors.BOLD}[1]{Colors.END} 🔑 Zaloguj się
  {Colors.BOLD}[2]{Colors.END} 📝 Zarejestruj nowe konto
  {Colors.BOLD}[3]{Colors.END} 📊 Statystyki bazy danych
  {Colors.BOLD}[4]{Colors.END} 📂 Przeglądaj plik z użytkownikami
  {Colors.BOLD}[5]{Colors.END} 🚪 Wyjdź z programu
        """)

        choice = input(f"  {Colors.CYAN}Wybierz opcję ➤ {Colors.END}").strip()

        if choice == "1":
            # Logowanie
            print_subheader("🔑 LOGOWANIE")
            username = input(f"  {Colors.YELLOW}Nazwa użytkownika: {Colors.END}").strip()
            password = input(f"  {Colors.YELLOW}Hasło: {Colors.END}").strip()

            if not username or not password:
                print_error("Nazwa użytkownika i hasło są wymagane!")
                time.sleep(1.5)
                continue

            loading_animation(1, "Weryfikowanie danych")
            result = auth.login(username, password)

            if result["success"]:
                print_success(result["message"])
                print_info(f"Rola: {result['role']}")
                print_info(f"Sesja wygasa za: {result['session_expires_in']}")
                print_info(f"Czas logowania: {result['time_elapsed']}")
                time.sleep(2)
                return result["token"]
            else:
                print_error(result["error"])
                time.sleep(2)

        elif choice == "2":
            # Rejestracja
            print_subheader("📝 REJESTRACJA NOWEGO KONTA")
            username = input(f"  {Colors.YELLOW}Nazwa użytkownika: {Colors.END}").strip()
            password = input(f"  {Colors.YELLOW}Hasło: {Colors.END}").strip()
            password2 = input(f"  {Colors.YELLOW}Powtórz hasło: {Colors.END}").strip()
            email = input(f"  {Colors.YELLOW}Email (opcjonalnie): {Colors.END}").strip()

            if password != password2:
                print_error("Hasła nie są identyczne!")
                time.sleep(1.5)
                continue

            # Pytaj o rolę (pierwszego użytkownika automatycznie jako admina)
            users = auth.list_users()
            role = "admin" if len(users) == 0 else "user"
            if len(users) == 0:
                print_info("Tworzysz pierwsze konto - otrzymasz uprawnienia administratora!")

            loading_animation(1.5, "Tworzenie konta")
            result = auth.register(username, password, email, role)

            if result["success"]:
                print_success(result["message"])
                print_info(f"Rola: {role}")
                print_info(f"Czas operacji: {result['time_elapsed']}")
            else:
                print_error(result["error"])
            time.sleep(2)

        elif choice == "3":
            # Statystyki
            print_subheader("📊 STATYSTYKI BAZY DANYCH")
            stats = auth.db.get_stats()
            for key, value in stats.items():
                print(f"  {Colors.CYAN}{key:>25}{Colors.END}: {Colors.BOLD}{value}{Colors.END}")
            input(f"\n  {Colors.DIM}Naciśnij Enter, aby kontynuować...{Colors.END}")

        elif choice == "4":
            # Przeglądanie pliku z użytkownikami
            print_subheader("📂 PLIK Z ZAREJESTROWANYMI UŻYTKOWNIKAMI")
            print_time()
            count = count_registered_users()
            print_info(f"Łączna liczba zarejestrowanych: {count}")
            print()
            content = read_users_from_file()
            print(content)
            print()

            # Opcja generowania raportu
            gen = input(f"  {Colors.YELLOW}Wygenerować pełny raport? (tak/nie): {Colors.END}").strip()
            if gen.lower() == "tak":
                loading_animation(1, "Generowanie raportu")
                report = generate_report()
                print(report)
            input(f"\n  {Colors.DIM}Naciśnij Enter, aby kontynuować...{Colors.END}")

        elif choice == "5":
            print_slow(f"\n  {Colors.CYAN}Do widzenia! 👋{Colors.END}", 0.05)
            time.sleep(1)
            sys.exit(0)

        else:
            print_error("Nieprawidłowa opcja!")
            time.sleep(1)


# ========================================
#  PANEL GŁÓWNY (po zalogowaniu)
# ========================================

def main_menu(auth, token):
    """Menu główne po zalogowaniu."""
    while True:
        session = auth.validate_session(token)
        if not session["valid"]:
            print_error(session["error"])
            time.sleep(2)
            return

        username = session["username"]
        role = session["role"]
        time_remaining = session["time_remaining"]

        print_header(f"👤 Panel użytkownika: {username}")
        print_time()
        print(f"  {Colors.DIM}Rola: {role} | Sesja wygasa za: {time_remaining}{Colors.END}")

        menu = f"""
  {Colors.BOLD}[1]{Colors.END} 📋 Zarządzanie tabelami
  {Colors.BOLD}[2]{Colors.END} 📝 Operacje na danych (CRUD)
  {Colors.BOLD}[3]{Colors.END} 👤 Mój profil
  {Colors.BOLD}[4]{Colors.END} 🔑 Zmień hasło
  {Colors.BOLD}[5]{Colors.END} 📜 Historia logowań
  {Colors.BOLD}[6]{Colors.END} 📊 Statystyki bazy danych
  {Colors.BOLD}[7]{Colors.END} 💾 Kopia zapasowa"""

        if role == "admin":
            menu += f"""
  {Colors.BOLD}[8]{Colors.END} 👥 Panel administracyjny
  {Colors.BOLD}[9]{Colors.END} 🔴 Aktywne sesje"""

        menu += f"""
  {Colors.BOLD}[0]{Colors.END} 🚪 Wyloguj się
        """
        print(menu)

        choice = input(f"  {Colors.CYAN}Wybierz opcję ➤ {Colors.END}").strip()

        if choice == "1":
            table_management(auth.db)
        elif choice == "2":
            crud_operations(auth.db)
        elif choice == "3":
            show_profile(auth, username)
        elif choice == "4":
            change_password_screen(auth, username)
        elif choice == "5":
            show_login_history(auth, username)
        elif choice == "6":
            show_stats(auth.db)
        elif choice == "7":
            backup_screen(auth.db)
        elif choice == "8" and role == "admin":
            admin_panel(auth, token)
        elif choice == "9" and role == "admin":
            show_active_sessions(auth)
        elif choice == "0":
            result = auth.logout(token)
            if result["success"]:
                print_success(result["message"])
                print_info(f"Czas sesji: {result['session_duration']}")
            time.sleep(2)
            return
        else:
            print_error("Nieprawidłowa opcja!")
            time.sleep(1)


# ========================================
#  ZARZĄDZANIE TABELAMI
# ========================================

def table_management(db):
    """Ekran zarządzania tabelami."""
    while True:
        print_subheader("📋 ZARZĄDZANIE TABELAMI")
        tables = db.list_tables()

        # Pokaż istniejące tabele (bez systemowych)
        user_tables = [t for t in tables if t not in ("users", "login_history", "sessions")]
        if user_tables:
            print(f"\n  {Colors.BOLD}Twoje tabele:{Colors.END}")
            for i, t in enumerate(user_tables, 1):
                info = db.table_info(t)
                print(f"    {i}. {Colors.CYAN}{t}{Colors.END} "
                      f"({info['record_count']} rekordów, "
                      f"utworzona: {info['created_at']})")
        else:
            print(f"\n  {Colors.DIM}Brak tabel użytkownika.{Colors.END}")

        print(f"""
  {Colors.BOLD}[1]{Colors.END} ➕ Utwórz nową tabelę
  {Colors.BOLD}[2]{Colors.END} ℹ️  Informacje o tabeli
  {Colors.BOLD}[3]{Colors.END} ❌ Usuń tabelę
  {Colors.BOLD}[0]{Colors.END} ↩️  Powrót
        """)

        choice = input(f"  {Colors.CYAN}Wybierz ➤ {Colors.END}").strip()

        if choice == "1":
            name = input(f"  {Colors.YELLOW}Nazwa tabeli: {Colors.END}").strip()
            cols_str = input(f"  {Colors.YELLOW}Kolumny (oddzielone przecinkami): {Colors.END}").strip()
            columns = [c.strip() for c in cols_str.split(",") if c.strip()]

            start = time.time()
            result = db.create_table(name, columns)
            elapsed = time.time() - start

            if result:
                print_success(f"Tabela '{name}' utworzona w {elapsed:.4f}s")
            time.sleep(1.5)

        elif choice == "2":
            name = input(f"  {Colors.YELLOW}Nazwa tabeli: {Colors.END}").strip()
            info = db.table_info(name)
            if info:
                print(f"\n  {Colors.BOLD}Informacje o tabeli '{name}':{Colors.END}")
                for key, value in info.items():
                    print(f"    {Colors.CYAN}{key:>15}{Colors.END}: {value}")
            else:
                print_error("Tabela nie istnieje!")
            input(f"\n  {Colors.DIM}Enter ➤ kontynuuj...{Colors.END}")

        elif choice == "3":
            name = input(f"  {Colors.YELLOW}Nazwa tabeli do usunięcia: {Colors.END}").strip()
            if name in ("users", "login_history", "sessions"):
                print_error("Nie można usunąć tabel systemowych!")
            else:
                confirm = input(f"  {Colors.RED}Czy na pewno? (tak/nie): {Colors.END}").strip()
                if confirm.lower() == "tak":
                    db.drop_table(name)
                    print_success(f"Tabela '{name}' została usunięta.")
            time.sleep(1.5)

        elif choice == "0":
            return


# ========================================
#  OPERACJE CRUD
# ========================================

def crud_operations(db):
    """Ekran operacji na danych."""
    while True:
        print_subheader("📝 OPERACJE NA DANYCH (CRUD)")

        user_tables = [t for t in db.list_tables() if t not in ("users", "login_history", "sessions")]
        if not user_tables:
            print_info("Brak tabel użytkownika. Utwórz najpierw tabelę.")
            input(f"\n  {Colors.DIM}Enter ➤ kontynuuj...{Colors.END}")
            return

        print(f"\n  {Colors.BOLD}Dostępne tabele:{Colors.END} {', '.join(user_tables)}")
        print(f"""
  {Colors.BOLD}[1]{Colors.END} ➕ Dodaj rekord (INSERT)
  {Colors.BOLD}[2]{Colors.END} 🔍 Wyświetl rekordy (SELECT)
  {Colors.BOLD}[3]{Colors.END} ✏️  Aktualizuj rekord (UPDATE)
  {Colors.BOLD}[4]{Colors.END} 🗑️  Usuń rekord (DELETE)
  {Colors.BOLD}[0]{Colors.END} ↩️  Powrót
        """)

        choice = input(f"  {Colors.CYAN}Wybierz ➤ {Colors.END}").strip()

        if choice == "1":
            # INSERT
            table = input(f"  {Colors.YELLOW}Tabela: {Colors.END}").strip()
            info = db.table_info(table)
            if not info:
                print_error("Tabela nie istnieje!")
                time.sleep(1)
                continue

            record = {}
            if info["columns"]:
                print(f"  {Colors.DIM}Kolumny: {', '.join(info['columns'])}{Colors.END}")
                for col in info["columns"]:
                    val = input(f"    {Colors.YELLOW}{col}: {Colors.END}").strip()
                    record[col] = val
            else:
                print_info("Tabela bez zdefiniowanych kolumn. Podaj dane ręcznie.")
                while True:
                    key = input(f"    {Colors.YELLOW}Nazwa pola (Enter = koniec): {Colors.END}").strip()
                    if not key:
                        break
                    val = input(f"    {Colors.YELLOW}Wartość: {Colors.END}").strip()
                    record[key] = val

            start = time.time()
            record_id = db.insert(table, record)
            elapsed = time.time() - start

            if record_id:
                print_success(f"Rekord #{record_id} dodany w {elapsed:.4f}s")
            time.sleep(1.5)

        elif choice == "2":
            # SELECT
            table = input(f"  {Colors.YELLOW}Tabela: {Colors.END}").strip()

            start = time.time()
            records = db.select(table)
            elapsed = time.time() - start

            if records:
                print(f"\n  {Colors.BOLD}Znaleziono {len(records)} rekordów ({elapsed:.4f}s):{Colors.END}\n")
                for record in records:
                    # Wyświetl bez wewnętrznych pól
                    display = {k: v for k, v in record.items() if not k.startswith("_")}
                    print(f"    {Colors.CYAN}#{record['id']}{Colors.END} │ ", end="")
                    fields = [f"{k}={v}" for k, v in display.items() if k != "id"]
                    print(", ".join(fields))
                    print(f"       {Colors.DIM}Utworzono: {record.get('_created_at_formatted', '?')} "
                          f"| Zmodyfikowano: {record.get('_modified_at_formatted', '?')}{Colors.END}")
            else:
                print_info("Brak rekordów lub tabela nie istnieje.")

            input(f"\n  {Colors.DIM}Enter ➤ kontynuuj...{Colors.END}")

        elif choice == "3":
            # UPDATE
            table = input(f"  {Colors.YELLOW}Tabela: {Colors.END}").strip()
            record_id = input(f"  {Colors.YELLOW}ID rekordu do aktualizacji: {Colors.END}").strip()

            try:
                record_id = int(record_id)
            except ValueError:
                print_error("ID musi być liczbą!")
                time.sleep(1)
                continue

            print_info("Podaj nowe wartości pól:")
            new_values = {}
            while True:
                key = input(f"    {Colors.YELLOW}Pole (Enter = zastosuj): {Colors.END}").strip()
                if not key:
                    break
                val = input(f"    {Colors.YELLOW}Nowa wartość: {Colors.END}").strip()
                new_values[key] = val

            if new_values:
                start = time.time()
                updated = db.update(table, {"id": record_id}, new_values)
                elapsed = time.time() - start
                print_success(f"Zaktualizowano {updated} rekord(ów) w {elapsed:.4f}s")
            time.sleep(1.5)

        elif choice == "4":
            # DELETE
            table = input(f"  {Colors.YELLOW}Tabela: {Colors.END}").strip()
            record_id = input(f"  {Colors.YELLOW}ID rekordu do usunięcia: {Colors.END}").strip()

            try:
                record_id = int(record_id)
            except ValueError:
                print_error("ID musi być liczbą!")
                time.sleep(1)
                continue

            confirm = input(f"  {Colors.RED}Usunąć rekord #{record_id}? (tak/nie): {Colors.END}").strip()
            if confirm.lower() == "tak":
                start = time.time()
                deleted = db.delete(table, {"id": record_id})
                elapsed = time.time() - start
                print_success(f"Usunięto {deleted} rekord(ów) w {elapsed:.4f}s")
            time.sleep(1.5)

        elif choice == "0":
            return


# ========================================
#  EKRANY DODATKOWE
# ========================================

def show_profile(auth, username):
    """Wyświetla profil użytkownika."""
    print_subheader(f"👤 PROFIL: {username}")
    profile = auth.get_user_profile(username)
    if profile:
        for key, value in profile.items():
            print(f"  {Colors.CYAN}{key:>20}{Colors.END}: {Colors.BOLD}{value}{Colors.END}")
    input(f"\n  {Colors.DIM}Enter ➤ kontynuuj...{Colors.END}")


def change_password_screen(auth, username):
    """Ekran zmiany hasła."""
    print_subheader("🔑 ZMIANA HASŁA")
    old_pass = input(f"  {Colors.YELLOW}Stare hasło: {Colors.END}").strip()
    new_pass = input(f"  {Colors.YELLOW}Nowe hasło: {Colors.END}").strip()
    new_pass2 = input(f"  {Colors.YELLOW}Powtórz nowe hasło: {Colors.END}").strip()

    if new_pass != new_pass2:
        print_error("Nowe hasła nie są identyczne!")
        time.sleep(1.5)
        return

    loading_animation(1, "Zmiana hasła")
    result = auth.change_password(username, old_pass, new_pass)
    if result["success"]:
        print_success(result["message"])
    else:
        print_error(result["error"])
    time.sleep(2)


def show_login_history(auth, username):
    """Wyświetla historię logowań."""
    print_subheader(f"📜 HISTORIA LOGOWAŃ: {username}")
    history = auth.get_login_history(username, limit=15)
    if history:
        print(f"\n  {'Czas':<22} {'Akcja':<22} {'Status'}")
        print(f"  {'─' * 50}")
        for entry in history:
            print(f"  {entry['time']:<22} {entry['action']:<22} {entry['success']}")
    else:
        print_info("Brak historii logowań.")
    input(f"\n  {Colors.DIM}Enter ➤ kontynuuj...{Colors.END}")


def show_stats(db):
    """Wyświetla statystyki bazy danych."""
    print_subheader("📊 STATYSTYKI BAZY DANYCH")
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"  {Colors.CYAN}{key:>25}{Colors.END}: {Colors.BOLD}{value}{Colors.END}")

    print(f"\n  {Colors.BOLD}Tabele:{Colors.END}")
    for table_name in db.list_tables():
        info = db.table_info(table_name)
        print(f"    📁 {Colors.CYAN}{table_name}{Colors.END}: "
              f"{info['record_count']} rekordów")

    input(f"\n  {Colors.DIM}Enter ➤ kontynuuj...{Colors.END}")


def backup_screen(db):
    """Ekran kopii zapasowych."""
    print_subheader("💾 KOPIE ZAPASOWE")
    backups = db.list_backups()
    if backups:
        print(f"\n  {Colors.BOLD}Istniejące kopie:{Colors.END}")
        for b in backups:
            print(f"    📄 {b['filename']} ({b['size_bytes']} bajtów)")
    else:
        print_info("Brak kopii zapasowych.")

    create = input(f"\n  {Colors.YELLOW}Utworzyć nową kopię? (tak/nie): {Colors.END}").strip()
    if create.lower() == "tak":
        loading_animation(1.5, "Tworzenie kopii zapasowej")
        path = db.create_backup()
        print_success(f"Kopia zapisana: {path}")
    time.sleep(1.5)


def admin_panel(auth, admin_token):
    """Panel administracyjny."""
    while True:
        print_subheader("👥 PANEL ADMINISTRACYJNY")
        print_time()
        print(f"""
  {Colors.BOLD}[1]{Colors.END} 📋 Lista użytkowników
  {Colors.BOLD}[2]{Colors.END} 🔴 Dezaktywuj użytkownika
  {Colors.BOLD}[3]{Colors.END} 🟢 Aktywuj użytkownika
  {Colors.BOLD}[4]{Colors.END} 📜 Historia logowań (wszyscy)
  {Colors.BOLD}[5]{Colors.END} ⚠️  Nieudane logowania (24h)
  {Colors.BOLD}[6]{Colors.END} 📊 Pełne statystyki
  {Colors.BOLD}[7]{Colors.END} 📄 Raport rejestracji (z pliku)
  {Colors.BOLD}[0]{Colors.END} ↩️  Powrót
        """)

        choice = input(f"  {Colors.CYAN}Wybierz ➤ {Colors.END}").strip()

        if choice == "1":
            users = auth.list_users()
            print(f"\n  {Colors.BOLD}Lista użytkowników ({len(users)}):{Colors.END}\n")
            print(f"  {'ID':>4} │ {'Użytkownik':<15} │ {'Rola':<8} │ {'Aktywny':<8} │ {'Ostatnie logowanie'}")
            print(f"  {'─' * 75}")
            for u in users:
                active_icon = "🟢" if u["is_active"] else "🔴"
                print(f"  {u['id']:>4} │ {u['username']:<15} │ {u['role']:<8} │ "
                      f"{active_icon:<8} │ {u['last_login'] or 'Nigdy'}")
            input(f"\n  {Colors.DIM}Enter ➤ kontynuuj...{Colors.END}")

        elif choice == "2":
            username = input(f"  {Colors.YELLOW}Użytkownik do dezaktywacji: {Colors.END}").strip()
            result = auth.deactivate_user(admin_token, username)
            if result["success"]:
                print_success(result["message"])
            else:
                print_error(result["error"])
            time.sleep(1.5)

        elif choice == "3":
            username = input(f"  {Colors.YELLOW}Użytkownik do aktywacji: {Colors.END}").strip()
            result = auth.activate_user(admin_token, username)
            if result["success"]:
                print_success(result["message"])
            else:
                print_error(result["error"])
            time.sleep(1.5)

        elif choice == "4":
            history = auth.get_login_history(limit=25)
            print(f"\n  {Colors.BOLD}Ostatnie 25 akcji:{Colors.END}\n")
            print(f"  {'Czas':<22} {'Użytkownik':<15} {'Akcja':<22} {'Status'}")
            print(f"  {'─' * 65}")
            for entry in history:
                print(f"  {entry['time']:<22} {entry['username']:<15} "
                      f"{entry['action']:<22} {entry['success']}")
            input(f"\n  {Colors.DIM}Enter ➤ kontynuuj...{Colors.END}")

        elif choice == "5":
            failed = auth.get_failed_login_attempts(hours=24)
            print(f"\n  {Colors.BOLD}{failed['period']} - Nieudane próby: {failed['total_failed']}{Colors.END}\n")
            for attempt in failed["attempts"]:
                print(f"  ❌ {attempt['time']} │ {attempt['username']} │ {attempt['action']}")
            input(f"\n  {Colors.DIM}Enter ➤ kontynuuj...{Colors.END}")

        elif choice == "6":
            show_stats(auth.db)

        elif choice == "7":
            # Raport rejestracji z pliku
            print_subheader("📄 RAPORT REJESTRACJI Z PLIKU")
            loading_animation(1, "Generowanie raportu")
            report = generate_report()
            print(report)

            # Pokaż surowe dane z pliku
            show_raw = input(f"\n  {Colors.YELLOW}Pokazać surowe dane z pliku? (tak/nie): {Colors.END}").strip()
            if show_raw.lower() == "tak":
                content = read_users_from_file()
                print(f"\n{content}")
            input(f"\n  {Colors.DIM}Enter ➤ kontynuuj...{Colors.END}")

        elif choice == "0":
            return


def show_active_sessions(auth):
    """Wyświetla aktywne sesje."""
    print_subheader("🔴 AKTYWNE SESJE")
    sessions = auth.get_active_sessions()
    if sessions:
        for s in sessions:
            print(f"  👤 {Colors.BOLD}{s['username']}{Colors.END} ({s['role']})")
            print(f"     Zalogowany: {s['created_at']}")
            print(f"     Wygasa: {s['expires_at']}")
            print(f"     Ostatnia aktyw.: {s['last_activity']}")
            print()
    else:
        print_info("Brak aktywnych sesji.")
    input(f"  {Colors.DIM}Enter ➤ kontynuuj...{Colors.END}")


# ========================================
#  URUCHOMIENIE PROGRAMU
# ========================================

def main():
    """Punkt wejścia programu."""
    show_banner()
    loading_animation(2, "Inicjalizacja systemu")

    # Inicjalizacja
    db = Database("system_database")
    auth = AuthSystem(db)

    print_success("System gotowy do pracy!\n")
    time.sleep(1)

    # Pętla główna
    while True:
        try:
            token = login_screen(auth)
            if token:
                main_menu(auth, token)
        except KeyboardInterrupt:
            print(f"\n\n  {Colors.YELLOW}Przerwanie programu...{Colors.END}")
            if auth.current_session:
                auth.logout()
            print_slow(f"  {Colors.CYAN}Do zobaczenia! 👋{Colors.END}", 0.03)
            break
        except Exception as e:
            print_error(f"Wystąpił błąd: {str(e)}")
            time.sleep(2)


if __name__ == "__main__":
    main()
