import json
import logging
from pathlib import Path
from typing import Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = logging.getLogger(__name__)


class AdminInlineKb:
    locale_path = Path(__file__).resolve().parent / "admin_kb.json"

    def __init__(self, lang: str = 'ru'):
        self.lang = lang
        self.template = self._load_json()

    def _load_json(self):
        try:
            with open(self.locale_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            logger.critical(f"[ADMIN KB] Failed to open/parse {self.locale_path}: {e}", exc_info=True)
            return None

    def get_kb(self, key: str) -> Optional[InlineKeyboardMarkup]:
        """Универсальный метод генерации клавиатур из admin_kb.json"""
        if self.template is None:
            logger.critical("[ADMIN KB] Keyboards template is missing!")
            return None

        data = self.template.get(key)
        if data is None:
            logger.critical(f"[ADMIN KB] Keyboard with key '{key}' not found!")
            return None

        buttons = data.get("buttons")
        sizes = data.get("sizes")

        if not buttons or not sizes:
            logger.critical(f"[ADMIN KB] Invalid structure for key '{key}'!")
            return None

        builder = InlineKeyboardBuilder()

        for callback_data, translations in buttons.items():
            button_text = translations.get(self.lang) or translations.get("en") or "XXX"

            if not translations.get(self.lang):
                logger.warning(f"[ADMIN KB] Missing translation for lang '{self.lang}' in button '{callback_data}'")

            builder.button(text=button_text, callback_data=callback_data)

        builder.adjust(*sizes)
        return builder.as_markup()

    def get_text(self, path: str, default: str = "") -> str:
        """Вспомогательный метод для получения локализованных строк/сообщений"""
        if self.template is None:
            return default

        keys = path.split(".")
        current = self.template.get("admin_messages", {})

        for key in keys:
            if isinstance(current, dict):
                current = current.get(key, {})
            else:
                return default

        if isinstance(current, dict):
            return current.get(self.lang) or current.get("en") or default
        return default

    def get_cancel_add_category_kb(self, back_callback: str) -> Optional[InlineKeyboardMarkup]:
        """Клавиатура отмены с динамическим callback_data для возврата назад"""
        if self.template is None:
            return None

        cfg = self.template.get("admin_category_actions")
        if not cfg:
            logger.critical("[ADMIN KB] 'admin_category_actions' configuration not found!")
            return None

        buttons_cfg = cfg.get("buttons", {})
        cancel_text = buttons_cfg.get("cancel", {}).get(self.lang) or "📥 Cancel"

        builder = InlineKeyboardBuilder()
        builder.button(text=cancel_text, callback_data=back_callback, style='danger')
        return builder.as_markup()

    def get_shop_edit_kb(
            self,
            categories: list,
            products: list,
            current_cat_id: int | None,
            parent_id: int | None
    ) -> Optional[InlineKeyboardMarkup]:
        """Динамический конструктор управления категориями и товарами магазина"""
        if self.template is None:
            return None

        nav_data = self.template.get("admin_shop_navigation")
        if not nav_data:
            logger.critical("[ADMIN KB] 'admin_shop_navigation' configuration not found!")
            return None

        nav_buttons = nav_data.get("buttons", {})

        # Локализуем статические кнопки
        back_text = nav_buttons.get("back", {}).get(self.lang) or "⬅️ Back"
        to_main_text = nav_buttons.get("to_main_menu", {}).get(self.lang) or "⬅️ To Main Menu"
        del_text = nav_buttons.get("delete", {}).get(self.lang) or "❌ Delete"
        add_sub_text = nav_buttons.get("add_subcategory", {}).get(self.lang) or "🟢 Add Subcategory"
        add_prod_text = nav_buttons.get("add_product", {}).get(self.lang) or "🔴 Add Product Here"
        add_tittle_text = nav_buttons.get("add_tittle", {}).get(self.lang) or "📝 Category details"
        save_text = nav_buttons.get("save_changes", {}).get(self.lang) or "💾 Save Changes"

        builder = InlineKeyboardBuilder()

        # 1. Навигация "Назад" / "В главное меню"
        if current_cat_id:
            parent_to_go = parent_id if parent_id else "root"
            builder.row(InlineKeyboardButton(text=back_text, callback_data=f"admin_shop_{parent_to_go}"))
        else:
            builder.row(InlineKeyboardButton(text=to_main_text, callback_data="admin_mainmenu"))

        # 2. Список подкатегорий (Имя категории + кнопка «Удалить»)
        for category in categories:
            builder.row(
                InlineKeyboardButton(text=f"📁 {category.name}", callback_data=f"admin_shop_{category.id}"),
                InlineKeyboardButton(text=del_text, callback_data=f"admin_del_cat_{category.id}")
            )

        # 3. Список товаров (Имя товара + кнопка «Удалить»)
        for product in products:
            builder.row(
                InlineKeyboardButton(text=f"📦 {product.name}", callback_data=f"admin_item_{product.id}"),
                InlineKeyboardButton(text=del_text, callback_data=f"admin_del_item_{product.id}")
            )

        # 4. Управление и добавление ресурсов
        cat_suffix = f"_{current_cat_id}" if current_cat_id else "_root"
        builder.row(InlineKeyboardButton(text=add_sub_text, callback_data=f"admin_addcat{cat_suffix}"))
        builder.row(InlineKeyboardButton(text=add_prod_text, callback_data=f"admin_add_item{cat_suffix}"))
        builder.row(InlineKeyboardButton(text=add_tittle_text, callback_data=f"admin_add_tittle{cat_suffix}"))
        builder.row(InlineKeyboardButton(text=save_text, callback_data="admin_save_shop"))

        return builder.as_markup()

    def get_product_editor_kb(self, product_id: int, category_id: int | str) -> Optional[InlineKeyboardMarkup]:
        """Клавиатура управления характеристиками конкретного товара"""
        if self.template is None:
            return None

        cfg = self.template.get("admin_product_editor")
        if not cfg:
            logger.critical("[ADMIN KB] 'admin_product_editor' configuration not found!")
            return None

        buttons_cfg = cfg.get("buttons", {})

        edit_name = buttons_cfg.get("edit_name", {}).get(self.lang) or "✏️ Name"
        edit_unit = buttons_cfg.get("edit_unit", {}).get(self.lang) or "⚖️ Unit"
        edit_desc = buttons_cfg.get("edit_desc", {}).get(self.lang) or "✏️ Description"
        edit_price = buttons_cfg.get("edit_price", {}).get(self.lang) or "💰 Price"
        edit_photo = buttons_cfg.get("edit_photo", {}).get(self.lang) or "📸 Photo"
        back_text = buttons_cfg.get("back", {}).get(self.lang) or "⬅️ Back"

        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text=edit_name, callback_data=f"admin_edit_p_name_{product_id}"),
            InlineKeyboardButton(text=edit_unit, callback_data=f"admin_edit_p_unit_{product_id}")
        )
        builder.row(
            InlineKeyboardButton(text=edit_desc, callback_data=f"admin_edit_p_desc_{product_id}"),
            InlineKeyboardButton(text=edit_price, callback_data=f"admin_edit_p_price_{product_id}")
        )
        builder.row(InlineKeyboardButton(text=edit_photo, callback_data=f"admin_edit_p_photo_{product_id}"))
        builder.row(InlineKeyboardButton(text=back_text, callback_data=f"admin_shop_{category_id}"))

        return builder.as_markup()