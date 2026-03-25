# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class NhanSuAIChat(models.Model):
    _name = 'nhan_su_ai.chat'
    _description = 'Trò chuyện với AI'
    _order = 'create_date desc'

    name = fields.Char(string="Câu hỏi", required=True)
    response = fields.Text(string="Phản hồi từ AI", readonly=True)
    user_id = fields.Many2one('res.users', string="Người hỏi", default=lambda self: self.env.user, readonly=True)

    def action_chat(self):
        self.ensure_one()
        # Sử dụng helper từ model nhan_vien (vì logic gọi API nằm ở đó)
        # Hoặc đưa logic gọi API vào một mixin/tập trung hơn.
        # Ở đây mình sẽ mượn logic gọi API đã viết.
        
        # Tạo instance giả để gọi helper (hoặc chuyển helper thành static/class method)
        # Để đơn giản, mình sẽ copy lại logic gọi API vào đây hoặc gọi qua env.
        
        # Lấy logic từ model nhan_vien
        nhan_vien_model = self.env['nhan_vien']
        # Vì _call_gemini_api là method của nhan_vien, ta cần một record nhan_vien để gọi.
        # Giải pháp tốt hơn: chuyển _call_gemini_api sang một model service riêng hoặc mixin.
        
        # Tạm thời copy logic gọi API vào đây để xử lý Chat tổng quát
        prompt = self.name
        answer = self.env['nhan_vien']._call_gemini_api(prompt)
        self.write({'response': answer})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'nhan_su_ai.chat',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
