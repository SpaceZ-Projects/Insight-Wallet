
from toga import App, Box, Button, PasswordInput, Label, TextInput, Divider, ProgressBar
from toga.style.pack import Pack
from toga.constants import COLUMN, ROW, CENTER, BOLD
from toga.colors import RED

from .wallet import Wallet


class Setup(Box):
    def __init__(self, app:App):
        super().__init__(
            style=Pack(
                direction=ROW,
                justify_content=CENTER,
                align_items=CENTER,
                flex=1
            )
        )

        self.app = app

        self.download_label = Label(
            text="Downloading tool...",
            style=Pack(
                text_align=CENTER,
                font_size=12
            )
        )

        self.download_progress = ProgressBar(
            max = 100,
            style=Pack(
                width=200
            )
        )

        self.download_panel = Box(
            style=Pack(
                direction=COLUMN,
                align_items=CENTER,
                flex=1,
                gap=10
            )
        )

        self.create_label = Label(
            text="No wallet is available for this device. Click the button to",
            style=Pack(
                font_size=12
            )
        )

        self.create_button = Button(
            text="Create Wallet",
            style=Pack(
                font_size=12
            ),
            on_press=self.show_create_panel
        )

        self.confirm_button = Button(
            text="Confirm",
            style=Pack(
                font_size=12,
                margin_left=10
            ),
            on_press=self.verify_account
        )

        self.cancel_button = Button(
            text="<<<",
            style=Pack(
                font_size=12,
                margin_right=10
            )
        )

        self.accounts_label = Label(
            text="Accounts",
            style=Pack(
                text_align=CENTER,
                font_size=12,
                font_weight=BOLD
            )
        )
        self.accounts_panel = Box(
            style=Pack(
                direction=COLUMN,
                align_items=CENTER,
                flex=1,
                gap=10
            )
        )

        self.password_rules = Label(
            text=f"- Length: Minimum 8 characters.\n"
                f"- Uppercase Letters: At least 1 (A-Z).\n"
                f"- Lowercase Letters: At least 1 (a-z).\n"
                f"- Numbers: At least 1 (0-9).\n"
                f"- Special Characters: At least 1 (e.g., ! @ # $ % ^ & *).\n"
                f"- No Spaces: Password cannot contain spaces.",
            style=Pack(
                color=RED,
                text_align=CENTER
            )
        )
        self.account_name = TextInput(
            placeholder="account name",
            style=Pack(
                width=250,
                font_size=11,
                text_align=CENTER
            )
        )
        self.account_password = PasswordInput(
            placeholder="password",
            style=Pack(
                width=250,
                font_size=11,
                text_align=CENTER
            )
        )
        self.create_confirm_button = Button(
            text="Confirm",
            style=Pack(
                font_size=12,
                flex=1
            ),
            on_press=self.verify_create_inputs
        )
        self.create_buttons_panel = Box(
            style=Pack(
                direction=ROW,
                width=250,
                margin_top=10
            )
        )
        self.create_panel = Box(
            style=Pack(
                direction=COLUMN,
                align_items=CENTER,
                flex=1,
                gap=10
            )
        )

        self.accounts_divider = Divider(
            style=Pack(
                width=250,
                margin_top=10
            )
        )
        self.verify_tool()


    def verify_tool(self):
        mktx = self.app.utils.get_tool()
        if mktx.exists():
            sha256 = self.app.utils.sha256_file(mktx)
            if not sha256:
                mktx.unlink()
        if not mktx.exists():
            self.add(self.download_panel)
            self.download_panel.add(
                self.download_label,
                self.download_progress
            )
            self.app.loop.create_task(
                self.app.utils.fetch_tool(self, self.download_label, self.download_progress)
            )
        else:
            self.verify_vault()


    def verify_vault(self):
        accounts = self.app.vault.list_accounts()
        if not accounts:
            self.show_new_setup()
            return
        self.show_accounts(accounts)


    def show_accounts(self, accounts):
        self.clear()
        self.accounts_panel.clear()
        self.accounts_panel.add(self.accounts_label)
        for account in accounts[:5]:
            button = Button(
                text=f"🏛️ {account}",
                style=Pack(
                    font_size=12,
                    width=200
                ),
                on_press=lambda widget, account=account: self.show_password_panel(account)
            )
            self.accounts_panel.add(button)
        self.create_button.style = Pack(font_size=12, width=200, margin_top=10)
        self.accounts_panel.add(
            self.accounts_divider,
            self.create_button
        )
        self.add(self.accounts_panel)
        self.cancel_button.on_press = self.cancel_account_access


    def show_new_setup(self):
        self.clear()
        self.add(
            self.create_label,
            self.create_button
        )
        self.cancel_button.on_press = self.cancel_create_account

    def show_create_panel(self, button):
        total_accounts = len(self.app.vault.list_accounts())
        if total_accounts >= 5:
            self.app.main_window.error_dialog(
                "Limit reached",
                "You cannot create more than 5 accounts."
            )
            return
        self.clear()
        self.create_panel.clear()
        self.create_buttons_panel.clear()
        self.account_name.value = ""
        self.account_password.value = ""
        self.create_panel.add(
            self.account_name,
            self.account_password,
            self.create_buttons_panel
        )
        self.create_buttons_panel.add(
            self.cancel_button,
            self.create_confirm_button
        )
        self.add(
            self.create_panel
        )
        self.account_password.on_confirm = None
        self.account_password.on_change = self.on_password_change


    def show_password_panel(self, account: str):
        self.clear()
        self.add(
            self.cancel_button,
            self.account_password,
            self.confirm_button
        )
        self.account_password.on_change = None
        self.account_password.value = ""
        self.account_password.on_confirm = lambda widget, account=account: self.verify_account(account)
        self.confirm_button.on_press = lambda widget, account=account: self.verify_account(account)


    def cancel_account_access(self, button):
        accounts = self.app.vault.list_accounts()
        self.show_accounts(accounts)


    def cancel_create_account(self, button):
        self.show_new_setup()
        
        
    def on_password_change(self, input):
        self.create_panel.remove(self.password_rules)


    def verify_create_inputs(self, button):
        def on_result(dialog, result):
            self.app.account = name
            self.app.password = password
            self.app.main_window.content = Wallet(self.app)
        name = self.account_name.value.strip()
        password = self.account_password.value.strip()
        if not name:
            self.app.main_window.error_dialog("Error", "Account name is required")
            self.account_name.focus()
            return
        if len(name) < 6:
            self.app.main_window.error_dialog("Error", "Account name must be at least 6 characters long")
            self.account_name.focus()
            return
        if not password:
            self.app.main_window.error_dialog("Error", "Account password is required")
            self.account_password.focus()
            return
        error = self.app.utils.is_strong_password(password)
        if error:
            self.app.main_window.error_dialog("Weak password", error)
            self.account_password.focus()
            self.create_panel.insert(1, self.password_rules)
            return
        if self.app.vault.vault_exists(name):
            self.app.main_window.error_dialog("Error", f"Account '{name}' already exists")
            self.account_name.focus()
            return
        try:
            created = self.app.vault.create_vault(name, password)
            if not created:
                raise RuntimeError("Vault creation failed")
        except Exception as e:
            self.app.main_window.error_dialog("Error", f"Failed to create wallet:\n{e}")
            return
        self.app.main_window.info_dialog("Success", f"Wallet for account '{name}' has been created !",
            on_result=on_result
        )


    def verify_account(self, account: str):
        password = self.account_password.value.strip()
        if not password:
            self.account_password.focus()
            return
        self.cancel_button.enabled = False
        self.confirm_button.enabled = False
        self.account_password.readonly = True

        try:
            conn, _ = self.app.vault.open_vault(account, password)
            conn.close()
        except Exception:
            self.app.main_window.error_dialog(
                "Error", "Invalid password"
            )
            self.cancel_button.enabled = True
            self.confirm_button.enabled = True
            self.account_password.readonly = False
            return
        self.app.account = account
        self.app.password = password
        self.app.main_window.content = Wallet(self.app)


