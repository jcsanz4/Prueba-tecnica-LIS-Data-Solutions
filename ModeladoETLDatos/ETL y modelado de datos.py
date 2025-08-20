import pandas as pd
import numpy as np

#Carga de ficheros
products = pd.read_csv(r"C:\Users\Juan Carlos\Documents\Prueba tecnica LIS\ModeladoETLDatos\products.csv",sep=";")
invoices_products = pd.read_csv(r"C:\Users\Juan Carlos\Documents\Prueba tecnica LIS\ModeladoETLDatos\invoices_products.csv",sep=";")
invoices_header = pd.read_csv(r"C:\Users\Juan Carlos\Documents\Prueba tecnica LIS\ModeladoETLDatos\invoices_header.csv",sep=";")
daily_currencies = pd.read_csv(r"C:\Users\Juan Carlos\Documents\Prueba tecnica LIS\ModeladoETLDatos\daily_currencies.csv",sep=";")
purchase_budget = pd.read_excel(r"C:\Users\Juan Carlos\Documents\Prueba tecnica LIS\ModeladoETLDatos\purchase_budget.xls",header=1)
suppliers = pd.read_csv(r"C:\Users\Juan Carlos\Documents\Prueba tecnica LIS\ModeladoETLDatos\suppliers.csv",sep=";")
#Limpieza de datos
#Comprobación de tipos de datos
daily_currencies.info()
purchase_budget.info()
products.info()
invoices_products.info()
invoices_header.info()
daily_currencies.info()
suppliers.info()
#Primero transformamos los datos de fecha en formato fecha
invoices_header["InvoiceDate"] = pd.to_datetime(invoices_header["InvoiceDate"])
invoices_header["InboundDate"] = pd.to_datetime(invoices_header["InboundDate"])
invoices_header["OrderDate"] = pd.to_datetime(invoices_header["OrderDate"])
daily_currencies["Date"] = pd.to_datetime(daily_currencies["Date"])

#Limpieza de datos nulos
#Encontramos datos nulos en suppliers y products que al ser tan pocos podemos eliminar 
products[products["Type"].isnull()] #Los Nans del tipo de producto corresponde a un 17% de los datos de la tabla por lo que no eliminaré esas filas ya que aunque no se tenga el tipo de prodycto se tiene el nombre y se podría interpretar, pero con tipo 1, tipo 2 es realmente dificiil de saber.
suppliers[suppliers.isnull().any(axis=1)] #No considero oportuno eliminar las columnas de los proveedores aunque se desconozca el metodo de pago o los payterms ya que tienen ventas asociadas.

########
#Ver si hay duplicados  en cada dataset
products.duplicated().sum()
suppliers.duplicated().sum()
daily_currencies.duplicated().sum()
purchase_budget.duplicated().sum()
invoices_header.duplicated().sum()
invoices_products.duplicated().sum()
#Hay 21 duplicados en invoices products por lo que los eliminamos de la tabla
invoices_products=invoices_products.drop_duplicates()

#------------------------------#
#Importe total de las compras que se realizan diriamente

#Unimos la tabla de dimensiones de invoices header con invoices products mediante invoice
invoices_merged = invoices_products.merge(invoices_header, on="Invoice", how="left")
#Ahora quiero unirlo con proveedores mediante supplier
invoices_merged_suppliers= invoices_merged.merge(suppliers, left_on="Supplier", right_on="IDSupplier", how="left")

#Calculamos el importe con la moneda correspondiente
invoices_merged_suppliers["importe_moneda"] = invoices_merged_suppliers["Quantity"] * invoices_merged_suppliers["PurchasePrice (Unit)"]
#Y para saber el tipo de cambio que hay, hay que unirlo con daily currencies para saber el precio de mercado de cada moneda
invoices_merged_suppliers_daily_currencies = invoices_merged_suppliers.merge(daily_currencies[["Date", "Currency", "Close"]],left_on=["InvoiceDate", "Currency"],right_on=["Date", "Currency"],how="left")

#Un avez tenemos esto podemos calcular el importe en EUR pero como tenemos que aplicar tipo de cambio si la moneda es distinta al europeo hacemos esa funcion lambda
invoices_merged_suppliers_daily_currencies["importe_eur"] = invoices_merged_suppliers_daily_currencies["importe_eur"] = invoices_merged_suppliers_daily_currencies.apply(lambda row: row["importe_moneda"] if row["Currency"] == "EUR" else row["importe_moneda"] * row["Close"],axis=1)

#Agrupamos por día y sacamos la media de los cuales podemos obtener estos datos:
diary_sells = invoices_merged_suppliers_daily_currencies.groupby("InvoiceDate")["importe_eur"].sum()
diary_sells_df = diary_sells.reset_index()

#---------------------------------------#
#Obtener un ranking de proveedores según el importe total comprado en un periodo de tiempo determinado y según el número de referencias o productos distintos comprados
#Ranking de proveedores para una fecha segun el importe total
ranking_proveedores_importe_total=invoices_merged_suppliers_daily_currencies[(invoices_merged_suppliers_daily_currencies["InvoiceDate"] >= "2014-05-26") & (invoices_merged_suppliers_daily_currencies["InvoiceDate"] <= "2014-07-25")].groupby(["SupplierName"]).sum().sort_values(by="importe_eur",ascending=False).reset_index()
#Ranking de los proveedores segun el numero de productos diferentes comprados
ranking_proveedores_productos=invoices_merged_suppliers_daily_currencies.groupby("SupplierName").agg(num_productos_distintos=("Product", "nunique")).sort_values(by="num_productos_distintos",ascending=False)
#--------------------------------------#
#Para medir la calidad del proveedor el responsable nos pide que midamos el tiempo de entrega o lead time real de las compras realizadas y que lo comparemos con el lead time teórico.
#Pasamos las columnas a datetime y hacemos la resta de la fecha de pedido y la fecha de factura para ver lo que tarda
invoices_merged_suppliers_daily_currencies['lead_time_real'] = (invoices_merged_suppliers_daily_currencies['InvoiceDate'] - invoices_merged_suppliers_daily_currencies['OrderDate']).dt.days

#Compararlo con el lead time teorico para ello creamos el lead time teorico como otra columna
def lead_time_teorico(row):
    if row['Country'] == 'ES':
        return 10
    elif row['Currency'] == 'EUR':
        return 20
    else:
        return 45
invoices_merged_suppliers_daily_currencies['lead_time_teorico'] = invoices_merged_suppliers_daily_currencies.apply(lead_time_teorico, axis=1)
invoices_merged_suppliers_daily_currencies['days_desviation'] = invoices_merged_suppliers_daily_currencies['lead_time_real'] - invoices_merged_suppliers_daily_currencies['lead_time_teorico']
#Cuando el lead time real del proveedor sea negativo estarás entregando antes de lo esperado, por lo que en tiempo y forma. Cuando sea positivo, el proveedor se habrá retrasado.

#----------------------------------------------#
#Esta información se quiere consumir mediante una media anual (considerando como referencia la fecha de emisión del pedido), pues se entiende que en periodos más cortos puede haber fluctuaciones que distorsionen la medida.
#Al ser una media anual, tenemos que sacar el año de las fechas de InvoiceDate
invoices_merged_suppliers_daily_currencies['year'] = invoices_merged_suppliers_daily_currencies['InvoiceDate'].dt.year
#Por tanto el resumen anual quedaría algo así:
resumen_anual = invoices_merged_suppliers_daily_currencies.groupby(['year', 'SupplierName', 'Product']).agg(lead_time_real_promedio=('lead_time_real', 'mean'),lead_time_teorico_promedio=('lead_time_teorico', 'mean'),desviacion_promedio=('lead_time_real', lambda x: (x - invoices_merged_suppliers_daily_currencies.loc[x.index, 'lead_time_teorico']).mean()),num_pedidos=('InvoiceDate', 'count')).reset_index()
#por tanto nuestras tablas de hecho podrían ser resumen anual, ranking de proveedores por prodyctos distintos y ranking de proveedores por importe total.
#guardamos dichas tablas
# Ahora se exportan estas nuevas tablas a csv para integrarlas donde corresponda.
ranking_proveedores_importe_total.to_csv(r"ranking_proveedores_importe_total.csv")
ranking_proveedores_productos.to_csv(r"ranking_proveedores_productos.csv")
resumen_anual.to_csv(r"resumen_anual.csv",index=False)




