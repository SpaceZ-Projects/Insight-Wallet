
from toga import App, Window
from toga.platform import current_platform

from . import Utils, Setup, InsightAPI, Vault


class InsightWallet(App):
    
    def set_window_params(self):
        platform = current_platform
        if platform == "windows":
            import System.Drawing as Drawing
            self.main_window._impl.native.Size = Drawing.Size(900,550)
            self.main_window._impl.native.MinimumSize = Drawing.Size(900,550)
            self.main_window._impl.native.Resize += self._on_window_resize
            self.utils.apply_title_bar_mode(self.main_window)
        elif platform == "linux":
            self.main_window.size = (1050,600)
            self.main_window._impl.native.set_size_request(1050,600)
        elif platform == "darwin":
            self.main_window.size = (900,550)

        size = self.main_window.size
        x, y = self.utils.windows_screen_center(size)
        self.main_window.position = (x,y)

    def _on_window_resize(self, event, sender):
        import System.Drawing as Drawing
        self.main_window._impl.native.MinimumSize = Drawing.Size(900,550)

    def startup(self):
        self.coin = None
        self.account = None
        self.password = None
        self.utils = Utils(self)
        self.vault = Vault(self)
        self.api = InsightAPI(self)
        self.setup = Setup(self)
        self.main_window = Window(
            title=f"{self.formal_name} v{self.version}"
        )
        self.set_window_params()
        self.main_window.content = self.setup
        self.main_window.show()

    async def on_exit(self):
        self.coin = None
        self.account = None
        self.password = None
        return super().on_exit()


def main():
    app = InsightWallet(
        formal_name="InsightWallet",
        app_id="com.btcz.insightwallet",
        version="1.0.0",
        icon="resources/insightwallet"
    )
    app.main_loop()

if __name__ == "__main__":
    main()
