
from toga import App, Box, Label, Button, Divider
from toga.style.pack import Pack
from toga.constants import COLUMN, ROW, CENTER, Direction, BOLD, NORMAL

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
                width=850
            )
        )

        self.wallet_container = Box(
            style=Pack(
                direction=ROW,
                flex=1,
                align_items=CENTER
            )
        )

        self.v_divider = Divider(
            direction=Direction.VERTICAL,
            style=Pack(
                height=400
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
            self.v_divider,
            self.coin_manage
        )
        self.coins_panel.add(
            self.coins_label,
            self.coins_list,
            self.add_button
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


    def confirm_add_coin(self, coin):
        if self._is_generating:
            return
        self._is_generating = True
        hdwallet = self.app.utils.generate_address(coin)
        if hdwallet:
            address = hdwallet.address()
            wif = hdwallet.wif()
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


    def manage_coin(self, coin, button):
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