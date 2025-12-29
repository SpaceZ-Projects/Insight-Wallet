
from toga import App
import re
import sqlite3
from pathlib import Path
from nacl import utils
from nacl.secret import SecretBox
from nacl.pwhash import argon2id


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value BLOB NOT NULL
);

CREATE TABLE IF NOT EXISTS coins (
    coin TEXT PRIMARY KEY,
    address BLOB NOT NULL,
    wif BLOB NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin TEXT NOT NULL,
    txid TEXT NOT NULL,
    type TEXT NOT NULL,
    amount TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    UNIQUE(coin, txid)
);
"""


class Vault:
    def __init__(self, app: App):
        self.app = app
        self.data_path: Path = app.paths.data
        self.data_path.mkdir(parents=True, exist_ok=True)


    def safe_account(self, account: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_-]", "_", account)

    def vault_path(self, account: str) -> Path:
        return self.data_path / f"wallet_{self.safe_account(account)}.db"

    def vault_exists(self, account: str) -> bool:
        return self.vault_path(account).exists()


    def derive_key(self, password: str, salt: bytes) -> bytes:
        return argon2id.kdf(
            SecretBox.KEY_SIZE,
            password.encode("utf-8"),
            salt,
            opslimit=argon2id.OPSLIMIT_MODERATE,
            memlimit=argon2id.MEMLIMIT_MODERATE,
        )

    def encrypt(self, key: bytes, value: str) -> bytes:
        return SecretBox(key).encrypt(value.encode("utf-8"))

    def decrypt(self, key: bytes, value: bytes) -> str:
        return SecretBox(key).decrypt(value).decode("utf-8")
    

    def create_vault(self, account: str, password: str) -> bool:
        path = self.vault_path(account)
        if path.exists():
            return False
        conn = sqlite3.connect(path)
        conn.execute("PRAGMA foreign_keys = ON")
        salt = utils.random(argon2id.SALTBYTES)
        key = self.derive_key(password, salt)
        conn.executescript(SCHEMA_SQL)

        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            ("salt", salt),
        )
        verifier = self.encrypt(key, "vault-ok")
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            ("verifier", verifier),
        )

        conn.commit()
        conn.close()
        return True

    def open_vault(self, account: str, password: str):
        path = self.vault_path(account)
        if not path.exists():
            raise FileNotFoundError("Vault does not exist")

        conn = sqlite3.connect(path)
        conn.execute("PRAGMA foreign_keys = ON")
        salt = conn.execute(
            "SELECT value FROM meta WHERE key='salt'"
        ).fetchone()
        verifier = conn.execute(
            "SELECT value FROM meta WHERE key='verifier'"
        ).fetchone()

        if not salt or not verifier:
            conn.close()
            raise ValueError("Invalid vault format")

        key = self.derive_key(password, salt[0])
        try:
            test = self.decrypt(key, verifier[0])
            if test != "vault-ok":
                raise ValueError
        except Exception:
            conn.close()
            raise ValueError("Wrong password")

        return conn, key

    def list_accounts(self) -> list[str]:
        return sorted(
            f.name[len("wallet_"):-3]
            for f in self.data_path.iterdir()
            if f.is_file() and f.name.startswith("wallet_") and f.name.endswith(".db")
        )

    def add_coin(self, account, password, coin, address, wif) -> bool:
        conn, key = self.open_vault(account, password)
        try:
            conn.execute(
                "INSERT INTO coins VALUES (?, ?, ?)",
                (coin, self.encrypt(key, address), self.encrypt(key, wif)),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def list_coins(self, account, password) -> list[str]:
        conn, _ = self.open_vault(account, password)
        rows = conn.execute("SELECT coin FROM coins").fetchall()
        conn.close()
        return [r[0] for r in rows]

    def get_coin_address(self, account, password, coin):
        conn, key = self.open_vault(account, password)
        row = conn.execute(
            "SELECT address FROM coins WHERE coin=?",
            (coin,),
        ).fetchone()
        conn.close()
        return self.decrypt(key, row[0]) if row else None

    def get_coin_wif(self, account, password, coin):
        conn, key = self.open_vault(account, password)
        row = conn.execute(
            "SELECT wif FROM coins WHERE coin=?",
            (coin,),
        ).fetchone()
        conn.close()
        return self.decrypt(key, row[0]) if row else None

    def add_transaction(
        self, account, password, coin, tx_type, txid, amount, timestamp
    ) -> bool:
        conn, _ = self.open_vault(account, password)
        try:
            conn.execute(
                """
                INSERT INTO transactions
                (coin, txid, type, amount, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (coin, txid, tx_type, amount, timestamp),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_transactions(self, account, password, coin) -> list[dict]:
        conn, _ = self.open_vault(account, password)
        rows = conn.execute(
            """
            SELECT txid, type, amount, timestamp
            FROM transactions
            WHERE coin=?
            ORDER BY id DESC
            """,
            (coin,),
        ).fetchall()
        conn.close()

        return [
            dict(txid=r[0], type=r[1], amount=r[2], timestamp=r[3])
            for r in rows
        ]
    

    def export_coin_data(
        self,
        account: str,
        password: str,
        coin: str,
        output_path=None
    ) -> bool:
        
        try:
            address = self.get_coin_address(account, password, coin)
            wif = self.get_coin_wif(account, password, coin)
        except Exception:
            return False

        if not address or not wif:
            return False

        txs = self.get_transactions(account, password, coin)
        if output_path is None:
            safe_account = re.sub(r"[^a-zA-Z0-9_-]", "_", account)
            filename = f"{safe_account}_{coin}_export.txt"
            output_path = self.app.paths.data / filename

        lines = []
        lines.append("⚠️ WARNING")
        lines.append("This file contains PRIVATE KEY.")
        lines.append("Anyone with access can spend your funds.")
        lines.append("Store OFFLINE and keep it secure.")
        lines.append("=" * 40)
        lines.append("")

        lines.append("WALLET COIN EXPORT")
        lines.append("=" * 40)
        lines.append(f"Account        : {account}")
        lines.append(f"Coin           : {coin}")
        lines.append("")

        lines.append(f"{'ADDRESS':15}: {address}")
        lines.append(f"{'WIF':15}: {wif}")

        lines.append("")
        lines.append(f"Transactions ({len(txs)})")
        lines.append("-" * 40)

        if not txs:
            lines.append("No transactions recorded.")
        else:
            for i, tx in enumerate(txs, 1):
                lines.append(f"[{i}]")
                for k, v in tx.items():
                    if k.lower() == "amount":
                        v = self.app.utils.format_balance(v)
                    lines.append(f"  {k.upper():12}: {v}")
                lines.append("")

        lines.append("=" * 40)

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return True
