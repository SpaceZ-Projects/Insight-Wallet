
import asyncio
import subprocess
from datetime import datetime, timezone
import json

from toga import App, Box, ImageView, Button, Label, Table, TextInput, OptionContainer, OptionItem, Divider
from toga.constants import COLUMN, ROW, CENTER, BOLD, ITALIC, Direction
from toga.style.pack import Pack
from toga.colors import RED, GRAY, GREEN
from toga.platform import current_platform


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
        self.app.api.base_url = coin_info["api"].rstrip("/")

        self.transactions_data = []
        self.current_height = 0
        self.toggle = True

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
            text="Balance :",
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
            text="Height :",
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
                margin_right=10
            )
        )

        self.destination_input = TextInput(
            placeholder=" enter address",
            style=Pack(
                font_size=12,
                flex=1
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
                margin_right=33
            )
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
                margin_right=65
            )
        )

        self.fee_input = TextInput(
            placeholder="0.00001000",
            style=Pack(
                text_align=CENTER,
                font_size=12,
                width=120
            ),
            validators=[
                self.is_digit
            ]
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
                margin_left=450
            ),
            on_press=self.verify_inputs
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
                self.send_option
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
            self.send_button
        )
        self.destination_box.add(
            self.destination_label,
            self.destination_input
        )
        self.amount_box.add(
            self.amount_label,
            self.amount_input
        )
        self.fee_box.add(
            self.fee_label,
            self.fee_input
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


    def open_in_explorer(self, event, sender):
        url = self.app.api.base_url.rstrip("/")
        blockbook_coins = {"ZEC", "YEC"}
        if self.app.coin in blockbook_coins:
            url = url.rstrip("/api") + "/api/v2"
        elif url.endswith("/api"):
            url = url[:-4]
        lv = self.transaction_table._impl.native
        for index in lv.SelectedIndices:
            txid = self.transactions_data[index]
            full_url = url + "/tx/" + txid
            import webbrowser
            webbrowser.open(full_url)


    
    async def load_transactions(self):
        self.fee_input.value = "0.00001000"
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
                    self.unconfirmed_label.text = (
                        f"Unconf. : +{self.app.utils.format_balance(unconfirmed)}"
                    )
                    self.unconfirmed_label.style.color = GREEN
                elif float(unconfirmed) < 0:
                    self.unconfirmed_label.text = (
                        f"Unconf. : -{self.app.utils.format_balance(abs(unconfirmed))}"
                    )
                    self.unconfirmed_label.style.color = RED
                else:
                    self.unconfirmed_label.text = "Unconf. : 0.00000000"
                    self.unconfirmed_label.style.color = GRAY
                spendable = float(confirmed)
                if float(unconfirmed) < 0:
                    spendable += float(unconfirmed)
                spendable = max(spendable, 0)
                self.balance_label.text = (
                    f"Balance : {self.app.utils.format_balance(spendable)}"
                )

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
        self.send_button.text = "Sending..."
        self.send_button.enabled = False
        self.destination_input.readonly = True
        self.amount_input.readonly = True
        self.fee_input.readonly = True


    def enable_send(self):
        self.send_button.text = "Broadcast"
        self.destination_input.readonly = False
        self.amount_input.readonly = False
        self.fee_input.readonly = False
        self.send_button.enabled = True


    async def verify_inputs(self, button):
        destination = self.destination_input.value.strip()
        try:
            amount_sat = int(float(self.amount_input.value) * 100_000_000)
            fee_sat = int(float(self.fee_input.value) * 100_000_000)
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
        addr_info = await self.app.api.get_address(destination)
        if not addr_info:
            self.app.main_window.error_dialog(
                "Error", "Invalid destination address"
            )
            return
        utxos = await self.app.api.get_utxos(self.address)
        total_input = 0
        inputs_to_use = []
        for u in utxos:
            if u.get("confirmations", 0) == 0:
                continue
            value_sat = int(float(u["amount"]) * 100_000_000)
            inputs_to_use.append(u)
            total_input += value_sat
            if total_input >= amount_sat + fee_sat:
                break
        if total_input < amount_sat + fee_sat:
            self.app.main_window.error_dialog(
                "Error", f"Not enough {self.app.coin} for amount + fee"
            )
            return
        self.disable_send()
        await self.send_transaction(inputs_to_use, destination, amount_sat, fee_sat)


    async def send_transaction(self, inputs_to_use, destination, amount_sat, fee_sat):
        wif = self.app.vault.get_coin_wif(self.app.account, self.app.password, self.app.coin)
        network = self.name.lower()
        mktx = str(self.app.utils.get_tool())
        utxos = [
            {
                "txid": u["txid"],
                "vout": int(u["vout"]),
                "satoshis": int(u["amount"] * 100_000_000),
                "scriptPubKey": u.get("scriptPubKey", "")
            } for u in inputs_to_use
        ]
        block_height = await self.app.api.get_block_height()
        cmd = [
            mktx,
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
                self.app.main_window.error_dialog(
                    "Error", f"Failed to build transaction: {stderr.decode()}"
                )
                self.enable_send()
                return
            raw_tx_hex = stdout.decode().strip()
            success, error = await self.app.api.broadcast_tx(raw_tx_hex)
            if success:
                self.app.main_window.info_dialog(
                    "Success", "Transaction broadcast successfully"
                )
                self.destination_input.value = ""
                self.amount_input.value = ""
                self.fee_input.value = "0.00001000"
                await self.fetch_transactions()
            else:
                self.app.main_window.error_dialog(
                    "Broadcast failed", error or "Unknown error"
                )
            self.enable_send()
        except Exception as e:
            self.app.main_window.error_dialog(
                "Error", f"Transaction build error: {e}"
            )
            self.enable_send()
