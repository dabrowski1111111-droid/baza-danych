"""
==========================================================
  MODUŁ BAZY DANYCH - Silnik bazodanowy oparty na JSON
  Wykorzystuje moduł 'time' do:
    - znaczników czasowych tworzenia/modyfikacji rekordów
    - mierzenia czasu wykonania operacji
    - automatycznych kopii zapasowych
    - zarządzania sesjami
==========================================================
"""

import json
import os
import time
import hashlib
import copy


class Database:
    """
    Silnik bazy danych oparty na plikach JSON.
    Obsługuje wiele tabel, indeksowanie i mierzenie czasu operacji.
    """

    def __init__(self, db_name="main_database", db_dir="data"):
        self.db_name = db_name
        self.db_dir = db_dir
        self.db_path = os.path.join(db_dir, f"{db_name}.json")
        self.backup_dir = os.path.join(db_dir, "backups")
        self.stats = {
            "total_queries": 0,
            "total_inserts": 0,
            "total_updates": 0,
            "total_deletes": 0,
            "total_time_spent": 0.0,
            "created_at": time.time(),
            "last_operation_at": None,
        }
        self.data = {}
        self._ensure_directories()
        self._load()

    def _ensure_directories(self):
        """Tworzy katalogi bazy danych jeśli nie istnieją."""
        os.makedirs(self.db_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

    def _load(self):
        """Ładuje bazę danych z pliku JSON."""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self.data = saved.get("tables", {})
                    self.stats = saved.get("stats", self.stats)
                    print(f"  [DB] Załadowano bazę '{self.db_name}' z dysku.")
            except (json.JSONDecodeError, IOError):
                print(f"  [DB] UWAGA: Nie udało się załadować bazy. Tworzenie nowej...")
                self.data = {}
        else:
            print(f"  [DB] Tworzenie nowej bazy danych '{self.db_name}'...")

    def _save(self):
        """Zapisuje bazę danych do pliku JSON."""
        save_data = {
            "db_name": self.db_name,
            "saved_at": time.time(),
            "saved_at_formatted": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "tables": self.data,
            "stats": self.stats,
        }
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

    def _measure_time(func):
        """Dekorator mierzący czas wykonania operacji bazodanowej."""
        def wrapper(self, *args, **kwargs):
            start = time.time()
            result = func(self, *args, **kwargs)
            elapsed = time.time() - start
            self.stats["total_time_spent"] += elapsed
            self.stats["last_operation_at"] = time.time()
            return result
        return wrapper

    # ========================================
    #  ZARZĄDZANIE TABELAMI
    # ========================================

    @_measure_time
    def create_table(self, table_name, columns=None):
        """
        Tworzy nową tabelę w bazie danych.
        
        Args:
            table_name: Nazwa tabeli
            columns: Lista nazw kolumn (opcjonalnie)
        """
        if table_name in self.data:
            print(f"  [DB] Tabela '{table_name}' już istnieje!")
            return False

        self.data[table_name] = {
            "columns": columns or [],
            "records": [],
            "auto_increment": 1,
            "created_at": time.time(),
            "created_at_formatted": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "modified_at": time.time(),
            "record_count": 0,
        }
        self._save()
        print(f"  [DB] Tabela '{table_name}' została utworzona.")
        return True

    def drop_table(self, table_name):
        """Usuwa tabelę z bazy danych."""
        if table_name not in self.data:
            print(f"  [DB] Tabela '{table_name}' nie istnieje!")
            return False

        del self.data[table_name]
        self._save()
        print(f"  [DB] Tabela '{table_name}' została usunięta.")
        return True

    def list_tables(self):
        """Zwraca listę wszystkich tabel."""
        return list(self.data.keys())

    def table_info(self, table_name):
        """Zwraca informacje o tabeli."""
        if table_name not in self.data:
            return None
        table = self.data[table_name]
        return {
            "name": table_name,
            "columns": table["columns"],
            "record_count": table["record_count"],
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(table["created_at"])),
            "modified_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(table["modified_at"])),
        }

    # ========================================
    #  OPERACJE CRUD
    # ========================================

    @_measure_time
    def insert(self, table_name, record):
        """
        Wstawia nowy rekord do tabeli.
        
        Args:
            table_name: Nazwa tabeli
            record: Słownik z danymi rekordu
        """
        if table_name not in self.data:
            print(f"  [DB] Tabela '{table_name}' nie istnieje!")
            return None

        table = self.data[table_name]

        # Dodaj metadane czasowe
        new_record = {
            "id": table["auto_increment"],
            **record,
            "_created_at": time.time(),
            "_created_at_formatted": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "_modified_at": time.time(),
            "_modified_at_formatted": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        }

        table["records"].append(new_record)
        table["auto_increment"] += 1
        table["record_count"] = len(table["records"])
        table["modified_at"] = time.time()
        self.stats["total_inserts"] += 1
        self._save()
        return new_record["id"]

    @_measure_time
    def select(self, table_name, conditions=None, limit=None, order_by=None):
        """
        Wyszukuje rekordy w tabeli.
        
        Args:
            table_name: Nazwa tabeli
            conditions: Słownik warunków {kolumna: wartość}
            limit: Maksymalna liczba wyników
            order_by: Kolumna do sortowania (prefiks '-' = malejąco)
        """
        if table_name not in self.data:
            print(f"  [DB] Tabela '{table_name}' nie istnieje!")
            return []

        self.stats["total_queries"] += 1
        records = self.data[table_name]["records"]

        # Filtrowanie
        if conditions:
            results = []
            for record in records:
                match = True
                for key, value in conditions.items():
                    if record.get(key) != value:
                        match = False
                        break
                if match:
                    results.append(copy.deepcopy(record))
        else:
            results = copy.deepcopy(records)

        # Sortowanie
        if order_by:
            reverse = False
            if order_by.startswith("-"):
                reverse = True
                order_by = order_by[1:]
            results.sort(key=lambda x: x.get(order_by, ""), reverse=reverse)

        # Limit
        if limit:
            results = results[:limit]

        return results

    @_measure_time
    def select_one(self, table_name, conditions):
        """Zwraca pierwszy pasujący rekord."""
        results = self.select(table_name, conditions, limit=1)
        return results[0] if results else None

    @_measure_time
    def update(self, table_name, conditions, new_values):
        """
        Aktualizuje rekordy spełniające warunki.
        
        Args:
            table_name: Nazwa tabeli
            conditions: Warunki wyszukiwania
            new_values: Nowe wartości do ustawienia
        """
        if table_name not in self.data:
            return 0

        updated = 0
        for record in self.data[table_name]["records"]:
            match = all(record.get(k) == v for k, v in conditions.items())
            if match:
                record.update(new_values)
                record["_modified_at"] = time.time()
                record["_modified_at_formatted"] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime()
                )
                updated += 1

        if updated > 0:
            self.data[table_name]["modified_at"] = time.time()
            self.stats["total_updates"] += updated
            self._save()

        return updated

    @_measure_time
    def delete(self, table_name, conditions):
        """
        Usuwa rekordy spełniające warunki.
        
        Args:
            table_name: Nazwa tabeli
            conditions: Warunki do dopasowania
        """
        if table_name not in self.data:
            return 0

        table = self.data[table_name]
        original_count = len(table["records"])

        table["records"] = [
            record for record in table["records"]
            if not all(record.get(k) == v for k, v in conditions.items())
        ]

        deleted = original_count - len(table["records"])
        if deleted > 0:
            table["record_count"] = len(table["records"])
            table["modified_at"] = time.time()
            self.stats["total_deletes"] += deleted
            self._save()

        return deleted

    # ========================================
    #  KOPIE ZAPASOWE
    # ========================================

    def create_backup(self):
        """Tworzy kopię zapasową bazy danych z znacznikiem czasowym."""
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        backup_filename = f"{self.db_name}_backup_{timestamp}.json"
        backup_path = os.path.join(self.backup_dir, backup_filename)

        save_data = {
            "db_name": self.db_name,
            "backup_created_at": time.time(),
            "backup_created_at_formatted": time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime()
            ),
            "tables": self.data,
            "stats": self.stats,
        }

        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        print(f"  [DB] Kopia zapasowa zapisana: {backup_filename}")
        return backup_path

    def list_backups(self):
        """Zwraca listę dostępnych kopii zapasowych."""
        backups = []
        if os.path.exists(self.backup_dir):
            for f in sorted(os.listdir(self.backup_dir)):
                if f.endswith(".json"):
                    path = os.path.join(self.backup_dir, f)
                    size = os.path.getsize(path)
                    backups.append({"filename": f, "size_bytes": size})
        return backups

    # ========================================
    #  STATYSTYKI
    # ========================================

    def get_stats(self):
        """Zwraca statystyki bazy danych."""
        uptime = time.time() - self.stats["created_at"]
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)

        return {
            "db_name": self.db_name,
            "tables_count": len(self.data),
            "total_records": sum(t["record_count"] for t in self.data.values()),
            "total_queries": self.stats["total_queries"],
            "total_inserts": self.stats["total_inserts"],
            "total_updates": self.stats["total_updates"],
            "total_deletes": self.stats["total_deletes"],
            "total_time_spent": f"{self.stats['total_time_spent']:.6f}s",
            "uptime": f"{hours}h {minutes}m {seconds}s",
            "created_at": time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(self.stats["created_at"])
            ),
            "last_operation": time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(self.stats["last_operation_at"])
            ) if self.stats["last_operation_at"] else "Brak",
        }
