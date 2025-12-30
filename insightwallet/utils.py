
import re
import json
from toga import App
from toga.platform import current_platform
from decimal import Decimal
import aiohttp

from hdwallet import HDWallet
from hdwallet.hds import BIP32HD
from hdwallet.mnemonics import BIP39_MNEMONIC_LANGUAGES
from hdwallet.entropies import BIP39Entropy, BIP39_ENTROPY_STRENGTHS
from hdwallet.derivations import CustomDerivation
from hdwallet.consts import PUBLIC_KEY_TYPES

import io
import qrcode
from toga.images import Image


#https://github.com/ezzygarmyz/bitgo-utxo-lib-z
TOOL_SHA256 = {
    "windows": "f5733aa845430b04e843d69cc9ca075a722d27e4e555f1448a98d46c6b853143",
    "linux":   "5961ea3ca5db48e62251730908dc55920037905063806327e33c094d6b4406c8",
    "darwin":  "26ef18c2d78d54b89daaca751ac7fca48ddf29636aef232f873526d140e30a68",
}

class Utils:
    def __init__(self, app:App):
        
        self.app = app
        if not self.app.paths.data.exists():
            self.app.paths.data.mkdir(exist_ok=True)


    def sha256_file(self, path):
        import hashlib
        platform = current_platform
        expected_hash = TOOL_SHA256.get(platform)
        if not expected_hash:
            return False
        h = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    h.update(chunk)
        except Exception:
            return False
        file_hash = h.hexdigest().lower()
        return file_hash == expected_hash.lower()


    def format_balance(self, value):
        value = Decimal(value)
        formatted_value = f"{value:.8f}"
        integer_part, decimal_part = formatted_value.split('.')
        if len(integer_part) > 4:
            digits_to_remove = len(integer_part) - 4
            formatted_decimal = decimal_part[:-digits_to_remove]
        else:
            formatted_decimal = decimal_part
        formatted_balance = f"{integer_part}.{formatted_decimal}"
        return formatted_balance
    
    def apply_title_bar_mode(self, window): 
        try:
            import ctypes
            hwnd = window._impl.native.Handle.ToInt32()
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                ctypes.wintypes.HWND(hwnd),
                ctypes.c_int(20),
                ctypes.byref(value),
                ctypes.sizeof(value)
            )
        except Exception as e:
            print(f"Failed to apply title bar mode: {e}")

    def get_tool(self):
        platfom = current_platform
        if platfom == "windows":
            file_name = "mktx.exe"
        elif platfom == "linux":
            file_name = "mktx"
        elif platfom == "darwin":
            file_name = "mktxmac"
        return self.app.paths.data / file_name


    def copy_to_clipboard(self, text):
        platform = current_platform
        if platform == "windows":
            import System.Windows.Forms as Forms
            clipboard = Forms.Clipboard
            clipboard.SetText(text)
        elif platform == "linux":
            from gi.repository import Gtk, Gdk
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(text, -1)
            clipboard.store()
        elif platform == "darwin":
            from rubicon.objc import ObjCClass
            NSPasteboard = ObjCClass("NSPasteboard")
            NSString = ObjCClass("NSString")
            pasteboard = NSPasteboard.generalPasteboard
            pasteboard.clearContents()
            ns_text = NSString.alloc().initWithUTF8String_(text.encode("utf-8"))
            pasteboard.setString_forType_(ns_text, "public.utf8-plain-text")


    def qr_generate(self, address: str):
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=7,
            border=1,
        )
        qr.add_data(address)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")
        buffer.seek(0)
        return Image(src=buffer.read())
    

    def load_coins_config(self) -> dict:
        coins_file = self.app.paths.app / "endpoints.json"
        if not coins_file.exists():
            return {}
        try:
            return json.loads(coins_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Failed to load coins config: {e}")
            return {}


    def get_available_coins(self) -> list[str]:
        coins = self.load_coins_config()
        return sorted(coins.keys())
    
    def get_coin(self, coin: str) -> dict | None:
        coins = self.load_coins_config()
        return coins.get(coin)
    

    async def fetch_tool(self, setup, label, progress_bar):
        platfom = current_platform
        if platfom == "windows":
            file_name = "mktx.exe"
        elif platfom == "linux":
            file_name = "mktx"
        elif platfom == "darwin":
            file_name = "mktxmac"
        url = "https://github.com/ezzygarmyz/bitgo-utxo-lib-z/releases/download/v1.0.0/"
        destination = self.app.paths.data / file_name
        self.progress = 0
        try:
            import ssl
            import certifi
            import hashlib
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            async with aiohttp.ClientSession() as session:
                async with session.get(url + file_name, timeout=None, ssl=ssl_context) as response:
                    if response.status == 200:
                        total_size = int(response.headers.get('content-length', 0))
                        chunk_size = 512
                        downloaded_size = 0
                        hasher = hashlib.sha256()
                        self.file_handle = open(destination, 'wb')
                        async for chunk in response.content.iter_chunked(chunk_size):
                            if not chunk:
                                break
                            self.file_handle.write(chunk)
                            hasher.update(chunk)
                            downloaded_size += len(chunk)
                            progress = int(downloaded_size / total_size * 100)
                            if self.progress < progress:
                                label.text = f"Downloading tool...{progress}%"
                                progress_bar.value = progress
                            self.progress = progress
                        self.file_handle.close()
                        self.file_handle = None
                        expected_hash = TOOL_SHA256.get(platfom)
                        actual_hash = hasher.hexdigest()
                        if not expected_hash:
                            destination.unlink(missing_ok=True)
                            raise RuntimeError("No SHA256 hash defined for this platform")
                        if actual_hash.lower() != expected_hash.lower():
                            destination.unlink(missing_ok=True)
                            raise RuntimeError("SHA256 verification failed")
                        if platfom in ("linux", "darwin"):
                            destination.chmod(0o755)
                        setup.verify_vault()
        except RuntimeError as e:
            print(f"RuntimeError caught: {e}")
        except aiohttp.ClientError as e:
            print(f"HTTP Error: {e}")
        except Exception as e:
            print(f"{e}")


    def is_strong_password(self, password: str) -> str | None:
        if len(password) < 8:
            return "Password must be at least 8 characters long"
        if len(password) > 64:
            return "Password is too long"
        if " " in password:
            return "Password must not contain spaces"
        if not re.search(r"[A-Z]", password):
            return "Password must contain at least one uppercase letter"
        if not re.search(r"[a-z]", password):
            return "Password must contain at least one lowercase letter"
        if not re.search(r"[0-9]", password):
            return "Password must contain at least one number"
        if not re.search(r"[!@#$%^&*()_+=\-{}\[\]:;\"'<>,.?/\\|]", password):
            return "Password must contain at least one special character"
        return None
    

    def windows_screen_center(self, size):
        screen_size = self.app.screens[0].size
        screen_width, screen_height = screen_size
        window_width, window_height = size
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        return (x, y)
    

    def generate_address(self, coin):
        if coin == "BTCZ":
            from hdwallet.cryptocurrencies import BitcoinZ as Crypto
            derivation = "m/44'/177'/0'/0/0"
        elif coin == "LTZ":
            from hdwallet.cryptocurrencies import LitecoinZ as Crypto
            derivation = "m/44'/221'/0'/0/0"
        elif coin == "ZCL":
            from hdwallet.cryptocurrencies import ZClassic as Crypto
            derivation = "m/44'/147'/0'/0/0"
        elif coin == "ZER":
            from hdwallet.cryptocurrencies import Zero as Crypto
            derivation = "m/44'/323'/0'/0/0"
        elif coin == "GLINK":
            from hdwallet.cryptocurrencies import Gemlink as Crypto
            derivation = "m/44'/410'/0'/0/0"
        elif coin == "YEC":
            from hdwallet.cryptocurrencies import Ycash as Crypto
            derivation = "m/44'/347'/0'/0/0"
        else:
            from hdwallet.cryptocurrencies import Zcash as Crypto
            derivation = "m/44'/133'/0'/0/0"
        hdwallet = HDWallet(
            cryptocurrency=Crypto,
            hd=BIP32HD,
            network=Crypto.NETWORKS.MAINNET,
            language=BIP39_MNEMONIC_LANGUAGES.ENGLISH,
            public_key_type=PUBLIC_KEY_TYPES.COMPRESSED,
            passphrase=""
        ).from_entropy(
            entropy=BIP39Entropy(entropy=BIP39Entropy.generate(
                strength=BIP39_ENTROPY_STRENGTHS.TWO_HUNDRED_FIFTY_SIX
            ))
        ).from_derivation(
            derivation=CustomDerivation(
                path=derivation
            )
        )
        return hdwallet


