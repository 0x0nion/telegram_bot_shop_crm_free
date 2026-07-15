import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class Locale:
    locale_path = Path(__file__).resolve().parent / "msg.json"

    def __init__(self, lang: str = "en"):
        self.lang = lang
        self.locales = self._load_json()

    def _load_json(self):
        try:
            with open(self.locale_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                return data.get(self.lang)
        except Exception as e:
            logger.critical(f"Can't open {self.locale_path}: {e}", exc_info=True)
            return None

    def get_text(self, key: str) -> str:
        if self.locales is None:
            logger.critical(f"[LOCALES] Unable '{self.lang}' in msg.json!")
            return "XXX"

        text = self.locales.get(key)
        if text is None:
            logger.critical(f"[LOCALES] Unable '{key}' for lang '{self.lang}'!")
            return "XXX"

        return text

    def format_order(self, order, template_key: str = "user_checkout_confirm") -> str:
        """
        Форматирует весь чек заказа.
        template_key позволяет выбрать текст: успешное оформление или просто просмотр.
        """

        item_lines = []
        for item in order.items:
            product_name = item.product.name if item.product else "Deleted Product"
            item_total = item.quantity * float(item.price_at_purchase)
            item_lines.append(
                f"• {product_name} — {item.quantity} x {float(item.price_at_purchase):.2f} $ = {item_total:.2f} $"
            )
        items_block = "\n".join(item_lines)

        address_block = f"{order.delivery_address}\n\n" if order.delivery_address else ""

        comment_block = f"📝 <b>Комментарий:</b> {order.user_comment}\n\n" if order.user_comment else ""

        template = self.get_text(template_key)

        return template.format(
            id=order.id,
            items=items_block,
            address_block=address_block,
            comment_block=comment_block,
            total_price=float(order.total_price)
        )

    def format_address(self, maps_url: str) -> str:
        """
        Форматирует ссылку на карты в красивый HTML-вид.
        """
        template = self.get_text("user_address_link")
        return template.format(maps_url=maps_url)


