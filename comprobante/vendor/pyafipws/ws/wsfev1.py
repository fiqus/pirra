#!/usr/bin/python
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""Módulo para obtener CAE/CAEA, código de autorización electrónico webservice
WSFEv1 de AFIP (Factura Electrónica Nacional - Proyecto Version 1 - 2.5)
Según RG 2485/08, RG 2757/2010, RG 2904/2010 y RG2926/10 (CAE anticipado),
RG 3067/2011 (RS - Monotributo), RG 3571/2013 (Responsables inscriptos IVA),
RG 3668/2014 (Factura A IVA F.8001), RG 3749/2015 (R.I. y exentos)
Más info: http://www.sistemasagiles.com.ar/trac/wiki/ProyectoWSFEv1
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2015 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.16d"

import datetime
import os
import sys
from comprobante.vendor.pyafipws.utils import verifica, inicializar_y_capturar_excepciones, BaseWS, get_install_dir
import logging

HOMO = False  # solo homologación
TYPELIB = False  # usar librería de tipos (TLB)
LANZAR_EXCEPCIONES = False  # valor por defecto: True

logger = logging.getLogger(__name__)

# WSDL = "https://www.sistemasagiles.com.ar/simulador/wsfev1/call/soap?WSDL=None"
WSDL = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"


# WSDL = "file:///home/reingart/tmp/service.asmx.xml"


class WSFEv1(BaseWS):
    "Interfaz para el WebService de Factura Electrónica Version 1 - 2.5"
    _public_methods_ = ['CrearFactura', 'AgregarIva', 'CAESolicitar',
                        'AgregarTributo', 'AgregarCmpAsoc', 'AgregarOpcional',
                        'CompUltimoAutorizado', 'CompConsultar',
                        'CAEASolicitar', 'CAEAConsultar', 'CAEARegInformativo',
                        'CAEASinMovimientoInformar',
                        'ParamGetTiposCbte',
                        'ParamGetTiposConcepto',
                        'ParamGetTiposDoc',
                        'ParamGetTiposIva',
                        'ParamGetTiposMonedas',
                        'ParamGetTiposOpcional',
                        'ParamGetTiposTributos',
                        'ParamGetCotizacion',
                        'ParamGetPtosVenta',
                        'AnalizarXml', 'ObtenerTagXml', 'LoadTestXML',
                        'SetParametros', 'SetTicketAcceso', 'GetParametro',
                        'EstablecerCampoFactura',
                        'Dummy', 'Conectar', 'DebugLog', 'SetTicketAcceso']
    _public_attrs_ = ['Token', 'Sign', 'Cuit',
                      'AppServerStatus', 'DbServerStatus', 'AuthServerStatus',
                      'XmlRequest', 'XmlResponse', 'Version', 'Excepcion', 'LanzarExcepciones',
                      'Resultado', 'Obs', 'Observaciones', 'Traceback', 'InstallDir',
                      'CAE', 'Vencimiento', 'Eventos', 'Errores', 'ErrCode', 'ErrMsg',
                      'Reprocesar', 'Reproceso', 'EmisionTipo', 'CAEA',
                      'CbteNro', 'CbtDesde', 'CbtHasta', 'FechaCbte',
                      'ImpTotal', 'ImpNeto', 'ImptoLiq',
                      'ImpIVA', 'ImpOpEx', 'ImpTrib', ]

    _reg_progid_ = "WSFEv1"
    _reg_clsid_ = "{CA0E604D-E3D7-493A-8880-F6CDD604185E}"

    if TYPELIB:
        _typelib_guid_ = '{B1D7283C-3EC2-463E-89B4-11F5228E2A15}'
        _typelib_version_ = 1, 13
        _com_interfaces_ = ['IWSFEv1']
        ##_reg_class_spec_ = "wsfev1.WSFEv1"

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
    Reprocesar = True  # recuperar automaticamente CAE emitidos
    LanzarExcepciones = LANZAR_EXCEPCIONES
    factura = None

    def inicializar(self):
        BaseWS.inicializar(self)
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.Resultado = self.Motivo = self.Reproceso = ''
        self.LastID = self.LastCMP = self.CAE = self.CAEA = self.Vencimiento = ''
        self.CbteNro = self.CbtDesde = self.CbtHasta = self.PuntoVenta = None
        self.ImpTotal = self.ImpIVA = self.ImpOpEx = self.ImpNeto = self.ImptoLiq = self.ImpTrib = None
        self.EmisionTipo = self.Periodo = self.Orden = ""
        self.FechaCbte = self.FchVigDesde = self.FchVigHasta = self.FchTopeInf = self.FchProceso = ""

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        if 'Errors' in ret:
            errores = ret['Errors']
            for error in errores:
                self.Errores.append("%s: %s" % (
                    error['Err']['Code'],
                    error['Err']['Msg'],
                ))
            self.ErrCode = ' '.join([str(error['Err']['Code']) for error in errores])
            self.ErrMsg = '\n'.join(self.Errores)
        if 'Events' in ret:
            events = ret['Events']
            for evt in events:
                self.Eventos.append("%s: %s" % (evt['Evt']['Code'], evt['Evt']['Msg'],))

    @inicializar_y_capturar_excepciones
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        result = self.client.FEDummy()['FEDummyResult']
        self.AppServerStatus = result['AppServer']
        self.DbServerStatus = result['DbServer']
        self.AuthServerStatus = result['AuthServer']
        return True

    def CrearFactura(self, concepto=1, tipo_doc=80, nro_doc="", tipo_cbte=1, punto_vta=0,
                     cbt_desde=0, cbt_hasta=0, imp_total=0.00, imp_tot_conc=0.00, imp_neto=0.00,
                     imp_iva=0.00, imp_trib=0.00, imp_op_ex=0.00, fecha_cbte="", fecha_venc_pago=None,
                     fecha_serv_desde=None, fecha_serv_hasta=None,  # --
                     moneda_id="PES", moneda_ctz="1.0000", caea=None, **kwargs
                     ):
        "Creo un objeto factura (interna)"
        # Creo una factura electronica de exportación 
        fact = {'tipo_doc': tipo_doc, 'nro_doc': nro_doc,
                'tipo_cbte': tipo_cbte, 'punto_vta': punto_vta,
                'cbt_desde': cbt_desde, 'cbt_hasta': cbt_hasta,
                'imp_total': imp_total, 'imp_tot_conc': imp_tot_conc,
                'imp_neto': imp_neto, 'imp_iva': imp_iva,
                'imp_trib': imp_trib, 'imp_op_ex': imp_op_ex,
                'fecha_cbte': fecha_cbte,
                'fecha_venc_pago': fecha_venc_pago,
                'moneda_id': moneda_id, 'moneda_ctz': moneda_ctz,
                'concepto': concepto,
                'cbtes_asoc': [],
                'tributos': [],
                'iva': [],
                'opcionales': [],
                }
        if fecha_serv_desde: fact['fecha_serv_desde'] = fecha_serv_desde
        if fecha_serv_hasta: fact['fecha_serv_hasta'] = fecha_serv_hasta
        if caea: fact['caea'] = caea

        self.factura = fact
        return True

    def EstablecerCampoFactura(self, campo, valor):
        if campo in self.factura or campo in ('fecha_serv_desde', 'fecha_serv_hasta', 'caea', 'fch_venc_cae'):
            self.factura[campo] = valor
            return True
        else:
            return False

    def AgregarCmpAsoc(self, tipo=1, pto_vta=0, nro=0, **kwarg):
        "Agrego un comprobante asociado a una factura (interna)"
        cmp_asoc = {'tipo': tipo, 'pto_vta': pto_vta, 'nro': nro}
        self.factura['cbtes_asoc'].append(cmp_asoc)
        return True

    def AgregarTributo(self, tributo_id=0, desc="", base_imp=0.00, alic=0, importe=0.00, **kwarg):
        "Agrego un tributo a una factura (interna)"
        tributo = {'tributo_id': tributo_id, 'desc': desc, 'base_imp': base_imp,
                   'alic': alic, 'importe': importe}
        self.factura['tributos'].append(tributo)
        return True

    def AgregarIva(self, iva_id=0, base_imp=0.0, importe=0.0, **kwarg):
        "Agrego un tributo a una factura (interna)"
        iva = {'iva_id': iva_id, 'base_imp': base_imp, 'importe': importe}
        self.factura['iva'].append(iva)
        return True

    def AgregarOpcional(self, opcional_id=0, valor="", **kwarg):
        "Agrego un dato opcional a una factura (interna)"
        op = {'opcional_id': opcional_id, 'valor': valor}
        self.factura['opcionales'].append(op)
        return True

    @inicializar_y_capturar_excepciones
    def CAESolicitar(self):
        f = self.factura
        ret = self.client.FECAESolicitar(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            FeCAEReq={
                'FeCabReq': {'CantReg': 1,
                             'PtoVta': f['punto_vta'],
                             'CbteTipo': f['tipo_cbte']},
                'FeDetReq': [{'FECAEDetRequest': {
                    'Concepto': f['concepto'],
                    'DocTipo': f['tipo_doc'],
                    'DocNro': f['nro_doc'],
                    'CbteDesde': f['cbt_desde'],
                    'CbteHasta': f['cbt_hasta'],
                    'CbteFch': f['fecha_cbte'],
                    'ImpTotal': f['imp_total'],
                    'ImpTotConc': f['imp_tot_conc'],
                    'ImpNeto': f['imp_neto'],
                    'ImpOpEx': f['imp_op_ex'],
                    'ImpTrib': f['imp_trib'],
                    'ImpIVA': f['imp_iva'],
                    # Fechas solo se informan si Concepto in (2,3)
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f.get('fecha_venc_pago'),
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f['fecha_venc_pago'],
                    'MonId': f['moneda_id'],
                    'MonCotiz': f['moneda_ctz'],
                    'CbtesAsoc': f['cbtes_asoc'] and [
                        {'CbteAsoc': {
                            'Tipo': cbte_asoc['tipo'],
                            'PtoVta': cbte_asoc['pto_vta'],
                            'Nro': cbte_asoc['nro']}}
                        for cbte_asoc in f['cbtes_asoc']] or None,
                    'Tributos': f['tributos'] and [
                        {'Tributo': {
                            'Id': tributo['tributo_id'],
                            'Desc': tributo['desc'],
                            'BaseImp': tributo['base_imp'],
                            'Alic': tributo['alic'],
                            'Importe': tributo['importe'],
                        }}
                        for tributo in f['tributos']] or None,
                    'Iva': f['iva'] and [
                        {'AlicIva': {
                            'Id': iva['iva_id'],
                            'BaseImp': iva['base_imp'],
                            'Importe': iva['importe'],
                        }}
                        for iva in f['iva']] or None,
                    'Opcionales': [
                                      {'Opcional': {
                                          'Id': opcional['opcional_id'],
                                          'Valor': opcional['valor'],
                                      }} for opcional in f['opcionales']] or None,
                }
                }]
            })

        result = ret['FECAESolicitarResult']

        logger.warning("SolicitaCAE")
        logger.warning("XMLRequest:")
        logger.warning(self.client.xml_request)
        logger.warning("XMLResponse")
        logger.warning(self.client.xml_response)

        if 'FeCabResp' in result:
            fecabresp = result['FeCabResp']
            fedetresp = result['FeDetResp'][0]['FECAEDetResponse']

            # Reprocesar en caso de error (recuperar CAE emitido anteriormente)
            if self.Reprocesar and ('Errors' in result or 'Observaciones' in fedetresp):
                for error in result.get('Errors', []) + fedetresp.get('Observaciones', []):
                    err_code = str(error.get('Err', error.get('Obs'))['Code'])
                    if fedetresp['Resultado'] == 'R' and err_code == '10016':
                        # guardo los mensajes xml originales
                        xml_request = self.client.xml_request
                        xml_response = self.client.xml_response
                        cae = self.CompConsultar(f['tipo_cbte'], f['punto_vta'], f['cbt_desde'], reproceso=True)
                        if cae and self.EmisionTipo == 'CAE':
                            self.Reproceso = 'S'
                            return cae
                        self.Reproceso = 'N'
                        # reestablesco los mensajes xml originales
                        self.client.xml_request = xml_request
                        self.client.xml_response = xml_response

            self.Resultado = fecabresp['Resultado']
            # Obs:
            for obs in fedetresp.get('Observaciones', []):
                self.Observaciones.append("%(Code)s: %(Msg)s" % (obs['Obs']))
            self.Obs = '\n'.join(self.Observaciones)
            self.CAE = fedetresp['CAE'] and str(fedetresp['CAE']) or ""
            self.EmisionTipo = 'CAE'
            self.Vencimiento = fedetresp['CAEFchVto']
            self.FechaCbte = fedetresp.get('CbteFch', "")  # .strftime("%Y/%m/%d")
            self.CbteNro = fedetresp.get('CbteHasta', 0)  # 1L
            self.PuntoVenta = fecabresp.get('PtoVta', 0)  # 4000
            self.CbtDesde = fedetresp.get('CbteDesde', 0)
            self.CbtHasta = fedetresp.get('CbteHasta', 0)
        self.__analizar_errores(result)
        return self.CAE

    @inicializar_y_capturar_excepciones
    def CompTotXRequest(self):
        ret = self.client.FECompTotXRequest(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
        )

        result = ret['FECompTotXRequestResult']
        return result['RegXReq']

    @inicializar_y_capturar_excepciones
    def CompUltimoAutorizado(self, tipo_cbte, punto_vta):
        ret = self.client.FECompUltimoAutorizado(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            PtoVta=punto_vta,
            CbteTipo=tipo_cbte,
        )

        result = ret['FECompUltimoAutorizadoResult']
        self.CbteNro = result['CbteNro']
        self.__analizar_errores(result)
        return self.CbteNro is not None and str(self.CbteNro) or ''

    @inicializar_y_capturar_excepciones
    def CompConsultar(self, tipo_cbte, punto_vta, cbte_nro, reproceso=False):
        difs = []  # si hay reproceso, verifico las diferencias con AFIP

        ret = self.client.FECompConsultar(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            FeCompConsReq={
                'CbteTipo': tipo_cbte,
                'CbteNro': cbte_nro,
                'PtoVta': punto_vta,
            })

        result = ret['FECompConsultarResult']
        if 'ResultGet' in result:
            resultget = result['ResultGet']

            if reproceso:
                # verifico los campos registrados coincidan con los enviados:
                f = self.factura
                verificaciones = {
                    'Concepto': f['concepto'],
                    'DocTipo': f['tipo_doc'],
                    'DocNro': f['nro_doc'],
                    'CbteDesde': f['cbt_desde'],
                    'CbteHasta': f['cbt_hasta'],
                    'CbteFch': f['fecha_cbte'],
                    'ImpTotal': f['imp_total'] and float(f['imp_total']) or 0.0,
                    'ImpTotConc': f['imp_tot_conc'] and float(f['imp_tot_conc']) or 0.0,
                    'ImpNeto': f['imp_neto'] and float(f['imp_neto']) or 0.0,
                    'ImpOpEx': f['imp_op_ex'] and float(f['imp_op_ex']) or 0.0,
                    'ImpTrib': f['imp_trib'] and float(f['imp_trib']) or 0.0,
                    'ImpIVA': f['imp_iva'] and float(f['imp_iva']) or 0.0,
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f.get('fecha_venc_pago'),
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f['fecha_venc_pago'],
                    'MonId': f['moneda_id'],
                    'MonCotiz': float(f['moneda_ctz']),
                    'CbtesAsoc': [
                        {'CbteAsoc': {
                            'Tipo': cbte_asoc['tipo'],
                            'PtoVta': cbte_asoc['pto_vta'],
                            'Nro': cbte_asoc['nro']}}
                        for cbte_asoc in f['cbtes_asoc']],
                    'Tributos': [
                        {'Tributo': {
                            'Id': tributo['tributo_id'],
                            'Desc': tributo['desc'],
                            'BaseImp': float(tributo['base_imp']),
                            'Alic': float(tributo['alic']),
                            'Importe': float(tributo['importe']),
                        }}
                        for tributo in f['tributos']],
                    'Iva': [
                        {'AlicIva': {
                            'Id': iva['iva_id'],
                            'BaseImp': float(iva['base_imp']),
                            'Importe': float(iva['importe']),
                        }}
                        for iva in f['iva']],
                }
                verifica(verificaciones, resultget.copy(), difs)
                if difs:
                    print("Diferencias:", difs)
                    self.log("Diferencias: %s" % difs)
            self.FechaCbte = resultget['CbteFch']  # .strftime("%Y/%m/%d")
            self.CbteNro = resultget['CbteHasta']  # 1L
            self.PuntoVenta = resultget['PtoVta']  # 4000
            self.Vencimiento = resultget['FchVto']  # .strftime("%Y/%m/%d")
            self.ImpTotal = str(resultget['ImpTotal'])
            cod_aut = resultget['CodAutorizacion'] and str(resultget['CodAutorizacion']) or ''  # 60423794871430L
            self.Resultado = resultget['Resultado']
            self.CbtDesde = resultget['CbteDesde']
            self.CbtHasta = resultget['CbteHasta']
            self.ImpTotal = resultget['ImpTotal']
            self.ImpNeto = resultget['ImpNeto']
            self.ImptoLiq = self.ImpIVA = resultget['ImpIVA']
            self.ImpOpEx = resultget['ImpOpEx']
            self.ImpTrib = resultget['ImpTrib']
            self.EmisionTipo = resultget['EmisionTipo']
            if self.EmisionTipo == 'CAE':
                self.CAE = cod_aut
            elif self.EmisionTipo == 'CAEA':
                self.CAEA = cod_aut

        self.__analizar_errores(result)
        if not difs:
            return self.CAE or self.CAEA
        else:
            return ''

    @inicializar_y_capturar_excepciones
    def CAESolicitarLote(self):
        f = self.factura
        ret = self.client.FECAESolicitar(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            FeCAEReq={
                'FeCabReq': {'CantReg': 250,
                             'PtoVta': f['punto_vta'],
                             'CbteTipo': f['tipo_cbte']},
                'FeDetReq': [{'FECAEDetRequest': {
                    'Concepto': f['concepto'],
                    'DocTipo': f['tipo_doc'],
                    'DocNro': f['nro_doc'],
                    'CbteDesde': f['cbt_desde'] + k,
                    'CbteHasta': f['cbt_hasta'] + k,
                    'CbteFch': f['fecha_cbte'],
                    'ImpTotal': f['imp_total'],
                    'ImpTotConc': f['imp_tot_conc'],
                    'ImpNeto': f['imp_neto'],
                    'ImpOpEx': f['imp_op_ex'],
                    'ImpTrib': f['imp_trib'],
                    'ImpIVA': f['imp_iva'],
                    # Fechas solo se informan si Concepto in (2,3)
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f.get('fecha_venc_pago'),
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f['fecha_venc_pago'],
                    'MonId': f['moneda_id'],
                    'MonCotiz': f['moneda_ctz'],
                    'CbtesAsoc': [
                        {'CbteAsoc': {
                            'Tipo': cbte_asoc['tipo'],
                            'PtoVta': cbte_asoc['pto_vta'],
                            'Nro': cbte_asoc['nro']}}
                        for cbte_asoc in f['cbtes_asoc']],
                    'Tributos': [
                        {'Tributo': {
                            'Id': tributo['tributo_id'],
                            'Desc': tributo['desc'],
                            'BaseImp': tributo['base_imp'],
                            'Alic': tributo['alic'],
                            'Importe': tributo['importe'],
                        }}
                        for tributo in f['tributos']],
                    'Iva': [
                        {'AlicIva': {
                            'Id': iva['iva_id'],
                            'BaseImp': iva['base_imp'],
                            'Importe': iva['importe'],
                        }}
                        for iva in f['iva']],
                    'Opcionales': [
                                      {'Opcional': {
                                          'Id': opcional['opcional_id'],
                                          'Valor': opcional['valor'],
                                      }} for opcional in f['opcionales']] or None,
                }
                } for k in range(250)]
            })

        result = ret['FECAESolicitarResult']
        if 'FeCabResp' in result:
            fecabresp = result['FeCabResp']
            fedetresp = result['FeDetResp'][0]['FECAEDetResponse']

            # Reprocesar en caso de error (recuperar CAE emitido anteriormente)
            if self.Reprocesar and 'Errors' in result:
                for error in result['Errors']:
                    err_code = str(error['Err']['Code'])
                    if fedetresp['Resultado'] == 'R' and err_code == '10016':
                        cae = self.CompConsultar(f['tipo_cbte'], f['punto_vta'], f['cbt_desde'], reproceso=True)
                        if cae and self.EmisionTipo == 'CAEA':
                            self.Reproceso = 'S'
                            return cae
                        self.Reproceso = 'N'

            self.Resultado = fecabresp['Resultado']
            # Obs:
            for obs in fedetresp.get('Observaciones', []):
                self.Observaciones.append("%(Code)s: %(Msg)s" % (obs['Obs']))
            self.Obs = '\n'.join(self.Observaciones)
            self.CAE = fedetresp['CAE'] and str(fedetresp['CAE']) or ""
            self.EmisionTipo = 'CAE'
            self.Vencimiento = fedetresp['CAEFchVto']
            self.FechaCbte = fedetresp['CbteFch']  # .strftime("%Y/%m/%d")
            self.CbteNro = fedetresp['CbteHasta']  # 1L
            self.PuntoVenta = fecabresp['PtoVta']  # 4000
            self.CbtDesde = fedetresp['CbteDesde']
            self.CbtHasta = fedetresp['CbteHasta']
            self.__analizar_errores(result)
        return self.CAE

    @inicializar_y_capturar_excepciones
    def CAEASolicitar(self, periodo, orden):
        ret = self.client.FECAEASolicitar(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            Periodo=periodo,
            Orden=orden,
        )

        result = ret['FECAEASolicitarResult']
        self.__analizar_errores(result)

        if 'ResultGet' in result:
            result = result['ResultGet']
            if 'CAEA' in result:
                self.CAEA = result['CAEA']
                self.Periodo = result['Periodo']
                self.Orden = result['Orden']
                self.FchVigDesde = result['FchVigDesde']
                self.FchVigHasta = result['FchVigHasta']
                self.FchTopeInf = result['FchTopeInf']
                self.FchProceso = result['FchProceso']

        return self.CAEA and str(self.CAEA) or ''

    @inicializar_y_capturar_excepciones
    def CAEAConsultar(self, periodo, orden):
        "Método de consulta de CAEA"
        ret = self.client.FECAEAConsultar(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            Periodo=periodo,
            Orden=orden,
        )

        result = ret['FECAEAConsultarResult']
        self.__analizar_errores(result)

        if 'ResultGet' in result:
            result = result['ResultGet']
            if 'CAEA' in result:
                self.CAEA = result['CAEA']
                self.Periodo = result['Periodo']
                self.Orden = result['Orden']
                self.FchVigDesde = result['FchVigDesde']
                self.FchVigHasta = result['FchVigHasta']
                self.FchTopeInf = result['FchTopeInf']
                self.FchProceso = result['FchProceso']

        return self.CAEA and str(self.CAEA) or ''

    @inicializar_y_capturar_excepciones
    def CAEARegInformativo(self):
        "Método para informar comprobantes emitidos con CAEA"
        f = self.factura
        ret = self.client.FECAEARegInformativo(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            FeCAEARegInfReq={
                'FeCabReq': {'CantReg': 1,
                             'PtoVta': f['punto_vta'],
                             'CbteTipo': f['tipo_cbte']},
                'FeDetReq': [{'FECAEADetRequest': {
                    'Concepto': f['concepto'],
                    'DocTipo': f['tipo_doc'],
                    'DocNro': f['nro_doc'],
                    'CbteDesde': f['cbt_desde'],
                    'CbteHasta': f['cbt_hasta'],
                    'CbteFch': f['fecha_cbte'],
                    'ImpTotal': f['imp_total'],
                    'ImpTotConc': f['imp_tot_conc'],
                    'ImpNeto': f['imp_neto'],
                    'ImpOpEx': f['imp_op_ex'],
                    'ImpTrib': f['imp_trib'],
                    'ImpIVA': f['imp_iva'],
                    # Fechas solo se informan si Concepto in (2,3)
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f.get('fecha_venc_pago'),
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f['fecha_venc_pago'],
                    'MonId': f['moneda_id'],
                    'MonCotiz': f['moneda_ctz'],
                    'CbtesAsoc': [
                        {'CbteAsoc': {
                            'Tipo': cbte_asoc['tipo'],
                            'PtoVta': cbte_asoc['pto_vta'],
                            'Nro': cbte_asoc['nro']}}
                        for cbte_asoc in f['cbtes_asoc']]
                    if f['cbtes_asoc'] else None,
                    'Tributos': [
                        {'Tributo': {
                            'Id': tributo['tributo_id'],
                            'Desc': tributo['desc'],
                            'BaseImp': tributo['base_imp'],
                            'Alic': tributo['alic'],
                            'Importe': tributo['importe'],
                        }}
                        for tributo in f['tributos']]
                    if f['tributos'] else None,
                    'Iva': [
                        {'AlicIva': {
                            'Id': iva['iva_id'],
                            'BaseImp': iva['base_imp'],
                            'Importe': iva['importe'],
                        }}
                        for iva in f['iva']]
                    if f['iva'] else None,
                    'CAEA': f['caea'],
                }
                }]
            })

        result = ret['FECAEARegInformativoResult']
        if 'FeCabResp' in result:
            fecabresp = result['FeCabResp']
            fedetresp = result['FeDetResp'][0]['FECAEADetResponse']

            # Reprocesar en caso de error (recuperar CAE emitido anteriormente)
            if self.Reprocesar and 'Errors' in result:
                for error in result['Errors']:
                    err_code = str(error['Err']['Code'])
                    if fedetresp['Resultado'] == 'R' and err_code == '703':
                        caea = self.CompConsultar(f['tipo_cbte'], f['punto_vta'], f['cbt_desde'], reproceso=True)
                        if caea and self.EmisionTipo == 'CAE':
                            self.Reproceso = 'S'
                            return caea
                        self.Reproceso = 'N'

            self.Resultado = fecabresp['Resultado']
            # Obs:
            for obs in fedetresp.get('Observaciones', []):
                self.Observaciones.append("%(Code)s: %(Msg)s" % (obs['Obs']))
            self.Obs = '\n'.join(self.Observaciones)
            self.CAEA = fedetresp['CAEA'] and str(fedetresp['CAEA']) or ""
            self.EmisionTipo = 'CAEA'
            self.FechaCbte = fedetresp['CbteFch']  # .strftime("%Y/%m/%d")
            self.CbteNro = fedetresp['CbteHasta']  # 1L
            self.PuntoVenta = fecabresp['PtoVta']  # 4000
            self.CbtDesde = fedetresp['CbteDesde']
            self.CbtHasta = fedetresp['CbteHasta']
            self.__analizar_errores(result)
        return self.CAEA

    @inicializar_y_capturar_excepciones
    def CAEASinMovimientoInformar(self, punto_vta, caea):
        "Método  para informar CAEA sin movimiento"
        ret = self.client.FECAEASinMovimientoInformar(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            PtoVta=punto_vta,
            CAEA=caea,
        )

        result = ret['FECAEASinMovimientoInformarResult']
        self.__analizar_errores(result)

        if 'CAEA' in result:
            self.CAEA = result['CAEA']
        if 'FchProceso' in result:
            self.FchProceso = result['FchProceso']
        if 'Resultado' in result:
            self.Resultado = result['Resultado']
            self.PuntoVenta = result['PtoVta']  # 4000

        return self.Resultado or ''

    @inicializar_y_capturar_excepciones
    def ParamGetTiposCbte(self, sep="|"):
        "Recuperador de valores referenciales de códigos de Tipos de Comprobantes"
        ret = self.client.FEParamGetTiposCbte(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
        )
        res = ret['FEParamGetTiposCbteResult']
        return [("%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p['CbteTipo']).replace("\t", sep)
                for p in res['ResultGet']]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposConcepto(self, sep="|"):
        "Recuperador de valores referenciales de códigos de Tipos de Conceptos"
        ret = self.client.FEParamGetTiposConcepto(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
        )
        res = ret['FEParamGetTiposConceptoResult']
        return [("%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p['ConceptoTipo']).replace("\t", sep)
                for p in res['ResultGet']]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposDoc(self, sep="|"):
        "Recuperador de valores referenciales de códigos de Tipos de Documentos"
        ret = self.client.FEParamGetTiposDoc(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
        )
        res = ret['FEParamGetTiposDocResult']
        return [("%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p['DocTipo']).replace("\t", sep)
                for p in res['ResultGet']]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposIva(self, sep="|"):
        "Recuperador de valores referenciales de códigos de Tipos de Alícuotas"
        ret = self.client.FEParamGetTiposIva(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
        )
        res = ret['FEParamGetTiposIvaResult']
        return [("%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p['IvaTipo']).replace("\t", sep)
                for p in res['ResultGet']]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposMonedas(self, sep="|"):
        "Recuperador de valores referenciales de códigos de Monedas"
        ret = self.client.FEParamGetTiposMonedas(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
        )
        res = ret['FEParamGetTiposMonedasResult']
        return [("%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p['Moneda']).replace("\t", sep)
                for p in res['ResultGet']]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposOpcional(self, sep="|"):
        "Recuperador de valores referenciales de códigos de Tipos de datos opcionales"
        ret = self.client.FEParamGetTiposOpcional(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
        )
        res = ret['FEParamGetTiposOpcionalResult']
        return [("%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p['OpcionalTipo']).replace("\t", sep)
                for p in res.get('ResultGet', [])]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposTributos(self, sep="|"):
        "Recuperador de valores referenciales de códigos de Tipos de Tributos"
        "Este método permite consultar los tipos de tributos habilitados en este WS"
        ret = self.client.FEParamGetTiposTributos(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
        )
        res = ret['FEParamGetTiposTributosResult']
        return [("%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p['TributoTipo']).replace("\t", sep)
                for p in res['ResultGet']]

    @inicializar_y_capturar_excepciones
    def ParamGetCotizacion(self, moneda_id):
        "Recuperador de cotización de moneda"
        ret = self.client.FEParamGetCotizacion(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            MonId=moneda_id,
        )
        self.__analizar_errores(ret)
        res = ret['FEParamGetCotizacionResult']['ResultGet']
        return str(res.get('MonCotiz', ""))

    @inicializar_y_capturar_excepciones
    def ParamGetPtosVenta(self, sep="|"):
        "Recuperador de valores referenciales Puntos de Venta registrados"
        ret = self.client.FEParamGetPtosVenta(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
        )
        res = ret.get('FEParamGetPtosVentaResult', {})
        return [("%(Nro)s\tEmisionTipo:%(EmisionTipo)s\tBloqueado:%(Bloqueado)s\tFchBaja:%(FchBaja)s" % p[
            'PtoVenta']).replace("\t", sep)
                for p in res.get('ResultGet', [])]
