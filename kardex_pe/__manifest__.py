# -*- coding: utf-8 -*-
{
  'name':'kardex Peruano',
  'summary': """
        Custom Module
    """,
  'description': '''
          Módulo para controlar los movimientos de inventario de acuerdo a su facturacion:
            * Para ventas cada producto que sale es etiquetado con su numero de factura
              correspondiente.
            * Para compras se cumple lo mismo pero sin llegar a la facturacions,
              solo se etiqueta con el nombre del proveedor.

	  ''',
  'version':'1.1.0',
  'author':'Ing. Renier Ferrer',
  'website': "https://fark-91.github.io/Portafolio/",
  'application': False,
  'depends': ['base', 'stock', 'sale', 'purchase', 'account'],
  'data': [
        'views/acs_inherit_stock_move_line.xml',
        'views/acs_inherit_stock_move_search.xml',
  ],
}
