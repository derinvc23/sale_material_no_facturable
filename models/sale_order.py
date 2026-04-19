# -*- coding: utf-8 -*-
from odoo import api, fields, models
import odoo.addons.decimal_precision as dp


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('state', 'order_line.invoice_status', 'order_line.no_facturable')
    def _get_invoice_status(self):
        """Si todas las líneas facturables están facturadas y solo quedan líneas NF
        con estado 'nothing_to_invoice', la OV debe mostrarse como 'Facturado'."""
        super(SaleOrder, self)._get_invoice_status()
        for order in self:
            if order.state not in ('sale', 'done'):
                continue
            # Solo corregir cuando quede en 'nothing_to_invoice'
            if order.invoice_status != 'nothing_to_invoice':
                continue
            lines = order.order_line
            if not lines:
                continue
            nf_lines = lines.filtered(lambda l: l.no_facturable)
            non_nf_lines = lines.filtered(lambda l: not l.no_facturable)
            # Si hay líneas NF y todas las líneas facturables ya están facturadas
            if nf_lines and all(l.invoice_status == 'invoiced' for l in non_nf_lines):
                order.invoice_status = 'invoiced'


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    no_facturable = fields.Boolean(
        string='No Facturable',
        default=False,
        help=u'Si está marcado, este producto/material NO generará línea en la factura, '
             u'pero SÍ generará movimiento de inventario (salida de stock) al confirmar la OV.',
    )
    costo_material = fields.Float(
        string=u'Costo Unit.',
        digits=dp.get_precision('Product Price'),
        default=0.0,
        help=u'Costo unitario del material (se autocompleta desde el costo estándar del producto). '
             u'Solo aplica para líneas marcadas como No Facturables.',
    )

    @api.onchange('product_id', 'no_facturable')
    def _onchange_costo_material(self):
        if self.no_facturable and self.product_id:
            self.costo_material = self.product_id.standard_price

    @api.depends(
        'state', 'product_id', 'qty_invoiced', 'qty_delivered',
        'product_uom_qty', 'no_facturable',
    )
    def _get_to_invoice_qty(self):
        """Líneas no facturables siempre tienen qty_to_invoice = 0."""
        super(SaleOrderLine, self)._get_to_invoice_qty()
        for line in self:
            if line.no_facturable:
                line.qty_to_invoice = 0.0

    @api.depends(
        'state', 'product_id', 'qty_invoiced', 'qty_delivered',
        'product_uom_qty', 'order_id.state', 'no_facturable',
    )
    def _get_invoice_status(self):
        """Líneas no facturables se tratan como 'invoiced' para no bloquear
        el estado de facturación de la OV una vez que los servicios están facturados."""
        super(SaleOrderLine, self)._get_invoice_status()
        for line in self:
            if line.no_facturable and line.state in ('sale', 'done'):
                line.invoice_status = 'invoiced'
