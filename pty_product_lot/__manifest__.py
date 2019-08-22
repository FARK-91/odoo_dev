# -*- coding: utf-8 -*-
{
  'name':'Venta por lotes',
  'summary': """
        Vendedores pueden cotizar por lotes, packs o kits.
    """,
  'description': '''
          * Se agrega funcionalidad en Cotizaciones para que los vendedores puedan cerrar ventas de productos por lotes o packs.
          * El usuario admin define los lotes de cada producto, los vendedores solo pueden seleccionarlos mas no editarlos ni eliminarlos.

    ''',
  'version':'1.0.3',
  'author':'Ing. Renier Ferrer',
  'website': "https://fark-91.github.io/Portafolio/",
  'application': False,
  'depends': ['base', 'sale', 'stock'],
  'data': [

  ],
}
