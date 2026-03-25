# -*- coding: utf-8 -*-
from odoo import models, fields, api

class NhanVienInherit(models.Model):
    _inherit = 'nhan_vien'

    # ✅ FIX: Dùng Many2many với relation table rõ ràng để tránh conflict với thanh_vien_ids trong du_an
    du_an_ids = fields.Many2many(
        'du_an',
        'du_an_nhan_vien_rel',   # Tên bảng quan hệ phải khớp với bên du_an
        'nhan_vien_id',
        'du_an_id',
        string="Dự án tham gia",
        readonly=True,
    )

    # ✅ LOGIC ĐÚNG: One2many từ cong_viec -> nguoi_thuc_hien_id
    cong_viec_ids = fields.One2many(
        'cong_viec',
        'nguoi_thuc_hien_id',
        string="Công việc được giao"
    )

    # ✅ KPI: Chỉ số hiệu suất tự động
    diem_hieu_suat = fields.Float(
        string="Chỉ số hiệu suất (%)",
        compute="_compute_hieu_suat",
        store=True,
        help="Tỉ lệ % công việc hoàn thành đúng hạn hoặc xuất sắc trên tổng công việc đã xong"
    )

    so_du_an = fields.Integer(
        string="Số dự án tham gia",
        compute="_compute_thong_ke",
        store=True
    )

    so_cong_viec_hoan_thanh = fields.Integer(
        string="Việc hoàn thành",
        compute="_compute_thong_ke",
        store=True
    )

    so_cong_viec_tre_han = fields.Integer(
        string="Việc trễ hạn",
        compute="_compute_thong_ke",
        store=True
    )

    @api.depends('cong_viec_ids.trang_thai', 'cong_viec_ids.danh_gia_hieu_qua')
    def _compute_hieu_suat(self):
        for rec in self:
            done = rec.cong_viec_ids.filtered(lambda t: t.trang_thai == 'hoan_thanh')
            total = len(done)
            if total > 0:
                good = len(done.filtered(lambda t: t.danh_gia_hieu_qua in ['tot', 'xuat_sac']))
                rec.diem_hieu_suat = round((good / total) * 100, 1)
            else:
                rec.diem_hieu_suat = 0.0

    @api.depends('cong_viec_ids.trang_thai', 'cong_viec_ids.danh_gia_hieu_qua', 'du_an_ids')
    def _compute_thong_ke(self):
        for rec in self:
            rec.so_du_an = len(rec.du_an_ids)
            rec.so_cong_viec_hoan_thanh = len(
                rec.cong_viec_ids.filtered(lambda t: t.trang_thai == 'hoan_thanh'))
            rec.so_cong_viec_tre_han = len(
                rec.cong_viec_ids.filtered(lambda t: t.danh_gia_hieu_qua == 'kem'))

    def action_xem_du_an(self):
        """Mở danh sách dự án mà nhân viên này tham gia."""
        return {
            'name': f'Dự án của {self.ho_ten}',
            'type': 'ir.actions.act_window',
            'res_model': 'du_an',
            'view_mode': 'kanban,tree,form',
            'domain': [('id', 'in', self.du_an_ids.ids)],
        }

    def action_xem_cong_viec(self):
        """Mở danh sách công việc được giao cho nhân viên này."""
        return {
            'name': f'Công việc của {self.ho_ten}',
            'type': 'ir.actions.act_window',
            'res_model': 'cong_viec',
            'view_mode': 'tree,form',
            'domain': [('nguoi_thuc_hien_id', '=', self.id)],
            'context': {'default_nguoi_thuc_hien_id': self.id},
        }

    @api.model
    def create(self, vals):
        record = super(NhanVienInherit, self).create(vals)
        if record.phong_ban_id:
            from datetime import date
            self.env['lich_su_lam_viec'].create({
                'nhan_vien_id': record.id,
                'loai_lich_su': 'chuc_vu',
                'phong_ban_id': record.phong_ban_id.id,
                'ten_cong_viec': f"Bắt đầu làm việc tại {record.phong_ban_id.ten_phong_ban}",
                'ngay_bat_dau': date.today()
            })
        return record

    def write(self, vals):
        old_departments = {rec.id: rec.phong_ban_id.id for rec in self}
        res = super(NhanVienInherit, self).write(vals)
        for rec in self:
            if 'phong_ban_id' in vals:
                new_dept_id = vals['phong_ban_id']
                if old_departments[rec.id] != new_dept_id:
                    from datetime import date
                    old_history = self.env['lich_su_lam_viec'].search([
                        ('nhan_vien_id', '=', rec.id),
                        ('loai_lich_su', '=', 'chuc_vu'),
                        ('ngay_ket_thuc', '=', False)
                    ], limit=1)
                    if old_history:
                        old_history.write({'ngay_ket_thuc': date.today(), 'ghi_chu': 'Chuyển phòng ban'})
                    
                    if new_dept_id:
                        self.env['lich_su_lam_viec'].create({
                            'nhan_vien_id': rec.id,
                            'loai_lich_su': 'chuc_vu',
                            'phong_ban_id': new_dept_id,
                            'ten_cong_viec': f"Điều chuyển sang {rec.phong_ban_id.ten_phong_ban}",
                            'ngay_bat_dau': date.today()
                        })
        return res
