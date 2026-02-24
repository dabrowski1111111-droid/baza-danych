"""
==========================================================
  SYSTEM AUTENTYKACJI - Logowanie, rejestracja, sesje
  Wykorzystuje moduł 'time' do:
    - hashowania haseł z solą czasową
    - zarządzania sesjami (tworzenie, wygasanie)
    - śledzenia historii logowań
    - blokowania konta po nieudanych próbach
    - mierzenia czasu aktywności użytkownika
==========================================================
"""

import time
import hashlib
import os
from database import Database
from user_data_export import save_user_to_file


class AuthSystem:
    """
    Kompletny system autentykacji z sesjami, historią logowań,
    blokadą konta i zarządzaniem rolami.
    """

    SESSION_TIMEOUT = 1800  # 30 minut na wygaśnięcie sesji
    MAX_FAILED_ATTEMPTS = 5  # Max nieudanych prób logowania
    LOCKOUT_DURATION = 300  # 5 minut blokady po przekroczeniu limitu
    PASSWORD_MIN_LENGTH = 6

    def __init__(self, db=None):
        self.db = db or Database("auth_database")
        self.sessions = {}  # Aktywne sesje {token: dane_sesji}
        self._setup_tables()
        self.current_user = None
        self.current_session = None

    def _setup_tables(self):
        """Inicjalizuje wymagane tabele w bazie danych."""
        # Tabela użytkowników
        self.db.create_table("users", [
            "id", "username", "password_hash", "salt",
            "email", "role", "is_active",
            "failed_attempts", "locked_until",
            "created_at", "last_login"
        ])

        # Tabela historii logowań
        self.db.create_table("login_history", [
            "id", "user_id", "username", "action",
            "success", "ip_address", "timestamp"
        ])

        # Tabela sesji
        self.db.create_table("sessions", [
            "id", "user_id", "token", "created_at",
            "expires_at", "is_active"
        ])

    # ========================================
    #  HASHOWANIE HASEŁ
    # ========================================

    def _generate_salt(self):
        """Generuje sól kryptograficzną z użyciem czasu."""
        time_component = str(time.time()).encode()
        random_bytes = os.urandom(32)
        combined = time_component + random_bytes
        return hashlib.sha256(combined).hexdigest()[:32]

    def _hash_password(self, password, salt):
        """Hashuje hasło z solą używając SHA-256."""
        salted = f"{salt}{password}{salt}".encode()
        # Wielokrotne hashowanie dla bezpieczeństwa
        hashed = hashlib.sha256(salted).hexdigest()
        for _ in range(1000):
            hashed = hashlib.sha256(f"{hashed}{salt}".encode()).hexdigest()
        return hashed

    def _generate_session_token(self, user_id):
        """Generuje unikalny token sesji z użyciem czasu."""
        token_data = f"{user_id}{time.time()}{os.urandom(16).hex()}"
        return hashlib.sha256(token_data.encode()).hexdigest()

    # ========================================
    #  REJESTRACJA
    # ========================================

    def register(self, username, password, email="", role="user"):
        """
        Rejestruje nowego użytkownika.
        
        Args:
            username: Nazwa użytkownika
            password: Hasło
            email: Adres email (opcjonalnie)
            role: Rola użytkownika ('user' lub 'admin')
            
        Returns:
            dict z wynikiem rejestracji
        """
        start_time = time.time()

        # Walidacja
        if len(username) < 3:
            return {"success": False, "error": "Nazwa użytkownika musi mieć min. 3 znaki."}

        if len(password) < self.PASSWORD_MIN_LENGTH:
            return {"success": False, "error": f"Hasło musi mieć min. {self.PASSWORD_MIN_LENGTH} znaków."}

        # Sprawdź czy użytkownik już istnieje
        existing = self.db.select_one("users", {"username": username})
        if existing:
            return {"success": False, "error": "Użytkownik o tej nazwie już istnieje!"}

        # Tworzenie konta
        salt = self._generate_salt()
        password_hash = self._hash_password(password, salt)

        user_id = self.db.insert("users", {
            "username": username,
            "password_hash": password_hash,
            "salt": salt,
            "email": email,
            "role": role,
            "is_active": True,
            "failed_attempts": 0,
            "locked_until": 0,
            "last_login": None,
            "last_login_formatted": None,
        })

        # Zapisz w historii
        self._log_action(user_id, username, "REGISTER", True)

        # === ZAPISZ DANE DO PLIKU TEKSTOWEGO ===
        save_user_to_file(username, email, role, user_id)
        print(f"  [AUTH] Dane użytkownika '{username}' zapisane do pliku.")

        elapsed = time.time() - start_time
        return {
            "success": True,
            "user_id": user_id,
            "message": f"Konto '{username}' zostało utworzone pomyślnie!",
            "time_elapsed": f"{elapsed:.4f}s",
        }

    # ========================================
    #  LOGOWANIE
    # ========================================

    def login(self, username, password):
        """
        Loguje użytkownika do systemu.
        
        Args:
            username: Nazwa użytkownika
            password: Hasło
            
        Returns:
            dict z wynikiem logowania i tokenem sesji
        """
        start_time = time.time()

        # Znajdź użytkownika
        user = self.db.select_one("users", {"username": username})
        if not user:
            self._log_action(None, username, "LOGIN_FAILED", False)
            return {"success": False, "error": "Nieprawidłowa nazwa użytkownika lub hasło."}

        # Sprawdź blokadę konta
        if user.get("locked_until", 0) > time.time():
            remaining = int(user["locked_until"] - time.time())
            self._log_action(user["id"], username, "LOGIN_BLOCKED", False)
            return {
                "success": False,
                "error": f"Konto jest zablokowane. Spróbuj za {remaining} sekund.",
            }

        # Sprawdź czy konto jest aktywne
        if not user.get("is_active", True):
            return {"success": False, "error": "Konto jest dezaktywowane."}

        # Weryfikacja hasła
        password_hash = self._hash_password(password, user["salt"])
        if password_hash != user["password_hash"]:
            # Zwiększ licznik nieudanych prób
            failed = user.get("failed_attempts", 0) + 1
            update_data = {"failed_attempts": failed}

            if failed >= self.MAX_FAILED_ATTEMPTS:
                update_data["locked_until"] = time.time() + self.LOCKOUT_DURATION
                self._log_action(user["id"], username, "ACCOUNT_LOCKED", False)
                self.db.update("users", {"id": user["id"]}, update_data)
                return {
                    "success": False,
                    "error": f"Konto zablokowane na {self.LOCKOUT_DURATION // 60} minut "
                             f"z powodu {self.MAX_FAILED_ATTEMPTS} nieudanych prób logowania.",
                }

            self.db.update("users", {"id": user["id"]}, update_data)
            self._log_action(user["id"], username, "LOGIN_FAILED", False)
            remaining_attempts = self.MAX_FAILED_ATTEMPTS - failed
            return {
                "success": False,
                "error": f"Nieprawidłowe hasło. Pozostało prób: {remaining_attempts}",
            }

        # === LOGOWANIE UDANE ===
        # Resetuj licznik nieudanych prób
        self.db.update("users", {"id": user["id"]}, {
            "failed_attempts": 0,
            "locked_until": 0,
            "last_login": time.time(),
            "last_login_formatted": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        })

        # Utwórz sesję
        token = self._generate_session_token(user["id"])
        session_data = {
            "user_id": user["id"],
            "username": username,
            "role": user["role"],
            "token": token,
            "created_at": time.time(),
            "expires_at": time.time() + self.SESSION_TIMEOUT,
            "last_activity": time.time(),
        }
        self.sessions[token] = session_data

        # Zapisz sesję do bazy
        self.db.insert("sessions", {
            "user_id": user["id"],
            "token": token,
            "expires_at": time.time() + self.SESSION_TIMEOUT,
            "is_active": True,
        })

        self.current_user = user
        self.current_session = token
        self._log_action(user["id"], username, "LOGIN_SUCCESS", True)

        elapsed = time.time() - start_time
        return {
            "success": True,
            "message": f"Witaj, {username}! Zalogowano pomyślnie.",
            "token": token,
            "role": user["role"],
            "session_expires_in": f"{self.SESSION_TIMEOUT // 60} minut",
            "time_elapsed": f"{elapsed:.4f}s",
        }

    # ========================================
    #  WYLOGOWANIE
    # ========================================

    def logout(self, token=None):
        """Wylogowuje użytkownika i kończy sesję."""
        token = token or self.current_session
        if not token or token not in self.sessions:
            return {"success": False, "error": "Brak aktywnej sesji."}

        session = self.sessions[token]
        username = session["username"]
        session_duration = time.time() - session["created_at"]

        # Dezaktywuj sesję
        del self.sessions[token]
        self.db.update("sessions", {"token": token}, {"is_active": False})
        self._log_action(session["user_id"], username, "LOGOUT", True)

        self.current_user = None
        self.current_session = None

        minutes = int(session_duration // 60)
        seconds = int(session_duration % 60)

        return {
            "success": True,
            "message": f"Wylogowano użytkownika '{username}'.",
            "session_duration": f"{minutes}m {seconds}s",
        }

    # ========================================
    #  ZARZĄDZANIE SESJAMI
    # ========================================

    def validate_session(self, token=None):
        """Sprawdza czy sesja jest aktywna i nieprzeterminowana."""
        token = token or self.current_session
        if not token or token not in self.sessions:
            return {"valid": False, "error": "Sesja nie istnieje."}

        session = self.sessions[token]

        # Sprawdź wygaśnięcie
        if time.time() > session["expires_at"]:
            del self.sessions[token]
            self.db.update("sessions", {"token": token}, {"is_active": False})
            self.current_user = None
            self.current_session = None
            return {"valid": False, "error": "Sesja wygasła. Zaloguj się ponownie."}

        # Odśwież sesję
        session["last_activity"] = time.time()
        session["expires_at"] = time.time() + self.SESSION_TIMEOUT

        remaining = int(session["expires_at"] - time.time())
        return {
            "valid": True,
            "username": session["username"],
            "role": session["role"],
            "time_remaining": f"{remaining // 60}m {remaining % 60}s",
        }

    def get_active_sessions(self):
        """Zwraca listę aktywnych sesji."""
        active = []
        for token, session in list(self.sessions.items()):
            if time.time() > session["expires_at"]:
                del self.sessions[token]
                continue
            active.append({
                "username": session["username"],
                "role": session["role"],
                "created_at": time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(session["created_at"])
                ),
                "expires_at": time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(session["expires_at"])
                ),
                "last_activity": time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(session["last_activity"])
                ),
            })
        return active

    # ========================================
    #  ZARZĄDZANIE UŻYTKOWNIKAMI
    # ========================================

    def change_password(self, username, old_password, new_password):
        """Zmienia hasło użytkownika."""
        user = self.db.select_one("users", {"username": username})
        if not user:
            return {"success": False, "error": "Użytkownik nie istnieje."}

        # Weryfikacja starego hasła
        old_hash = self._hash_password(old_password, user["salt"])
        if old_hash != user["password_hash"]:
            return {"success": False, "error": "Nieprawidłowe stare hasło."}

        if len(new_password) < self.PASSWORD_MIN_LENGTH:
            return {"success": False, "error": f"Nowe hasło musi mieć min. {self.PASSWORD_MIN_LENGTH} znaków."}

        # Ustaw nowe hasło
        new_salt = self._generate_salt()
        new_hash = self._hash_password(new_password, new_salt)

        self.db.update("users", {"id": user["id"]}, {
            "password_hash": new_hash,
            "salt": new_salt,
        })

        self._log_action(user["id"], username, "PASSWORD_CHANGED", True)
        return {"success": True, "message": "Hasło zostało zmienione pomyślnie."}

    def deactivate_user(self, admin_token, username):
        """Dezaktywuje konto użytkownika (tylko admin)."""
        admin_session = self.validate_session(admin_token)
        if not admin_session["valid"]:
            return {"success": False, "error": "Brak uprawnień - nieprawidłowa sesja."}

        session_data = self.sessions.get(admin_token)
        if not session_data or session_data["role"] != "admin":
            return {"success": False, "error": "Brak uprawnień administratora!"}

        user = self.db.select_one("users", {"username": username})
        if not user:
            return {"success": False, "error": "Użytkownik nie istnieje."}

        self.db.update("users", {"username": username}, {"is_active": False})
        self._log_action(user["id"], username, "ACCOUNT_DEACTIVATED", True)

        return {"success": True, "message": f"Konto '{username}' zostało dezaktywowane."}

    def activate_user(self, admin_token, username):
        """Aktywuje konto użytkownika (tylko admin)."""
        admin_session = self.validate_session(admin_token)
        if not admin_session["valid"]:
            return {"success": False, "error": "Brak uprawnień - nieprawidłowa sesja."}

        session_data = self.sessions.get(admin_token)
        if not session_data or session_data["role"] != "admin":
            return {"success": False, "error": "Brak uprawnień administratora!"}

        self.db.update("users", {"username": username}, {"is_active": True, "failed_attempts": 0, "locked_until": 0})
        return {"success": True, "message": f"Konto '{username}' zostało aktywowane."}

    def list_users(self, admin_token=None):
        """Lista wszystkich użytkowników (widok administracyjny)."""
        users = self.db.select("users")
        result = []
        for user in users:
            result.append({
                "id": user["id"],
                "username": user["username"],
                "email": user.get("email", ""),
                "role": user["role"],
                "is_active": user["is_active"],
                "last_login": user.get("last_login_formatted", "Nigdy"),
                "created_at": user.get("_created_at_formatted", ""),
            })
        return result

    def get_user_profile(self, username):
        """Zwraca profil użytkownika."""
        user = self.db.select_one("users", {"username": username})
        if not user:
            return None

        # Oblicz czas od rejestracji
        registered_time = user.get("_created_at", time.time())
        account_age = time.time() - registered_time
        days = int(account_age // 86400)
        hours = int((account_age % 86400) // 3600)

        # Historia logowań
        login_count = len(self.db.select("login_history", {
            "username": username, "action": "LOGIN_SUCCESS"
        }))

        return {
            "username": user["username"],
            "email": user.get("email", ""),
            "role": user["role"],
            "is_active": user["is_active"],
            "account_age": f"{days} dni, {hours} godzin",
            "total_logins": login_count,
            "last_login": user.get("last_login_formatted", "Nigdy"),
            "registered_at": user.get("_created_at_formatted", ""),
        }

    # ========================================
    #  HISTORIA LOGOWAŃ
    # ========================================

    def _log_action(self, user_id, username, action, success):
        """Zapisuje akcję w historii logowań."""
        self.db.insert("login_history", {
            "user_id": user_id,
            "username": username,
            "action": action,
            "success": success,
            "timestamp": time.time(),
            "timestamp_formatted": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        })

    def get_login_history(self, username=None, limit=20):
        """Zwraca historię logowań."""
        if username:
            history = self.db.select("login_history", {"username": username})
        else:
            history = self.db.select("login_history")

        # Sortuj od najnowszych
        history.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

        if limit:
            history = history[:limit]

        result = []
        for entry in history:
            result.append({
                "username": entry["username"],
                "action": entry["action"],
                "success": "✅" if entry["success"] else "❌",
                "time": entry.get("timestamp_formatted", ""),
            })
        return result

    def get_failed_login_attempts(self, username=None, hours=24):
        """Zwraca nieudane próby logowania z ostatnich N godzin."""
        cutoff = time.time() - (hours * 3600)
        
        if username:
            history = self.db.select("login_history", {"username": username})
        else:
            history = self.db.select("login_history")

        failed = [
            entry for entry in history
            if not entry.get("success", True)
            and entry.get("timestamp", 0) > cutoff
        ]

        return {
            "period": f"Ostatnie {hours} godzin",
            "total_failed": len(failed),
            "attempts": [
                {
                    "username": e["username"],
                    "action": e["action"],
                    "time": e.get("timestamp_formatted", ""),
                }
                for e in failed
            ],
        }
