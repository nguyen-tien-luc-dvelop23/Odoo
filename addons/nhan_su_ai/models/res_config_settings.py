# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    gemini_api_key = fields.Char(
        string="API Key",
        config_parameter='nhan_su_ai.gemini_api_key',
        help="Nhập API Key vào đây"
    )
    telegram_bot_token = fields.Char(string="Bot Token", config_parameter='nhan_su_ai.telegram_bot_token')
