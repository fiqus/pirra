#!/usr/bin/python
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""Módulo para obtener un ticket de autorización del web service WSAA de AFIP
Basado en wsaa-client.php de Gerardo Fisanotti - DvSHyS/DiOPIN/AFIP - 13-apr-07
Definir WSDL, CERT, PRIVATEKEY, PASSPHRASE, SERVICE, WSAAURL
Devuelve TA.xml (ticket de autorización de WSAA)
"""

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2008 Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "1.0"

import email,os,sys
from .utils import date
from .soap import SimpleXMLElement, SoapClient, SoapFault, parse_proxy
from M2Crypto import BIO, Rand, SMIME, SSL

# Constantes (si se usa el script de linea de comandos)
WSDL = "wsaa.wsdl"      # El WSDL correspondiente al WSAA (no se usa)
CERT = "homo.crt"        # El certificado X.509 obtenido de Seg. Inf.
PRIVATEKEY = "homo.key"  # La clave privada del certificado CERT
PASSPHRASE = "xxxxxxx"  # La contraseña para firmar (si hay)
SERVICE = "wsfe"        # El nombre del web service al que se le pide el TA

# WSAAURL: la URL para acceder al WSAA, verificar http/https y wsaa/wsaahomo
#WSAAURL = "https://wsaa.afip.gov.ar/ws/services/LoginCms" # PRODUCCION!!!
WSAAURL = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms" # homologacion (pruebas)
SOAP_ACTION = 'http://ar.gov.afip.dif.facturaelectronica/' # Revisar WSDL
SOAP_NS = "http://ar.gov.afip.dif.facturaelectronica/"     # Revisar WSDL 

# Verificación del web server remoto (opcional?) igual no se usa
REMCN = "wsaahomo.afip.gov.ar" # WSAA homologacion CN (CommonName)
REMCACERT = "AFIPcerthomo.crt" # WSAA homologacion CA Cert

# No debería ser necesario modificar nada despues de esta linea

def create_tra(service=SERVICE):
    "Crear un Ticket de Requerimiento de Acceso (TRA)"
    tra = SimpleXMLElement(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<loginTicketRequest version="1.0">'
        '</loginTicketRequest>')
    tra.addChild('header')
    # El source es opcional. Si falta, toma la firma (recomendado).
    #tra.header.addChild('source','subject=...')
    #tra.header.addChild('destination','cn=wsaahomo,o=afip,c=ar,serialNumber=CUIT 33693450239')
    tra.header.addChild('uniqueId', date('U'))
    tra.header.addChild('generationTime', date('c', date('U')-24000))
    tra.header.addChild('expirationTime', date('c', date('U')+24000))
    tra.addChild('service', service)
    return tra.asXML()


def sign_tra(tra,cert=CERT,key=PRIVATEKEY):
    from M2Crypto import BIO, Rand, SMIME

    def makebuf(text):
        return BIO.MemoryBuffer(text)

    # Make a MemoryBuffer of the message.
    buf = makebuf(tra.encode())

    # Seed the PRNG.
    Rand.load_file('randpool.dat', -1)

    # Instantiate an SMIME object; set it up; sign the buffer.
    s = SMIME.SMIME()
    s.load_key(key, cert)
    p7 = s.sign(buf)

    out = BIO.MemoryBuffer()
    s.write(out, p7)

    msg = email.message_from_bytes(out.read())
    for part in msg.walk():
        filename = part.get_filename()
        if filename == "smime.p7m":                 # es la parte firmada?
            return part.get_payload(decode=False)   # devolver CMS


def call_wsaa(cms, location = WSAAURL, proxy=None):
    "Llamar web service con CMS para obtener ticket de autorización (TA)"
  
    # cliente soap del web service
    client = SoapClient(location = location , 
        action = SOAP_ACTION,
        namespace = SOAP_NS,
        cert = REMCACERT,  # certificado remoto (revisar)
        trace = False,     # imprimir mensajes de depuración
        exceptions = True, # lanzar Fallas Soap
        proxy = proxy,      # datos del servidor proxy (opcional)
        )
        

    results = client.loginCms(in0=cms)
    return str(results.loginCmsReturn)
