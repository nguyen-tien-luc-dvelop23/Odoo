# -*- coding: utf-8 -*-
import requests
import logging
from odoo import models, api, _

_logger = logging.getLogger(__name__)

class TelegramService(models.AbstractModel):
    _name = 'nhan_su_ai.telegram.service'
    _description = 'Dịch vụ Telegram'

    @api.model
    def send_message(self, chat_id, message):
        if not chat_id or not message:
            return False
            
        token = self.env['ir.config_parameter'].sudo().get_param('nhan_su_ai.telegram_bot_token')
        if not token:
            _logger.warning("Chưa cấu hình Telegram Bot Token!")
            return False

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            _logger.error("Lỗi gửi Telegram: %s", str(e))
            return False
