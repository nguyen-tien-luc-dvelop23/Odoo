# -*- coding: utf-8 -*-
from odoo import models, api, _

class CongViecInherit(models.Model):
    _inherit = 'cong_viec'

    @api.model
    def create(self, vals):
        res = super(CongViecInherit, self).create(vals)
        # Sửa từ nhan_vien_id thành nguoi_thuc_hien_id
        if res.nguoi_thuc_hien_id and res.nguoi_thuc_hien_id.telegram_chat_id:
            msg = f"🔔 <b>Công việc mới:</b> {res.ten_cong_viec}\n👤 <b>Dự án:</b> {res.du_an_id.ten_du_an}\n📅 <b>Hạn:</b> {res.deadline or 'N/A'}"
            self.env['nhan_su_ai.telegram.service'].send_message(res.nguoi_thuc_hien_id.telegram_chat_id, msg)
        return res

    def write(self, vals):
        res = super(CongViecInherit, self).write(vals)
        # Sửa từ nhan_vien_id thành nguoi_thuc_hien_id
        if 'nguoi_thuc_hien_id' in vals and self.nguoi_thuc_hien_id and self.nguoi_thuc_hien_id.telegram_chat_id:
            msg = f"🔄 <b>Điều chuyển công việc:</b> {self.ten_cong_viec}\n👤 bạn đã được giao phụ trách công việc này."
            self.env['nhan_su_ai.telegram.service'].send_message(self.nguoi_thuc_hien_id.telegram_chat_id, msg)
        return res


class DuAnInherit(models.Model):
    _inherit = 'du_an'

    def write(self, vals):
        old_status = {self.id: self.trang_thai for p in self}
        res = super(DuAnInherit, self).write(vals)
        if 'trang_thai' in vals:
            for p in self:
                msg = f"🚀 <b>Cập nhật Dự án:</b> {p.ten_du_an}\n📈 <b>Trạng thái mới:</b> {dict(self._fields['trang_thai'].selection).get(p.trang_thai)}"
                # Gửi cho Quản lý dự án
                if p.nguoi_quan_ly_id.telegram_chat_id:
                    self.env['nhan_su_ai.telegram.service'].send_message(p.nguoi_quan_ly_id.telegram_chat_id, msg)
        return res
