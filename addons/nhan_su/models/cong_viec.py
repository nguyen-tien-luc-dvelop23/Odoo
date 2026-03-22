# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import date

class CongViec(models.Model):
    _name = 'cong_viec'
    _description = 'Quản lý Công việc/Tác vụ'
    _rec_name = 'ten_cong_viec'
    _order = 'deadline asc, id desc'

    active = fields.Boolean(string="Hoạt động", default=True)

    ma_cong_viec = fields.Char(
        string="Mã công việc",
        readonly=True,
        copy=False,
        default=lambda self: 'Mới'
    )
    ten_cong_viec = fields.Char(string="Tên công việc", required=True)
    mo_ta = fields.Text(string="Mô tả chi tiết")
    
    du_an_id = fields.Many2one('du_an', string="Thuộc dự án", required=True, ondelete='cascade')
    nguoi_thuc_hien_id = fields.Many2one(
        'nhan_vien', 
        string="Người thực hiện"
    )
    
    deadline = fields.Date(string="Deadline", required=True)
    ngay_hoan_thanh_thuc_te = fields.Date(string="Đã hoàn thành vào ngày", readonly=True)
    
    trang_thai = fields.Selection([
        ('moi', 'Mới'),
        ('dang_xu_ly', 'Đang xử lý'),
        ('hoan_thanh', 'Hoàn thành'),
        ('huy_bo', 'Hủy bỏ')
    ], string="Trạng thái", default='moi')

    uu_tien = fields.Selection([
        ('thap', 'Thấp'),
        ('trung_binh', 'Trung bình'),
        ('cao', 'Cao'),
        ('khan_cap', 'Khẩn cấp'),
    ], string="Mức độ ưu tiên", default='trung_binh')

    danh_gia_hieu_qua = fields.Selection([
        ('xuat_sac', 'Xuất sắc (> 2 ngày trước deadline)'),
        ('tot', 'Đạt/Tốt (Đúng hạn)'),
        ('kem', 'Kém (Trễ hạn)'),
    ], string="Đánh giá tự động", compute="_compute_danh_gia", store=True)

    is_qua_han = fields.Boolean(
        string="Quá hạn?",
        compute="_compute_is_qua_han",
        store=True
    )

    @api.model
    def create(self, vals):
        if vals.get('ma_cong_viec', 'Mới') == 'Mới':
            vals['ma_cong_viec'] = self.env['ir.sequence'].next_by_code('cong_viec.sequence') or 'CV001'
        record = super(CongViec, self).create(vals)
        
        # Auto create Work History when assigned
        if record.nguoi_thuc_hien_id:
            self.env['lich_su_lam_viec'].create({
                'nhan_vien_id': record.nguoi_thuc_hien_id.id,
                'loai_lich_su': 'cong_viec',
                'du_an_id': record.du_an_id.id,
                'cong_viec_id': record.id,
                'ten_cong_viec': record.ten_cong_viec,
            })
        return record

    def write(self, vals):
        res = super(CongViec, self).write(vals)
        for rec in self:
            # 1. Employee changed -> close old history and open new history
            if 'nguoi_thuc_hien_id' in vals:
                old_history = self.env['lich_su_lam_viec'].search([
                    ('cong_viec_id', '=', rec.id),
                    ('loai_lich_su', '=', 'cong_viec'),
                    ('ngay_ket_thuc', '=', False)
                ], limit=1)
                if old_history:
                    old_history.write({
                        'ngay_ket_thuc': date.today(),
                        'ghi_chu': 'Bàn giao cho người khác'
                    })
                if rec.nguoi_thuc_hien_id:
                    self.env['lich_su_lam_viec'].create({
                        'nhan_vien_id': rec.nguoi_thuc_hien_id.id,
                        'loai_lich_su': 'cong_viec',
                        'du_an_id': rec.du_an_id.id,
                        'cong_viec_id': rec.id,
                        'ten_cong_viec': rec.ten_cong_viec,
                    })

            # 2. Task status changed to done/cancel -> close active history
            if 'trang_thai' in vals and vals['trang_thai'] in ['hoan_thanh', 'huy_bo']:
                active_history = self.env['lich_su_lam_viec'].search([
                    ('cong_viec_id', '=', rec.id),
                    ('loai_lich_su', '=', 'cong_viec'),
                    ('ngay_ket_thuc', '=', False)
                ])
                if active_history:
                    ghi_chu = "Hoàn thành công việc" if vals['trang_thai'] == 'hoan_thanh' else "Công việc bị hủy"
                    active_history.write({
                        'ngay_ket_thuc': date.today(),
                        'ghi_chu': ghi_chu
                    })
        return res

    @api.constrains('nguoi_thuc_hien_id', 'du_an_id')
    def _check_nguoi_thuc_hien(self):
        for rec in self:
            if rec.nguoi_thuc_hien_id and rec.du_an_id and rec.du_an_id.thanh_vien_ids:
                if rec.nguoi_thuc_hien_id not in rec.du_an_id.thanh_vien_ids:
                    raise ValidationError(
                        f"Nhân viên '{rec.nguoi_thuc_hien_id.ho_ten}' không phải thành viên của dự án '{rec.du_an_id.ten_du_an}'!\n"
                        "Vui lòng thêm nhân viên vào danh sách thành viên dự án trước."
                    )

    def action_bat_dau_lam(self):
        for rec in self:
            if rec.trang_thai == 'moi':
                rec.trang_thai = 'dang_xu_ly'

    def action_hoan_thanh(self):
        for rec in self:
            if rec.trang_thai == 'huy_bo':
                raise UserError("Không thể hoàn thành công việc đã hủy bỏ!")
            if rec.trang_thai != 'hoan_thanh':
                rec.trang_thai = 'hoan_thanh'
                rec.ngay_hoan_thanh_thuc_te = date.today()

    def action_huy_bo(self):
        for rec in self:
            if rec.trang_thai == 'hoan_thanh':
                raise UserError("Không thể hủy bỏ công việc đã hoàn thành!")
            rec.trang_thai = 'huy_bo'

    @api.depends('trang_thai', 'ngay_hoan_thanh_thuc_te', 'deadline')
    def _compute_danh_gia(self):
        for rec in self:
            if rec.trang_thai == 'hoan_thanh' and rec.ngay_hoan_thanh_thuc_te and rec.deadline:
                delta = (rec.deadline - rec.ngay_hoan_thanh_thuc_te).days
                if delta >= 2:
                    rec.danh_gia_hieu_qua = 'xuat_sac'
                elif delta >= 0:
                    rec.danh_gia_hieu_qua = 'tot'
                else:
                    rec.danh_gia_hieu_qua = 'kem'
            else:
                rec.danh_gia_hieu_qua = False

    @api.depends('deadline', 'trang_thai')
    def _compute_is_qua_han(self):
        today = date.today()
        for rec in self:
            if rec.deadline and rec.trang_thai not in ['hoan_thanh', 'huy_bo']:
                rec.is_qua_han = rec.deadline < today
            else:
                rec.is_qua_han = False
