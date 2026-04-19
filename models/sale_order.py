# -*- coding: utf-8 -*-
from odoo import api, fields, models
import odoo.addons.decimal_precision as dp


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('state', 'order_line.invoice_status', 'order_line.no_facturable')
    def _get_invoice_status(self):
        """Para órdenes SIN líneas NF usa la lógica estándar de Odoo.
        Para órdenes CON líneas NF determina el estado mirando SOLO las líneas
        facturables, ignorando las NF para que no afecten el estado de la OV."""
        # Órdenes sin líneas NF → lógica estándar de Odoo (sin cambios)
        without_nf = self.filtered(
            lambda o: not o.order_line.filtered(lambda l: l.no_facturable)
        )
        super(SaleOrder, without_nf)._get_invoice_status()

        # Órdenes con líneas NF → calcular basado solo en líneas facturables
        for order in (self - without_nf):
            if order.state not in ('sale', 'done'):
                order.invoice_status = 'nothing_to_invoice'
                continue

            non_nf_lines = order.order_line.filtered(lambda l: not l.no_facturable)

            if not non_nf_lines:
                # Solo tiene líneas NF, sin nada facturable
                order.invoice_status = 'nothing_to_invoice'
            elif any(l.invoice_status == 'to invoice' for l in non_nf_lines):
                order.invoice_status = 'to invoice'
            elif all(l.invoice_status == 'invoiced' for l in non_nf_lines):
                order.invoice_status = 'invoiced'
            else:
                order.invoice_status = 'nothing_to_invoice'


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
        """Líneas no facturables siempre se tratan como 'invoiced'
        para no bloquear el estado de facturación de la OV."""
        super(SaleOrderLine, self)._get_invoice_status()
        for line in self:
            if line.no_facturable:
                line.invoice_status = 'invoiced'
