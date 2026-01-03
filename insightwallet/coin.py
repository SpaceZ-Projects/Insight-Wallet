
import asyncio
import subprocess
from datetime import datetime, timezone
import json

from toga import App, Box, ImageView, Button, Label, Table, TextInput, OptionContainer, OptionItem, Divider, ProgressBar, PasswordInput
from toga.constants import COLUMN, ROW, CENTER, BOLD, ITALIC, Direction, END
from toga.style.pack import Pack
from toga.colors import RED, GRAY, GREEN
from toga.platform import current_platform


SATOSHIS = 100_000_000
FEE_RATE = 1


class Coin(Box):
    def __init__(self, app:App, address):
        super().__init__(
            style=Pack(
                direction=COLUMN,
                flex=1,
                align_items=CENTER
            )
        )

        self.app = app
        self.address = address

        coin_info = self.app.utils.get_coin(self.app.coin)
        self.name = coin_info["name"]
        self.network = coin_info["network"]
        self.app.api.base_url = coin_info["api"].rstrip("/")

        self.transactions_data = []
        self.current_height = 0
        self.toggle = True

        if current_platform == "linux":
            amount_label_style = Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=37
            )
            fee_label_style = Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=73
            )
        else:
            amount_label_style = Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=33
            )
            fee_label_style = Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=65
            )

        self.coin_logo = ImageView(
            image=f"resources/{self.app.coin}.png",
            style=Pack(
                width=50,
                margin_left=10,
                margin_top=10
            )
        )

        self.coin_label = Label(
            text=self.name,
            style=Pack(
                font_size=17,
                font_weight=BOLD,
                flex=1,
                margin_left=10
            )
        )

        divider_r = Divider(
            direction=Direction.VERTICAL,
            style=Pack(
                height=50
            )
        )

        self.key_button = Button(
            text="🔑",
            style=Pack(
                font_size=12,
                margin_right=10
            ),
            on_press=self.export_key
        )

        self.balance_label = Label(
            text="Balance : 0.00000000",
            style=Pack(
                font_size=10,
                font_weight=BOLD
            )
        )

        self.unconfirmed_label = Label(
            text="Unconf. : 0.00000000",
            style=Pack(
                color=GRAY,
                font_size=10,
                font_weight=BOLD
            )
        )

        self.balances_box = Box(
            style=Pack(
                direction=COLUMN,
                margin_right=20
            )
        )

        self.blocks_label = Label(
            text="Height : 0",
            style=Pack(
                font_size=10,
                font_weight=BOLD,
                margin_right=10
            )
        )

        self.balance_panel = Box(
            style=Pack(
                direction=ROW,
                height=70,
                align_items=CENTER
            )
        )

        self.transaction_table = Table(
            headings=["_", "_", "_", "_"],
            accessors={"type", "txid", "amount", "timestamp"},
            style=Pack(
                font_size=10,
                flex=1
            )
        )

        self.transaction_page = Box(
            style=Pack(
                direction=COLUMN,
                flex=1
            )
        )

        self.transaction_option = OptionItem(
            text="  Transactions  ",
            content=self.transaction_page
        )

        self.address_label = Label(
            text=self.address,
            style=Pack(
                text_align=CENTER,
                font_size=12,
                margin_top=10
            )
        )

        qr_code = self.app.utils.qr_generate(self.address)

        self.qr_view = ImageView(
            image=qr_code,
            style=Pack(width=200, height=200)
        )

        self.copy_button = Button(
            text="Copy",
            style=Pack(
                font_size=12,
                width=100
            ),
            on_press=self.copy_address
        )

        self.receive_buttons = Box(
            style=Pack(
                direction=ROW,
                align_items=CENTER,
                gap=5
            )
        )

        self.receive_page = Box(
            style=Pack(
                direction=COLUMN,
                flex=1,
                align_items=CENTER,
                justify_content=CENTER,
                gap=10
            )
        )

        self.receive_option = OptionItem(
            text="  Receive  ",
            content=self.receive_page
        )

        self.destination_label = Label(
            text="Destination :",
            style=Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=10,
                margin_top=10
            )
        )

        self.destination_input = TextInput(
            placeholder=" enter address",
            style=Pack(
                font_size=12,
                width=500,
                margin_top=10
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
            style=amount_label_style
        )

        self.amount_input = TextInput(
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

        self.max_button = Button(
            text="Max",
            style=Pack(
                margin_left=10
            ),
            on_press=self.max_amount
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
            style=fee_label_style
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

        self.calcul_button = Button(
            text="Calculate",
            style=Pack(
                margin_left=10
            ),
            on_press=self.calcul_fee
        )

        self.fee_box = Box(
            style=Pack(
                direction=ROW,
                align_items=CENTER,
                margin=10
            )
        )

        self.send_button = Button(
            text="Broadcast",
            style=Pack(
                width=120,
                font_size=12,
                font_weight=BOLD,
                margin_left=115,
                margin_bottom=20
            ),
            on_press=self.verify_inputs
        )

        self.send_progress = ProgressBar(
            max=100,
            style=Pack(
                width=100,
                margin_left=10,
                margin_bottom=23
            )
        )

        self.send_buttons = Box(
            style=Pack(
                direction=ROW,
                flex=1,
                align_items=END
            )
        )

        self.send_page = Box(
            style=Pack(
                direction=COLUMN,
                flex=1
            )
        )

        self.send_option = OptionItem(
            text="  Send  ",
            content=self.send_page
        )

        self.key_label = Label(
            text="Key (WIF) :",
            style=Pack(
                font_size=12,
                text_align=CENTER,
                margin_right=10,
                margin_top=10
            )
        )

        self.key_input = PasswordInput(
            placeholder=" enter wif key",
            style=Pack(
                font_size=12,
                width=500,
                margin_top=10
            )
        )

        self.key_box = Box(
            style=Pack(
                direction=ROW,
                align_items=CENTER,
                margin=10
            )
        )

        self.redeem_address = Label(
            text="",
            style=Pack(
                color=GREEN,
                font_size=11,
                font_weight=BOLD,
                text_align=CENTER,
                margin_right=10,
                margin_top=10
            )
        )

        self.redeem_balance = Label(
            text="",
            style=Pack(
                font_size=10,
                font_weight=BOLD,
                text_align=CENTER,
                margin_right=10,
                margin_top=10
            )
        )

        self.redeem_box = Box(
            style=Pack(
                direction=ROW,
                align_items=CENTER,
                margin=10
            )
        )

        self.redeem_button = Button(
            text="Verify",
            style=Pack(
                width=120,
                font_size=12,
                font_weight=BOLD,
                margin_left=115,
                margin_bottom=20
            ),
            on_press=self.verify_redeem_key
        )

        self.reset_button = Button(
            text="⟳",
            style=Pack(
                font_size=12,
                font_weight=BOLD,
                margin_left=10,
                margin_bottom=20
            ),
            on_press=self.reset_redeem_page
        )

        self.redeem_buttons = Box(
            style=Pack(
                direction=ROW,
                flex=1,
                align_items=END
            )
        )

        self.redeem_page = Box(
            style=Pack(
                direction=COLUMN,
                flex=1
            )
        )

        self.redeem_option = OptionItem(
            text=" Redeem ",
            content=self.redeem_page
        )

        self.coin_container = OptionContainer(
            style=Pack(
                font_size=12,
                font_style=ITALIC,
                font_weight=BOLD,
                flex=1,
                margin_left=10,
                margin_bottom=10,
                margin_right=10
            ),
            content= [
                self.transaction_option,
                self.receive_option,
                self.send_option,
                self.redeem_option
            ]
        )

        self.add(
            self.balance_panel,
            self.coin_container
        )
        self.balance_panel.add(
            self.coin_logo,
            self.coin_label,
            self.balances_box,
            divider_r,
            self.blocks_label
        )
        self.balances_box.add(
            self.balance_label,
            self.unconfirmed_label
        )

        self.receive_page.add(
            self.address_label,
            self.qr_view,
            self.receive_buttons
        )
        self.receive_buttons.add(
            self.copy_button,
            self.key_button
        )

        self.send_page.add(
            self.destination_box,
            self.amount_box,
            self.fee_box,
            self.send_buttons
        )
        self.destination_box.add(
            self.destination_label,
            self.destination_input
        )
        self.amount_box.add(
            self.amount_label,
            self.amount_input,
            self.max_button
        )
        self.send_buttons.add(
            self.send_button
        )
        self.fee_box.add(
            self.fee_label,
            self.fee_input,
            self.calcul_button
        )

        self.redeem_page.add(
            self.key_box,
            self.redeem_box,
            self.redeem_buttons
        )
        self.key_box.add(
            self.key_label,
            self.key_input
        )
        self.redeem_buttons.add(
            self.redeem_button
        )

        self.set_table_context_menu()
        self.app.loop.create_task(self.load_transactions())


    def set_table_context_menu(self):
        platfrom = current_platform
        if platfrom == "windows":
            import System.Windows.Forms as Forms
            context_menu = Forms.ContextMenuStrip()
            view_command = Forms.ToolStripMenuItem()
            view_command.Text = "Open in explorer"
            view_command.Click += self.open_in_explorer
            context_menu.Items.Add(view_command)
            self.transaction_table._impl.native.ContextMenuStrip = context_menu
        elif platfrom == "linux":
            from gi.repository import Gtk, Gdk
            context_menu = Gtk.Menu()
            view_command = Gtk.MenuItem()
            view_command.set_label("Open in explorer")
            view_command.connect("activate", self.open_in_explorer)
            context_menu.append(view_command)
            context_menu.show_all()
            tree = self.transaction_table._impl.native.get_child()
            def on_button_press(widget, event):
                if event.button == Gdk.BUTTON_SECONDARY:
                    context_menu.popup_at_pointer(event)
                    return True
                return False
            tree.connect("button-press-event", on_button_press)


    def open_in_explorer(self, *args):
        url = self.app.api.base_url.rstrip("/")
        blockbook_coins = {"ZEC", "YEC"}
        if self.app.coin in blockbook_coins:
            url = url.rstrip("/api") + "/api/v2"
        elif url.endswith("/api"):
            url = url[:-4]
        native = self.transaction_table._impl.native
        indices = []
        if hasattr(native, "SelectedIndices"):
            indices = native.SelectedIndices
        else:
            from gi.repository import Gtk
            treeview = native.get_child()
            if not isinstance(treeview, Gtk.TreeView):
                return
            selection = treeview.get_selection()
            m, paths = selection.get_selected_rows()
            indices = [path.get_indices()[0] for path in paths]
        for index in indices:
            txid = self.transactions_data[index]
            full_url = url + "/tx/" + txid
            import webbrowser
            webbrowser.open(full_url)


    async def load_transactions(self):
        transactions = self.app.vault.get_transactions(self.app.account, self.app.password, self.app.coin)
        transactions.sort(key=lambda tx: tx.get("timestamp", 0), reverse=True)
        for tx in transactions:
            tx_type = tx.get('type')
            txid = tx.get('txid')
            amount = tx.get('amount')
            timestamp = tx.get('timestamp')
            amount = self.app.utils.format_balance(amount)
            timestamp = datetime.fromtimestamp(int(timestamp)).strftime("%Y-%m-%d %H:%M:%S")
            data = {"type": tx_type.upper(), "txid": txid, "amount": amount, "timestamp": timestamp}
            self.transaction_table.data.append(data)
            self.transactions_data.append(txid)

        self.transaction_page.add(self.transaction_table)
        self.transaction_table.style.flex = 1
        self.app.loop.create_task(self.fetch_network_info())


    async def fetch_network_info(self):
        while True:
            if not self.toggle:
                return
            blocks = await self.app.api.get_block_height()
            if blocks:
                self.blocks_label.text = f"Height : {blocks}"
                if self.current_height < blocks:
                    self.app.loop.create_task(self.fetch_transactions())
                self.current_height = blocks
            addr_info = await self.app.api.get_address(self.address)
            if addr_info:
                confirmed = addr_info.get("balance", 0)
                unconfirmed = addr_info.get("unconfirmedBalance", 0)
                if float(unconfirmed) > 0:
                    self.unconfirmed_label.text = f"Unconf. : +{self.app.utils.format_balance(unconfirmed)}"
                    self.unconfirmed_label.style.color = GREEN
                elif float(unconfirmed) < 0:
                    self.unconfirmed_label.text = f"Unconf. : -{self.app.utils.format_balance(abs(unconfirmed))}"
                    self.unconfirmed_label.style.color = RED
                else:
                    self.unconfirmed_label.text = "Unconf. : 0.00000000"
                    self.unconfirmed_label.style.color = GRAY
                spendable = float(confirmed)
                if float(unconfirmed) < 0:
                    spendable += float(unconfirmed)
                spendable = max(spendable, 0)
                self.balance_label.text = f"Balance : {self.app.utils.format_balance(spendable)}"

            await asyncio.sleep(15)


    def classify_tx(self, tx: dict, address: str):
        sent = 0.0
        received = 0.0
        for vin in tx.get("vin", []):
            if vin.get("addr") == address:
                sent += float(vin.get("value", 0))

        for vout in tx.get("vout", []):
            spk = vout.get("scriptPubKey", {})
            addresses = spk.get("addresses", [])
            if address in addresses:
                received += float(vout.get("value", 0))
        net = received - sent
        if net > 0:
            return "receive", net
        elif net < 0:
            return "send", abs(net)
        else:
            return None, 0
        

    def get_tx_timestamp(self, tx: dict) -> int:
        if tx.get("time"):
            return int(tx["time"])
        if tx.get("blocktime"):
            return int(tx["blocktime"])
        return int(datetime.now(timezone.utc).timestamp())


    async def fetch_transactions(self):
        transactions = await self.app.api.get_transactions(self.address)
        transactions.sort(
            key=lambda tx: self.get_tx_timestamp(tx),
            reverse=True
        )
        for tx in transactions:
            txid = tx.get("txid")
            if txid not in self.transactions_data:
                tx_type, amount = self.classify_tx(tx, self.address)
                if not tx_type:
                    continue
                timestamp = self.get_tx_timestamp(tx)
                self.app.vault.add_transaction(
                    self.app.account, self.app.password, self.app.coin, tx_type, txid, amount, timestamp
                )
                amount = self.app.utils.format_balance(amount)
                timestamp = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                data = {"type": tx_type.upper(), "txid": txid, "amount": amount, "timestamp": timestamp}
                self.transaction_table.data.insert(0, data)
                self.transactions_data.insert(0, txid)


    def copy_address(self, button):
        self.app.utils.copy_to_clipboard(self.address)


    def export_key(self, button):
        def on_result(widget, path):
            if not path:
                return
            success = self.app.vault.export_coin_data(
                account=self.app.account,
                password=self.app.password,
                coin=self.app.coin,
                output_path=path
            )
            if not success:
                self.app.main_window.error_dialog(
                    "Export failed",
                    "Unable to export coin data."
                )
                return
            self.app.main_window.info_dialog(
                "Export complete",
                f"{self.app.coin} data was successfully exported\n{path}"
            )
        def on_confirm(widget, result):
            if result is False:
                return
            self.app.main_window.save_file_dialog(
                "Export coin",
                f"{self.app.account}_{self.app.coin}_export",
                file_types=["txt"],
                on_result=on_result
            )
        self.app.main_window.confirm_dialog(
            "Security warning",
            "This file will contain PRIVATE KEY.\n\n"
            "Anyone with access can spend your funds.\n\n"
            "Do you want to continue?",
            on_result=on_confirm
        )


    def is_digit(self, value):
        if not self.amount_input.value.replace('.', '', 1).isdigit():
            self.amount_input.value = ""
        if not self.fee_input.value.replace('.', '', 1).isdigit():
            self.fee_input.value = ""


    def disable_send(self):
        self.send_buttons.add(self.send_progress)
        self.send_progress.value = 5
        self.send_button.text = "Sending..."
        self.send_button.enabled = False
        self.destination_input.readonly = True
        self.amount_input.readonly = True
        self.fee_input.readonly = True


    def enable_send(self):
        self.send_buttons.remove(self.send_progress)
        self.send_button.text = "Broadcast"
        self.destination_input.readonly = False
        self.amount_input.readonly = False
        self.fee_input.readonly = False
        self.send_button.enabled = True


    async def build_transaction(self, wif, inputs_to_use, destination, amount_sat, fee_sat):
        if not wif:
            return None, "Failed to unlock private key"
        self.send_progress.value = 10
        network = self.name.lower()
        wallet_cli = str(self.app.utils.get_tool())
        utxos = [
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
            "--network", network,
            "--wif", wif,
            "--to", destination,
            "--amount", str(amount_sat),
            "--fee", str(fee_sat),
            "--utxos", json.dumps(utxos),
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
                return None, stderr.decode().strip() or "Transaction build failed"
            raw_tx_hex = stdout.decode().strip()
            if not raw_tx_hex or len(raw_tx_hex) < 20:
                return None, "Invalid raw transaction returned"
            self.send_progress.value = 50
            return raw_tx_hex, None
        except Exception as e:
            return None, f"Transaction build error: {e}"
        

    async def min_fee(self, amount_sat):
        utxos = await self.app.api.get_utxos(self.address)
        if not utxos:
            return None, None
        utxos.sort(key=lambda u: u.get("confirmations", 0), reverse=True)
        total_input = 0
        inputs_count = 0
        outputs_count = 1
        fee_sat = 0
        def estimate_tx_size(inputs, outputs):
            return 10 + inputs * 148 + outputs * 34
        for u in utxos:
            if u.get("confirmations", 0) <= 0:
                continue
            value_sat = int(round(float(u["amount"]) * SATOSHIS))
            total_input += value_sat
            inputs_count += 1
            fee_sat = estimate_tx_size(inputs_count, outputs_count) * FEE_RATE
            if total_input >= amount_sat + fee_sat:
                break
        return total_input, fee_sat
        

    async def max_amount(self, button):
        addr_info = await self.app.api.get_address(self.address)
        if not addr_info:
            return
        confirmed = addr_info.get("balance", 0)
        unconfirmed = addr_info.get("unconfirmedBalance", 0)
        spendable = float(confirmed)
        if float(unconfirmed) < 0:
            spendable += float(unconfirmed)
        spendable = max(spendable, 0)
        if float(spendable) <= 0:
            return
        self.amount_input.value = self.app.utils.format_balance(spendable)


    async def calcul_fee(self, button):
        try:
            amount_sat = int(round(float(self.amount_input.value) * SATOSHIS))
        except (TypeError, ValueError):
            self.app.main_window.error_dialog(
                "Error", "Invalid amount"
            )
            return
        if amount_sat <= 0:
            return
        total_input, fee_sat = await self.min_fee(amount_sat)
        if not total_input and not fee_sat:
            self.app.main_window.error_dialog(
                "Error", "No UTXOs available"
            )
            return
        if total_input < amount_sat + fee_sat:
            amount_sat = total_input - fee_sat
            self.amount_input.value = f"{amount_sat / SATOSHIS:.8f}"
        self.fee_input.value = f"{fee_sat / SATOSHIS:.8f}"


    async def verify_inputs(self, button):
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
        self.disable_send()
        addr_info = await self.app.api.get_address(destination)
        if not addr_info:
            self.app.main_window.error_dialog(
                "Error", "Invalid destination address"
            )
            self.enable_send()
            return
        utxos = await self.app.api.get_utxos(self.address)
        if not utxos:
            self.app.main_window.error_dialog(
                "Error", "No UTXOs available"
            )
            self.enable_send()
            return
        utxos.sort(key=lambda u: u.get("confirmations", 0), reverse=True)
        total_input = 0
        inputs_to_use = []
        for u in utxos:
            if u.get("confirmations", 0) <= 0:
                continue
            value_sat = int(round(float(u["amount"]) * 100_000_000))
            inputs_to_use.append(u)
            total_input += value_sat
            if total_input >= amount_sat + fee_sat:
                break
        if total_input < amount_sat + fee_sat:
            self.app.main_window.error_dialog(
                "Error", f"Not enough {self.app.coin} for amount + fee"
            )
            self.enable_send()
            return
        wif = self.app.vault.get_coin_wif(
            self.app.account,
            self.app.password,
            self.app.coin
        )
        raw_tx_hex, error = await self.build_transaction(wif, inputs_to_use, destination, amount_sat, fee_sat)
        if error:
            self.app.main_window.error_dialog(
                "Error", error
            )
            self.enable_send()
            return
        success, error = await self.app.api.broadcast_tx(raw_tx_hex)
        if success:
            async def on_result(widget, result):
                self.destination_input.value = ""
                self.amount_input.value = ""
                self.fee_input.value = ""
                self.enable_send()
                await self.fetch_transactions()
            self.send_progress.value = 100
            self.app.main_window.info_dialog(
                "Success", "Transaction broadcast successfully",
                on_result=on_result
            )
        else:
            self.app.main_window.error_dialog(
                "Broadcast failed", error or "Unknown error"
            )
            self.enable_send()
        

    def disable_redeem(self):
        self.redeem_button.enabled = False
        self.redeem_buttons.remove(self.reset_button)
        self.redeem_buttons.add(self.send_progress)
        self.send_progress.value = 5
        self.redeem_button.text = "Sending..."

    def enable_redeem(self):
        self.redeem_button.enabled = True
        self.redeem_buttons.remove(self.send_progress)
        self.redeem_buttons.add(self.reset_button)
        self.redeem_button.text = "Redeem"


    async def verify_redeem_key(self, button):
        wif = self.key_input.value.strip()
        if not wif:
            self.app.main_window.error_dialog(
                "Error", "Key is required"
            )
            self.key_input.focus()
            return
        if current_platform == "darwin":
            address = await self.address_from_wif(wif)
        else:
            address = self.app.utils.address_from_wif(self.app.coin, wif)
        if not address:
            self.app.main_window.error_dialog(
                "Error", "Invalid wallet import format (WIF)"
            )
            return
        self.key_input.readonly = True
        self.redeem_box.add(
            self.redeem_address,
            self.redeem_balance
        )
        self.redeem_buttons.add(self.reset_button)
        self.redeem_address.text = address
        await self.get_redeem_balance(address, wif)


    async def address_from_wif(self, wif):
        wallet_cli = str(self.app.utils.get_tool())
        cmd = [wallet_cli, "--network", self.network, "--address-from-wif", "--wif", wif]
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
                self.app.main_window.error_dialog(
                    "Error", stderr.decode().strip()
                )
                return None
            address = stdout.decode().strip()
            return address
        except Exception as e:
            self.app.main_window.error_dialog(
                "Error", e
            )


    async def get_redeem_balance(self, address, wif):
        addr_info = await self.app.api.get_address(address)
        if addr_info:
            confirmed = self.app.utils.format_balance(addr_info.get("balance", 0))
            unconfirmed = self.app.utils.format_balance(addr_info.get("unconfirmedBalance", 0))
            self.redeem_balance.text = f"Bal. :{confirmed} | Unconf. :{unconfirmed}"
            if float(confirmed) > 0:
                self.redeem_button.text = "Redeem"
                self.redeem_button.on_press = lambda widget, address=address, wif=wif: self.on_redeem_balance(address, wif)


    def on_redeem_balance(self, address, wif):
        self.disable_redeem()
        destination = self.app.vault.get_coin_address(self.app.account, self.app.password, self.app.coin)
        self.app.loop.create_task(self.collet_redeem_utxos(destination, address, wif))
        

    async def collet_redeem_utxos(self, destination, address, wif):
        utxos = await self.app.api.get_utxos(address)
        if not utxos:
            self.app.main_window.error_dialog(
                "Error", "No UTXOs available"
            )
            self.enable_redeem()
            return
        utxos.sort(key=lambda u: u.get("confirmations", 0), reverse=True)
        total_input = 0
        inputs_to_use = []
        for u in utxos:
            if u.get("confirmations", 0) <= 0:
                continue
            value_sat = int(round(float(u["amount"]) * 100_000_000))
            inputs_to_use.append(u)
            total_input += value_sat
        fee_sat = 1_000
        if total_input <= fee_sat:
            self.app.main_window.error_dialog(
                "Error", "Insufficient balance to cover transaction fee"
            )
            self.enable_redeem()
            return
        amount_sat = total_input - fee_sat
        raw_tx_hex, error = await self.build_transaction(wif, inputs_to_use, destination, amount_sat, fee_sat)
        if error:
            self.app.main_window.error_dialog(
                "Error", error
            )
            self.enable_redeem()
            return
        success, error = await self.app.api.broadcast_tx(raw_tx_hex)
        if success:
            async def on_result(widget, result):
                self.redeem_buttons.remove(self.send_progress)
                self.clear_redeem_page()
                await self.fetch_transactions()
            self.send_progress.value = 100
            self.app.main_window.info_dialog(
                "Success", "Transaction broadcast successfully",
                on_result=on_result
            )
        else:
            self.app.main_window.error_dialog(
                "Broadcast failed", error or "Unknown error"
            )
            self.enable_redeem()


    def clear_redeem_page(self):
        self.redeem_box.clear()
        self.key_input.value = ""
        self.key_input.readonly = False
        self.redeem_button.text = "Verify"
        self.redeem_button.on_press = self.verify_redeem_key
        self.redeem_button.enabled = True


    def reset_redeem_page(self, button):
        self.redeem_buttons.remove(button)
        self.clear_redeem_page()

