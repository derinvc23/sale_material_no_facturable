# -*- coding: utf-8 -*-
{
    'name': u'Materiales No Facturables en OV',
    'version': '10.0.1.0.0',
    'category': 'Sales',
    'summary': u'Agrega materiales no facturables en Órdenes de Venta con salida de inventario automática',
    'author': 'Aluminios de Bolivia',
    'depends': ['sale', 'stock', 'sale_stock'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
