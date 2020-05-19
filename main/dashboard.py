from datetime import date, timedelta, datetime
import json
from comprobante.models import Comprobante
from empresa.models import Cliente

__author__ = 'mlambir'

months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre',
          'Noviembre', 'Diciembre']


def get_past_months(year, month):
    while True:
        yield "{}-{:02d}".format(year, month)
        month -= 1
        if month == 0:
            month = 12
            year -= 1


def get_past_days(year, month, day):
    d = date(year, month, day)
    while True:
        yield "{}-{:02d}-{:02d}".format(d.year, d.month, d.day)
        d = d - timedelta(days=1)


def get_line_dataset(data):
    labels = list(sorted(list(data.keys())))
    return {"labels": labels,
            "datasets": [{
                "data": [data[l] for l in labels]
            }]}


def get_pie_dataset(data):
    ret = [{"label": l, "value": d} for l, d in sorted(list(data.items()), key=lambda x: x[0])]
    if len(ret) > 10:
        ret = [{"label": "Otros", "value": sum([i["value"] for i in ret[10:]])}] + ret[:9]

    for i in ret:
        if i["value"] < 0:
            i["value"] = 0

    return {"labels": [i["label"] for i in ret],
            "datasets": [{"data": [i["value"]for i in ret]}]}


def get_cbtes_monthly_dataset(data, labels):
    ret = {
        "labels": labels,
        "datasets": []
    }
    for k in data:
        d = {"label": k, "data": []}
        for l in labels:
            d["data"].append(data[k][l])
        ret["datasets"].append(d)
    return ret


def crear_consumidor_final():
    cliente = Cliente(tipo_doc_id=5, nro_doc=0, nombre="Consumidor Final", condicion_iva_id=5, editable=False)
    cliente.save()


def get_cbtes(date_from, date_to):
    return Comprobante.objects.order_by('fecha_emision') \
        .prefetch_related('detallecomprobante_set') \
        .prefetch_related('tributocomprobante_set') \
        .prefetch_related('tipo_cbte') \
        .prefetch_related('punto_vta') \
        .prefetch_related('cliente') \
        .prefetch_related('detallecomprobante_set__producto') \
        .prefetch_related('detallecomprobante_set__alicuota_iva') \
        .filter(fecha_emision__gte=date_from, fecha_emision__lte=date_to).all()


def get_fact_year(now):
    from_january = date(datetime.now().year, 1, 1)
    to_now = date(now.year, now.month, now.day)
    cbtes_year = get_cbtes(from_january, to_now)
    fact_year = 0

    for cbte in cbtes_year:
        mult = 1 if cbte.es_factura() or cbte.es_nota_debito() or cbte.es_recibo() else -1
        if cbte.moneda_ctz:
            fact_year += float(cbte.importe_total * mult * cbte.moneda_ctz)
        else:
            fact_year += float(cbte.importe_total * mult)
    return fact_year


def get_dashboard_data():
    now = datetime.now()
    year = now.year - 1
    month = now.month + 1
    if month == 13:
        month = 1
        year += 1
    date_from = date(year, month, 1)
    date_to = date(date_from.year + 1, date_from.month, 1) - timedelta(days=1)

    if Cliente.objects.count() == 0:
        crear_consumidor_final()

    cbtes = get_cbtes(date_from, date_to)
    fact_year = get_fact_year(now)

    month_gen = get_past_months(now.year, now.month)
    day_gen = get_past_days(now.year, now.month, now.day)

    fact_monthly = {next(month_gen): 0 for m in range(12)}
    fact_daily = {next(day_gen): 0 for m in range(30)}

    tipos = list(set([str(c.tipo_cbte) for c in cbtes]))
    cbtes_monthly = {t: None for t in tipos}
    for k in cbtes_monthly:
        month_gen = get_past_months(now.year, now.month)
        cbtes_monthly[k] = {next(month_gen): 0 for m in range(12)}

    client_year = {}
    client_month = {}

    prod_year = {}
    prod_month = {}

    cbtes_sin_aut = 0
    fact_today = 0
    for cbte in cbtes:
        month_repr = "{}-{:02d}".format(cbte.fecha_emision.year, cbte.fecha_emision.month)
        cbtes_monthly[str(cbte.tipo_cbte)][month_repr] += 1

        mult = 1 if cbte.es_factura() or cbte.es_nota_debito() or cbte.es_recibo() else -1

        day_repr = "{}-{:02d}-{:02d}".format(cbte.fecha_emision.year, cbte.fecha_emision.month, cbte.fecha_emision.day)

        if cbte.moneda_ctz:
            fact_monthly[month_repr] += float(cbte.importe_total * mult * cbte.moneda_ctz)
            client_year[cbte.cliente.nombre] = client_year.get(cbte.cliente.nombre, 0) + float(
                cbte.importe_total * mult * cbte.moneda_ctz)
        else:
            fact_monthly[month_repr] += float(cbte.importe_total * mult)
            client_year[cbte.cliente.nombre] = client_year.get(cbte.cliente.nombre, 0) + float(
                cbte.importe_total * mult)

        if cbte.es_factura():
            for item in cbte.detallecomprobante_set.all():
                if item.producto:
                    prod_year[item.producto.nombre_completo] = prod_year.get(item.producto.nombre_completo, 0) + float(
                        item.precio_total)

        if day_repr in fact_daily:
            fact_daily[day_repr] += float(cbte.importe_total * mult)
            if cbte.moneda_ctz:
                client_month[cbte.cliente.nombre] = client_month.get(cbte.cliente.nombre, 0) + float(
                    cbte.importe_total * mult * cbte.moneda_ctz)
            else:
                client_month[cbte.cliente.nombre] = client_month.get(cbte.cliente.nombre, 0) + float(
                    cbte.importe_total * mult)
            if cbte.es_factura():
                for item in cbte.detallecomprobante_set.all():
                    if item.producto:
                        prod_month[item.producto.nombre_completo] = prod_month.get(item.producto.nombre_completo,
                                                                                   0) + float(item.precio_total)

        if not cbte.cae:
            cbtes_sin_aut += 1

        if now.date() == cbte.fecha_emision:
            if cbte.moneda_ctz:
                fact_today += float(cbte.importe_total * mult * cbte.moneda_ctz)
            else:
                fact_today += float(cbte.importe_total * mult)

    current_fact_period = "{}-{}".format(now.year, str(now.month).zfill(2))

    ret = {
        "cbtes_month": json.dumps(get_cbtes_monthly_dataset(cbtes_monthly, list(reversed(list(fact_monthly.keys()))))),
        "fact_monthly": json.dumps(get_line_dataset(fact_monthly)),
        "fact_daily": json.dumps(get_line_dataset(fact_daily)),
        "client_year": json.dumps(get_pie_dataset(client_year)),
        "client_month": json.dumps(get_pie_dataset(client_month)),
        "prod_year": json.dumps(get_pie_dataset(prod_year)),
        "prod_month": json.dumps(get_pie_dataset(prod_month)),
        "cbtes_sin_aut": cbtes_sin_aut,
        "fact_today": fact_today,
        "fact_month": fact_monthly[current_fact_period],
        "fact_year": fact_year,
        "show_vinculacion_msg": False,
    }
    return ret
