from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    custom_measure_ids = fields.One2many(
        'sale.order.line.measure', 'order_line_id',
        string="Mesures personnalisées")
    custom_measure_summary = fields.Char(
        string="Résumé des mesures",
        compute='_compute_custom_measure_summary', store=True)

    @api.depends('custom_measure_ids.value_display', 'custom_measure_ids.name')
    def _compute_custom_measure_summary(self):
        for line in self:
            parts = []
            for m in line.custom_measure_ids:
                unit = (' %s' % m.unit) if m.unit else ''
                parts.append('%s : %s%s' % (m.name, m.value_display or '', unit))
            line.custom_measure_summary = ' | '.join(parts)
