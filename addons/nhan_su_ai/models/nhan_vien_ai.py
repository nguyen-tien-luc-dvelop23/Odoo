# -*- coding: utf-8 -*-
import requests
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class NhanVienAI(models.Model):
    _inherit = 'nhan_vien'

    ai_summary = fields.Text(string="Tóm tắt AI (Hiệu suất & Kỹ năng)", readonly=True)
    telegram_chat_id = fields.Char(string="Telegram Chat ID", help="ID chat với Bot Telegram để nhận thông báo.")

    def action_test_telegram(self):
        self.ensure_one()
        if not self.telegram_chat_id:
            raise UserError(_("Vui lòng điền Telegram Chat ID trước!"))
        
        msg = f"🚀 <b>Kiểm tra kết nối:</b> Chào {self.ho_ten}, Telegram của bạn đã được kết nối thành công với Odoo!"
        success = self.env['nhan_su_ai.telegram.service'].send_message(self.telegram_chat_id, msg)
        
        if success:
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'Tin nhắn thử nghiệm đã được gửi!',
                    'type': 'rainbow_man',
                }
            }
        else:
            raise UserError(_("Không thể gửi tin nhắn. Kiểm tra lại Bot Token trong Cấu hình AI."))


    @api.model
    def _call_gemini_api(self, prompt):
        """Helper để gọi Gemini với logic fallback model"""
        api_key = self.env['ir.config_parameter'].sudo().get_param('nhan_su_ai.gemini_api_key')
        if not api_key:
            raise UserError(_("Vui lòng cấu hình Gemini API Key."))

        # Danh sách các model và endpoint thử nghiệm dựa trên kết quả lits-models
        test_configs = [
            ("v1beta", "gemini-2.0-flash"),
            ("v1beta", "gemini-1.5-flash"),
            ("v1beta", "gemini-flash-latest"),
            ("v1", "gemini-1.5-flash"),
            ("v1beta", "gemini-pro"),
        ]


        last_error = ""
        for version, model in test_configs:
            url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={api_key}"
            headers = {'Content-Type': 'application/json'}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            
            try:
                _logger.info("Thử gọi Gemini: model=%s, version=%s", model, version)
                response = requests.post(url, headers=headers, json=payload, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    if 'candidates' in data and data['candidates']:
                        return data['candidates'][0]['content']['parts'][0]['text']
                last_error = f"{response.status_code}: {response.text}"
            except Exception as e:
                last_error = str(e)
                continue
        
        raise UserError(_("Không thể kết nối với Gemini AI sau nhiều lần thử. Lỗi cuối: %s") % last_error)

    def action_generate_ai_summary(self):
        """Gọi Gemini AI để tóm tắt hồ sơ nhân viên"""
        self.ensure_one()
        
        # Lấy dữ liệu
        histories = self.env['lich_su_lam_viec'].search([('nhan_vien_id', '=', self.id)])
        history_text = "\n".join([f"- {h.ngay_bat_dau}: {h.ten_cong_viec}" for h in histories])
        projects = self.du_an_ids
        project_text = "\n".join([f"- {p.ten_du_an}: {p.trang_thai}" for p in projects])

        prompt = f"Tóm tắt hồ sơ nhân sự (150 chữ): Tên {self.ho_ten}, CV {self.chuc_vu_id.ten_chuc_vu}, PB {self.phong_ban_id.ten_phong_ban}. Lịch sử: {history_text}. Dự án: {project_text}."
        
        result = self._call_gemini_api(prompt)
        self.write({'ai_summary': result})
        return True

    ai_chat_input = fields.Char(string="Câu hỏi của bạn")
    ai_chat_output = fields.Text(string="Trả lời từ AI", readonly=True)

    def action_ai_chat(self):
        self.ensure_one()
        if not self.ai_chat_input:
            return
        
        # Thêm ngữ cảnh nhân viên vào chat
        context_prompt = f"Dựa trên nhân viên {self.ho_ten} ({self.chuc_vu_id.ten_chuc_vu}), hãy trả lời: {self.ai_chat_input}"
        answer = self._call_gemini_api(context_prompt)
        
        self.write({
            'ai_chat_output': (self.ai_chat_output or '') + f"\nBạn: {self.ai_chat_input}\nAI: {answer}\n" + "-"*30,
            'ai_chat_input': ''
        })


