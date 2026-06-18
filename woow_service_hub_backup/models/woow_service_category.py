from odoo import fields, models


class WoowServiceCategory(models.Model):
    _name = "woow.service.category"
    _description = "Service Category"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    color = fields.Integer(string="Color Index")

    _sql_constraints = [
        ("name_uniq", "UNIQUE(name)", "Category name must be unique!"),
    ]
