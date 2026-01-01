
import asyncio
import subprocess
import json
from toga import App, Box, Label, Button, Divider, Command, Group
from toga.style.pack import Pack
from toga.constants import COLUMN, ROW, CENTER, Direction, BOLD, NORMAL
from toga.platform import current_platform

from .coin import Coin


class Wallet(Box):
    def __init__(self, app:App):
        super().__init__(
            style=Pack(
                direction=COLUMN,
                flex=1,
                align_items=CENTER
            )
        )

        self.app = app
        self._is_generating = None
        self.coin_view = None

        self.account_panel = Box(
            style=Pack(
                direction=ROW,
                height=70,
                align_items=CENTER
            )
        )

        self.add_button = Button(
            text="+ Add Coin",
            style=Pack(
                font_size=11,
                width=150,
                margin_bottom=15
            ),
            on_press=self.show_add_coins
        )

        self.cancel_button = Button(
            text="<<<",
            style=Pack(
                font_size=11,
                width=150,
                margin_bottom=20
            ),
            on_press=self.cancel_add_coins
        )

        self.accoun_label = Label(
            text=f"Account : {self.app.account}",
            style=Pack(
                font_size=14,
                text_align=CENTER,
                flex=1,
                font_weight=BOLD,
                margin_top=20
            )
        )

        self.h_divider = Divider(
            direction=Direction.HORIZONTAL,
            style=Pack(
                flex=1,
                margin_left=15,
                margin_right=15
            )
        )

        self.wallet_container = Box(
            style=Pack(
                direction=ROW,
                flex=1,
                align_items=CENTER
            )
        )

        v_divider = Divider(
            direction=Direction.VERTICAL,
            style=Pack(
                flex=1,
                margin_top=15,
                margin_bottom=15
            )
        )

        self.coins_label = Label(
            text="Coins List",
            style=Pack(
                font_size=11,
                text_align=CENTER,
                flex=1,
                font_weight=BOLD,
                margin_top=20,
                margin_bottom=20
            )
        )

        self.coins_list = Box(
            style=Pack(
                direction=COLUMN,
                flex=1,
                align_items=CENTER,
                gap=5
            )
        )

        self.add_coins_list = Box(
            style=Pack(
                direction=COLUMN,
                flex=1,
                align_items=CENTER,
                gap=5
            )
        )

        self.coins_panel = Box(
            style=Pack(
                direction=COLUMN,
                width=200,
                align_items=CENTER
            )
        )

        self.coin_manage = Box(
            style=Pack(
                direction=COLUMN,
                flex=1,
                align_items=CENTER
            )
        )
        if current_platform == "linux":
            self.toolbar_box = Box(
                style=Pack(
                    direction = ROW,
                    height = 24
                )
            )
            self.add(self.toolbar_box)

        self.add(
            self.account_panel,
            self.h_divider,
            self.wallet_container
        )
        self.account_panel.add(
            self.accoun_label
        )
        self.wallet_container.add(
            self.coins_panel,
            v_divider,
            self.coin_manage
        )
        self.coins_panel.add(
            self.coins_label,
            self.coins_list,
            self.add_button
        )

        self.insert_toolbar()

    def insert_toolbar(self):
        if current_platform == "linux":
            from gi.repository import Gtk
            toolbar = Gtk.MenuBar()
            self.toolbar_box._impl.native.add(toolbar)

            help_group = Gtk.MenuItem()
            help_group.set_label("Help")

            submenu = Gtk.Menu()

            about_cmd = Gtk.MenuItem()
            about_cmd.set_label("About")
            about_cmd.connect("activate", self.show_about)
            github_cmd = Gtk.MenuItem()
            github_cmd.set_label("Github")
            github_cmd.connect("activate", self.visit_page)
            donate_cmd = Gtk.MenuItem()
            donate_cmd.set_label("Donate")
            donate_cmd.connect("activate", self.donate)

            submenu.append(about_cmd)
            submenu.append(github_cmd)
            submenu.append(donate_cmd)
            submenu.show_all()

            help_group.set_submenu(submenu)
            toolbar.append(help_group)
            toolbar.show_all()
        else:
            about_cmd = Command(
                group=Group.HELP,
                text="About",
                action=self.show_about
            )
            visit_cmd = Command(
                group=Group.HELP,
                text="Github",
                action=self.visit_page
            )
            donate_cmd = Command(
                group=Group.HELP,
                text="Donate",
                action=self.donate
            )
            self.app.commands.add(
                donate_cmd,
                visit_cmd,
                about_cmd
            )
        self.show_coins_list()


    def show_coins_list(self):
        wallet = self.app.vault.list_coins(self.app.account, self.app.password)
        for coin in wallet:
            coin_button = Button(
                text=coin,
                style=Pack(
                    font_size=12,
                    width=100
                ),
                on_press=lambda widget, coin=coin: self.manage_coin(coin, widget)
            )
            self.coins_list.add(coin_button)

        
    def show_add_coins(self, button):
        self.add_coins_list.clear()
        self.coins_panel.remove(
            self.coins_list,
            self.add_button
        )
        self.coins_panel.add(
            self.add_coins_list,
            self.cancel_button
        )
        self.coins_label.text = "+ Add Coin"
        wallet = self.app.vault.list_coins(self.app.account, self.app.password)
        coins = self.app.utils.get_available_coins()
        for coin in coins:
            if coin not in wallet:
                coin_button = Button(
                    text=coin,
                    style=Pack(
                        font_size=12,
                        font_weight=BOLD,
                        width=100
                    ),
                    on_press=lambda widget, coin=coin: self.confirm_add_coin(coin)
                )
                self.add_coins_list.add(coin_button)


    def cancel_add_coins(self, button):
        self.restore_coins_list()


    def restore_coins_list(self):
        self.coins_label.text = "Coins List"
        self.coins_panel.remove(
            self.add_coins_list,
            self.cancel_button
        )
        self.coins_panel.add(
            self.coins_list,
            self.add_button
        )


    def insert_coin(self, coin, address, wif):
        self.app.vault.add_coin(self.app.account, self.app.password, coin, address, wif)
        coin_button = Button(
            text=coin,
            style=Pack(
                font_size=12,
                width=100
            ),
            on_press=lambda widget, coin=coin: self.manage_coin(coin, widget)
        )
        self.coins_list.add(coin_button)
        self.restore_coins_list()
        self._is_generating = None


    def confirm_add_coin(self, coin):
        if self._is_generating:
            return
        self._is_generating = True
        if current_platform == "darwin":
            hdwallet = self.generate_address(coin)
        else:
            hdwallet = self.app.utils.generate_address(coin)
        if not hdwallet:
            self.app.main_window.error_dialog(
                "Error", "Failed to generate address"
            )
            return
        address = hdwallet["address"]
        wif = hdwallet["wif"]
        self.insert_coin(coin, address, wif)


    async def generate_address(self, coin):
        coin_info = self.app.utils.get_coin(coin)
        network = coin_info["network"]
        wallet_cli = str(self.app.utils.get_tool())
        cmd = [wallet_cli, "--network", network, "--gen-address"]
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=0
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                self.app.main_window.error_dialog(
                    "Error", f"Failed to generate address: {stderr.decode()}"
                )
                return None
            raw = stdout.decode().strip()
            try:
                data = json.loads(raw)
                return {
                    "address": data["address"],
                    "wif": data["wif"]
                }
            except json.JSONDecodeError as e:
                self.app.main_window.error_dialog(
                    "Error",
                    f"Invalid JSON from address generator:\n{raw}"
                )
                return None
        except Exception as e:
            self.app.main_window.error_dialog(
                "Error", f"Failed to generate address: {e}"
            )
            return None


    def manage_coin(self, coin, button):
        if self.app.coin == coin:
            return
        if self.coin_view:
            self.coin_view.toggle = None
        self.app.loop.create_task(self.update_buttons(button))
        self.app.coin = coin
        address = self.app.vault.get_coin_address(self.app.account, self.app.password, coin)
        if address:
            self.coin_manage.clear()
            self.coin_view = Coin(self.app, address)
            self.coin_manage.add(self.coin_view)
            

    async def update_buttons(self, button):
        for widget in self.coins_list.children:
            widget.style.width = 100
            widget.style.font_weight = NORMAL
        button.style.width = 120
        button.style.font_weight = BOLD


    def show_about(self, cmd):
        self.app.about()

    def visit_page(self, cmd):
        import webbrowser
        webbrowser.open(self.app.home_page)

    def donate(self, cmd):
        if not self.app.coin:
            return
        donation = self.app.utils.get_donation_address(self.app.coin)
        if donation:
            if self.coin_view:
                self.coin_view.coin_container.current_tab = self.coin_view.send_option
                self.coin_view.destination_input.value = donation
                self.coin_view.amount_input.focus()