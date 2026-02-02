
import asyncio
import subprocess
import json

from toga import App, Window, Box, Label, Selection, MultilineTextInput, Button, TextInput
from toga.style.pack import Pack
from toga.constants import COLUMN, ROW, CENTER, END, BOLD
from toga.platform import current_platform

SATOSHIS = 100_000_000


class Result(Window):
    def __init__(self, title, raw_tx, utxos_payload = None):
        super().__init__(
            resizable=False,
            minimizable=False,
            size=(650,350)
        )

        self.title = title
        if current_platform == "windows":
            self.app.utils.apply_title_bar_mode(self)
        x, y = self.app.utils.windows_screen_center(self.size)
        self.position = (x,y)

        self.utxos = utxos_payload

        self.result_input = MultilineTextInput(
            value=raw_tx,
            style=Pack(
                flex=1,
                font_size=11
            )
        )

        self.save_button = Button(
            text="Save Utxos",
            style=Pack(
                width=120,
                font_size=12,
                font_weight=BOLD
            ),
            on_press=self.save_utxos
        )

        self.main_box = Box(
            style=Pack(
                flex=1,
                margin=5,
                direction=COLUMN,
                align_items=CENTER
            )
        )

        self.content = self.main_box
        self.main_box.add(
            self.result_input
        )
        if self.utxos:
            self.main_box.add(
                self.save_button
            )


    async def save_utxos(self, button):
        def on_result(widget, result):
            if result is False:
                return
            with open(result, "w", encoding="utf-8") as f:
                json.dump(self.utxos, f, indent=2)

        self.app.main_window.save_file_dialog(
            "Save utxos",
            f"utxos",
            file_types=["json"],
            on_result=on_result
        )


class GenerateMultisig(Box):
    def __init__(self, app:App, network):
        super().__init__(
            style=Pack(
                direction=COLUMN,
                flex=1
            )
        )

        self.app = app
        self.network = network

        self.required_signs_label = Label(
            text="Required Signs :",
            style=Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=10,
                margin_top=10
            )
        )

        self.required_signs_selection = Selection(
            accessor="required",
            items=["2", "3", "4", "5", "6", "7", "8", "9", "10"],
            style=Pack(
                font_size=12,
                margin_top=10
            )
        )

        self.required_signs_box = Box(
            style=Pack(
                direction=ROW,
                align_items=CENTER,
                margin=10
            )
        )

        self.publickeys_label = Label(
            text="Public Keys :",
            style=Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=10,
                margin_top=10
            )
        )

        self.publickeys_input = MultilineTextInput(
            placeholder="pubkey1, pubkey2, ...",
            style=Pack(
                margin_top=10,
                width=500
            )
        )

        self.publickeys_box = Box(
            style=Pack(
                direction=ROW,
                align_items=CENTER,
                margin=10
            )
        )

        self.generate_button = Button(
            text="Generate",
            style=Pack(
                width=120,
                font_size=12,
                font_weight=BOLD,
                margin_left=115,
                margin_bottom=20
            ),
            on_press=self.verify_inputs
        )

        self.buttons_box = Box(
            style=Pack(
                direction=ROW,
                flex=1,
                align_items=END
            )
        )

        self.add(
            self.required_signs_box,
            self.publickeys_box,
            self.buttons_box
        )
        self.required_signs_box.add(
            self.required_signs_label,
            self.required_signs_selection
        )
        self.publickeys_box.add(
            self.publickeys_label,
            self.publickeys_input
        )
        self.buttons_box.add(
            self.generate_button
        )


    async def generate_multisig(self, required, pubkeys):
        wallet_cli = str(self.app.utils.get_tool())
        cmd = [
            wallet_cli,
            "--network", self.network,
            "--gen-multisig",
            "--m", required,
            "--pubkeys", pubkeys
        ]
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if current_platform == "windows" else 0
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                return None, stderr.decode().strip() or "Generate multisig failed"
            result = stdout.decode().strip()
            return result, None
        except Exception as e:
            return None, f"Generate multisig error: {e}"

    
    async def verify_inputs(self, button):
        async def on_result(widget, result):
            if result is False:
                return
            multisig_info, error = await self.generate_multisig(required, ",".join(pubkeys_list))
            if error:
                self.app.main_window.error_dialog("Error", error)
                return
            with open(result, "w") as f:
                f.write(multisig_info)
            self.app.main_window.info_dialog("Success", "Multisig saved successfully!")
            self.publickeys_input.value = ""

        required = self.required_signs_selection.value.required
        pubkeys_list = [pk.strip() for pk in self.publickeys_input.value.split(",") if pk.strip()]
        if len(pubkeys_list) < int(required):
            self.app.main_window.error_dialog(
                "Error", f"You need at least {required} public keys, but only {len(pubkeys_list)} provided"
            )
            return

        self.app.main_window.save_file_dialog(
            "Save multisig",
            f"multisig_address",
            file_types=["txt"],
            on_result=on_result
        )



class CreateMultisig(Box):
    def __init__(self, app:App, network):
        super().__init__(
            style=Pack(
                direction=COLUMN,
                flex=1
            )
        )

        self.app = app
        self.network = network

        self.address_label = Label(
            text="Address :",
            style=Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=10,
                margin_top=10
            )
        )

        self.address_input = TextInput(
            placeholder="multisig address",
            style=Pack(
                font_size=12,
                width=500,
                margin_top=10,
                margin_left=41
            )
        )

        self.address_box = Box(
            style=Pack(
                direction=ROW,
                align_items=CENTER,
                margin=10
            )
        )

        self.script_label = Label(
            text="RedeemScript :",
            style=Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=10
            )
        )

        self.script_input = TextInput(
            placeholder="redeemScript (hex)",
            style=Pack(
                font_size=12,
                width=500
            )
        )

        self.script_box = Box(
            style=Pack(
                direction=ROW,
                align_items=CENTER,
                margin=10
            )
        )

        self.destination_label = Label(
            text="Destination :",
            style=Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=10
            )
        )

        self.destination_input = TextInput(
            placeholder="destination",
            style=Pack(
                font_size=12,
                width=500,
                margin_left=18
            )
        )

        self.destination_box = Box(
            style=Pack(
                direction=ROW,
                align_items=CENTER,
                margin=10
            )
        )

        self.amount_label = Label(
            text="Amount :",
            style=Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=10
            )
        )

        self.amount_input = TextInput(
            placeholder="0.00000000",
            style=Pack(
                text_align=CENTER,
                font_size=12,
                width=120,
                margin_left=41
            ),
            validators=[
                self.is_digit
            ]
        )

        self.amount_box = Box(
            style=Pack(
                direction=ROW,
                align_items=CENTER,
                margin=10
            )
        )

        self.fee_label = Label(
            text="Fee :",
            style=Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=10,
                margin_left=40
            )
        )

        self.fee_input = TextInput(
            placeholder="0.00000000",
            style=Pack(
                text_align=CENTER,
                font_size=12,
                width=120
            ),
            validators=[
                self.is_digit
            ]
        )

        self.create_button = Button(
            text="Build TX",
            style=Pack(
                width=120,
                font_size=12,
                font_weight=BOLD,
                margin_left=134,
                margin_bottom=20
            ),
            on_press=self.verify_inputs
        )

        self.buttons_box = Box(
            style=Pack(
                direction=ROW,
                flex=1,
                align_items=END
            )
        )

        self.add(
            self.address_box,
            self.script_box,
            self.destination_box,
            self.amount_box,
            self.buttons_box
        )
        self.address_box.add(
            self.address_label,
            self.address_input
        )
        self.script_box.add(
            self.script_label,
            self.script_input
        )
        self.destination_box.add(
            self.destination_label,
            self.destination_input
        )
        self.amount_box.add(
            self.amount_label,
            self.amount_input,
            self.fee_label,
            self.fee_input
        )
        self.buttons_box.add(
            self.create_button
        )

    async def build_multisig_transaction(self, redeemscript, inputs_to_use, destination, amount_sat, fee_sat):
        wallet_cli = str(self.app.utils.get_tool())
        utxos_payload = [
            {
                "txid": u["txid"],
                "vout": int(u["vout"]),
                "satoshis": int(round(float(u["amount"]) * 100_000_000))
            }
            for u in inputs_to_use
        ]
        block_height = await self.app.api.get_block_height()
        cmd = [
            wallet_cli,
            "--network", self.network,
            "--create-unsigned",
            "--redeem-script", redeemscript,
            "--utxos", json.dumps(utxos_payload),
            "--to", destination,
            "--amount", str(amount_sat),
            "--fee", str(fee_sat),
            "--blockheight", str(block_height)
        ]
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if current_platform == "windows" else 0
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                return None, None, stderr.decode().strip() or "Transaction build failed"
            raw_tx_hex = stdout.decode().strip()
            if not raw_tx_hex or len(raw_tx_hex) < 20:
                return None, None, "Invalid raw transaction returned"
            return utxos_payload, raw_tx_hex, None
        except Exception as e:
            return None, None, f"Transaction build error: {e}"
        

    async def verify_inputs(self, button):
        multisig_address = self.address_input.value.strip()
        if not multisig_address:
            self.app.main_window.error_dialog(
                "Error", "Multisig address is required"
            )
            self.address_input.focus()
            return
        redeemscript = self.script_input.value.strip()
        if not redeemscript:
            self.app.main_window.error_dialog(
                "Error", "redeemScript is required"
            )
            self.script_input.focus()
            return
        destination = self.destination_input.value.strip()
        if not destination:
            self.app.main_window.error_dialog(
                "Error", "Destination address is required"
            )
            self.destination_input.focus()
            return
        try:
            amount_sat = int(round(float(self.amount_input.value) * SATOSHIS))
            fee_sat = int(round(float(self.fee_input.value) * SATOSHIS))
        except (TypeError, ValueError):
            self.app.main_window.error_dialog(
                "Error", "Invalid amount or fee"
            )
            return
        if amount_sat <= 0 or fee_sat <= 0:
            self.app.main_window.error_dialog(
                "Error", "Amount and fee must be greater than zero"
            )
            return
        self.disable_create()
        addr_info = await self.app.api.get_address(destination)
        if not addr_info:
            self.app.main_window.error_dialog(
                "Error", "Invalid destination address"
            )
            self.enable_create()
            return
        utxos = await self.app.api.get_utxos(multisig_address)
        if not utxos:
            self.app.main_window.error_dialog(
                "Error", "No UTXOs available"
            )
            self.enable_create()
            return
        utxos.sort(key=lambda u: u.get("confirmations", 0), reverse=True)
        total_input = 0
        inputs_to_use = []
        for u in utxos:
            if u.get("confirmations", 0) <= 0:
                continue
            value_sat = int(round(float(u["amount"]) * SATOSHIS))
            inputs_to_use.append(u)
            total_input += value_sat
            if total_input >= amount_sat + fee_sat:
                break
        if total_input < amount_sat + fee_sat:
            self.app.main_window.error_dialog(
                "Error", f"Not enough {self.app.coin} for amount + fee"
            )
            self.enable_create()
            return
        utxos_payload, unsigned_raw_tx_hex, error = await self.build_multisig_transaction(
            redeemscript, inputs_to_use, destination, amount_sat, fee_sat
        )
        if error:
            self.app.main_window.error_dialog(
                "Error", error
            )
            self.enable_create()
            return
        self.enable_create()
        self.script_input.value = ""
        self.destination_input.value = ""
        self.address_input.value = ""
        self.amount_input.value = ""
        self.fee_input.value = ""
        result = Result("Unsigned Raw TX", unsigned_raw_tx_hex, utxos_payload)
        result.show()
        

    def is_digit(self, value):
        if not self.amount_input.value.replace('.', '', 1).isdigit():
            self.amount_input.value = ""
        if not self.fee_input.value.replace('.', '', 1).isdigit():
            self.fee_input.value = ""


    def disable_create(self):
        self.create_button.text = "Building..."
        self.create_button.enabled = False
        self.script_input.readonly = True
        self.destination_input.readonly = True
        self.address_input.readonly = True
        self.amount_input.readonly = True
        self.fee_input.readonly = True


    def enable_create(self):
        self.create_button.text = "Build TX"
        self.address_input.readonly = False
        self.script_input.readonly = False
        self.destination_input.readonly = False
        self.amount_input.readonly = False
        self.fee_input.readonly = False
        self.create_button.enabled = True



class PartialMultisig(Box):
    def __init__(self, app:App, network):
        super().__init__(
            style=Pack(
                direction=COLUMN,
                flex=1
            )
        )

        self.app = app
        self.network = network

        self.utxos_label = Label(
            text="Utxos file :",
            style=Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=10,
                margin_top=10
            )
        )

        self.utxos_input = TextInput(
            placeholder="utxos file",
            style=Pack(
                font_size=12,
                width=400,
                margin_top=10,
                margin_left=33
            )
        )

        self.utxos_button = Button(
            text="...",
            style=Pack(
                font_size=12,
                font_weight=BOLD,
                margin_top=10
            ),
            on_press=self.load_utxos
        )

        self.utxos_box = Box(
            style=Pack(
                direction=ROW,
                align_items=CENTER,
                margin=10
            )
        )

        self.script_label = Label(
            text="RedeemScript :",
            style=Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=10
            )
        )

        self.script_input = TextInput(
            placeholder="redeemScript (hex)",
            style=Pack(
                font_size=12,
                width=500
            )
        )

        self.script_box = Box(
            style=Pack(
                direction=ROW,
                align_items=CENTER,
                margin=10
            )
        )

        self.tx_label = Label(
            text="Raw TX :",
            style=Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=10
            )
        )

        self.tx_input = TextInput(
            placeholder="incompleted raw tx",
            style=Pack(
                font_size=12,
                width=500,
                margin_left=45
            )
        )

        self.tx_box = Box(
            style=Pack(
                direction=ROW,
                align_items=CENTER,
                margin=10
            )
        )

        self.key_label = Label(
            text="Key (WIF) :",
            style=Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=10
            )
        )

        self.key_input = TextInput(
            placeholder="enter wif key",
            style=Pack(
                font_size=12,
                width=500,
                margin_left=30
            )
        )

        self.key_box = Box(
            style=Pack(
                direction=ROW,
                align_items=CENTER,
                margin=10
            )
        )

        self.sign_button = Button(
            text="Sign TX",
            style=Pack(
                width=120,
                font_size=12,
                font_weight=BOLD,
                margin_left=134,
                margin_bottom=20
            ),
            on_press=self.verify_inputs
        )

        self.buttons_box = Box(
            style=Pack(
                direction=ROW,
                flex=1,
                align_items=END
            )
        )

        self.add(
            self.utxos_box,
            self.script_box,
            self.tx_box,
            self.key_box,
            self.buttons_box
        )
        self.utxos_box.add(
            self.utxos_label,
            self.utxos_input,
            self.utxos_button
        )
        self.script_box.add(
            self.script_label,
            self.script_input
        )
        self.tx_box.add(
            self.tx_label,
            self.tx_input
        )
        self.key_box.add(
            self.key_label,
            self.key_input
        )
        self.buttons_box.add(
            self.sign_button
        )


    async def sign_partial_transaction(self, raw_tx, redeemscript, utxos, wif):
        wallet_cli = str(self.app.utils.get_tool())
        cmd = [
            wallet_cli,
            "--network", self.network,
            "--sign",
            "--rawtx", raw_tx,
            "--redeem-script", redeemscript,
            "--wif", wif,
            "--utxos-file", utxos
        ]
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if current_platform == "windows" else 0
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                return None, stderr.decode().strip() or "Transaction sign failed"
            raw_tx_hex = stdout.decode().strip()
            if not raw_tx_hex or len(raw_tx_hex) < 20:
                return None, None, "Invalid raw transaction returned"
            return raw_tx_hex, None
        except Exception as e:
            return None, f"Transaction sign error: {e}"


    async def verify_inputs(self, button):
        utxos = self.utxos_input.value.strip()
        if not utxos:
            return
        redeemscript = self.script_input.value.strip()
        if not redeemscript:
            self.app.main_window.error_dialog(
                "Error", "redeemScript is required"
            )
            self.script_input.focus()
            return
        wif = self.key_input.value.strip()
        if not wif:
            self.app.main_window.error_dialog(
                "Error", "Key is required"
            )
            self.key_input.focus()
            return
        raw_tx = self.tx_input.value.strip()
        if not raw_tx:
            self.app.main_window.error_dialog(
                "Error", "Raw tx is required"
            )
            self.tx_input.focus()
            return
        self.disable_sign()
        signed_raw_tx_hex, error = await self.sign_partial_transaction(
            raw_tx, redeemscript, utxos, wif
        )
        if error:
            self.app.main_window.error_dialog(
                "Error", error
            )
            self.enable_sign()
            return
        self.enable_sign()
        self.script_input.value = ""
        self.utxos_input.value = ""
        self.key_input.value = ""
        self.tx_input.value = ""
        result = Result("Patrial signed TX", signed_raw_tx_hex)
        result.show()

        
        
    async def load_utxos(self, button):
        def on_result(widget, result):
            if result is False:
                return
            self.utxos_input.value = result

        self.app.main_window.open_file_dialog(
            "Load utxos",
            file_types=["json"],
            on_result=on_result
        )


    def disable_sign(self):
        self.sign_button.text = "Signing..."
        self.sign_button.enabled = False
        self.utxos_button.enabled = False
        self.script_input.readonly = True
        self.utxos_input.readonly = True
        self.key_input.readonly = True
        self.tx_input.readonly = True


    def enable_sign(self):
        self.sign_button.text = "Sign TX"
        self.utxos_input.readonly = False
        self.script_input.readonly = False
        self.key_input.readonly = False
        self.tx_input.readonly = False
        self.utxos_button.enabled = True
        self.sign_button.enabled = True



class FinalizeMultisig(Box):
    def __init__(self, app:App, network):
        super().__init__(
            style=Pack(
                direction=COLUMN,
                flex=1
            )
        )

        self.app = app
        self.network = network

        self.utxos_label = Label(
            text="Utxos file :",
            style=Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=10,
                margin_top=10
            )
        )

        self.utxos_input = TextInput(
            placeholder="utxos file",
            style=Pack(
                font_size=12,
                width=400,
                margin_top=10,
                margin_left=33
            )
        )

        self.utxos_button = Button(
            text="...",
            style=Pack(
                font_size=12,
                font_weight=BOLD,
                margin_top=10
            ),
            on_press=self.load_utxos
        )

        self.utxos_box = Box(
            style=Pack(
                direction=ROW,
                align_items=CENTER,
                margin=10
            )
        )

        self.script_label = Label(
            text="RedeemScript :",
            style=Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=10
            )
        )

        self.script_input = TextInput(
            placeholder="redeemScript (hex)",
            style=Pack(
                font_size=12,
                width=500
            )
        )

        self.script_box = Box(
            style=Pack(
                direction=ROW,
                align_items=CENTER,
                margin=10
            )
        )

        self.tx_label = Label(
            text="Raw TX :",
            style=Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=10
            )
        )

        self.tx_input = TextInput(
            placeholder="incompleted raw tx",
            style=Pack(
                font_size=12,
                width=500,
                margin_left=45
            )
        )

        self.tx_box = Box(
            style=Pack(
                direction=ROW,
                align_items=CENTER,
                margin=10
            )
        )

        self.key_label = Label(
            text="Key (WIF) :",
            style=Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=10
            )
        )

        self.key_input = TextInput(
            placeholder="enter wif key",
            style=Pack(
                font_size=12,
                width=500,
                margin_left=30
            )
        )

        self.key_box = Box(
            style=Pack(
                direction=ROW,
                align_items=CENTER,
                margin=10
            )
        )

        self.sign_button = Button(
            text="Sign TX",
            style=Pack(
                width=120,
                font_size=12,
                font_weight=BOLD,
                margin_left=134,
                margin_bottom=20
            ),
            on_press=self.verify_inputs
        )

        self.buttons_box = Box(
            style=Pack(
                direction=ROW,
                flex=1,
                align_items=END
            )
        )

        self.add(
            self.utxos_box,
            self.script_box,
            self.tx_box,
            self.key_box,
            self.buttons_box
        )
        self.utxos_box.add(
            self.utxos_label,
            self.utxos_input,
            self.utxos_button
        )
        self.script_box.add(
            self.script_label,
            self.script_input
        )
        self.tx_box.add(
            self.tx_label,
            self.tx_input
        )
        self.key_box.add(
            self.key_label,
            self.key_input
        )
        self.buttons_box.add(
            self.sign_button
        )

        self.add(
            self.utxos_box
        )
        self.utxos_box.add(
            self.utxos_label,
            self.utxos_input,
            self.utxos_button
        )

    
    async def final_sign_transaction(self, raw_tx, redeemscript, utxos, wif):
        wallet_cli = str(self.app.utils.get_tool())
        cmd = [
            wallet_cli,
            "--network", self.network,
            "--finalize",
            "--rawtx", raw_tx,
            "--redeem-script", redeemscript,
            "--wif", wif,
            "--utxos-file", utxos
        ]
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if current_platform == "windows" else 0
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                return None, stderr.decode().strip() or "Transaction sign failed"
            raw_tx_hex = stdout.decode().strip()
            if not raw_tx_hex or len(raw_tx_hex) < 20:
                return None, None, "Invalid raw transaction returned"
            return raw_tx_hex, None
        except Exception as e:
            return None, f"Transaction sign error: {e}"


    async def verify_inputs(self, button):
        utxos = self.utxos_input.value.strip()
        if not utxos:
            return
        redeemscript = self.script_input.value.strip()
        if not redeemscript:
            self.app.main_window.error_dialog(
                "Error", "redeemScript is required"
            )
            self.script_input.focus()
            return
        wif = self.key_input.value.strip()
        if not wif:
            self.app.main_window.error_dialog(
                "Error", "Key is required"
            )
            self.key_input.focus()
            return
        raw_tx = self.tx_input.value.strip()
        if not raw_tx:
            self.app.main_window.error_dialog(
                "Error", "Raw tx is required"
            )
            self.tx_input.focus()
            return
        self.disable_sign()
        signed_raw_tx_hex, error = await self.final_sign_transaction(
            raw_tx, redeemscript, utxos, wif
        )
        if error:
            self.app.main_window.error_dialog(
                "Error", error
            )
            self.enable_sign()
            return
        self.enable_sign()
        self.script_input.value = ""
        self.utxos_input.value = ""
        self.key_input.value = ""
        self.tx_input.value = ""
        result = Result("Patrial signed TX", signed_raw_tx_hex)
        result.show()

        
        
    async def load_utxos(self, button):
        def on_result(widget, result):
            if result is False:
                return
            self.utxos_input.value = result

        self.app.main_window.open_file_dialog(
            "Load utxos",
            file_types=["json"],
            on_result=on_result
        )


    def disable_sign(self):
        self.sign_button.text = "Signing..."
        self.sign_button.enabled = False
        self.utxos_button.enabled = False
        self.script_input.readonly = True
        self.utxos_input.readonly = True
        self.key_input.readonly = True
        self.tx_input.readonly = True


    def enable_sign(self):
        self.sign_button.text = "Sign TX"
        self.utxos_input.readonly = False
        self.script_input.readonly = False
        self.key_input.readonly = False
        self.tx_input.readonly = False
        self.utxos_button.enabled = True
        self.sign_button.enabled = True