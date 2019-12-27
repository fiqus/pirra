from afip.models import ErrorCustomAfip
import logging

# Utilidades de AFIP que pueden ayudar a resolver situaciones generales

logger = logging.getLogger(__name__)


def handler_errores_afip(ret, comprobante):
    result = {"display_errors": "", "display_obs": ""}
    try:
        if hasattr(ret, 'Errores') and len(ret.Errores):
            for error in ret.Errores:
                if error != '0: OK':
                    result["display_errors"] += get_display_error(error)
                    comprobante.errores_wsfe = result["display_errors"]
        if hasattr(ret, 'Observaciones') and len(ret.Observaciones):
            for obs in ret.Observaciones:
                if obs != '0: OK':
                    result["display_obs"] += get_display_error(obs)
                    comprobante.observaciones_wsfe = result["display_obs"]
        if len(result["display_errors"]) or len(result["display_obs"]):
            comprobante.save()
    except Exception as e:
        logger.error("Error al interpretar el error de afip para el comprobante.id {}".format(comprobante.id))
        logger.error(str(e))
    return result


def get_display_error(error):
    # error = 602: No existen datos en nuestros registros para los parametros ingresados
    # obs = 10015: El campo  DocNro es invalido.
    error_custom_afip = ErrorCustomAfip()
    try:
        error_data = error.split(":")
        codigo = error_data[0]
        error_custom = error_custom_afip.get_error(codigo)
        if error_custom and len(error_custom) > 1:
            # hay mas de un errror posible hay que verificar la regex
            for custom in error_custom:
                if custom['regex'] in error:
                    return custom['descripcion']
        elif error_custom and len(error_custom) > 0:
            return error_custom[0]['descripcion']
        else:
            logger.error("[ERROR_AFIP_NOT_FOUND] {}".format(error))
    except Exception as e:
        logger.error("[ERROR_AFIP_NOT_HANDLED] {}".format(error))
        logger.error(str(e))
    return "<br/>{}".format(error)


# todos los errores de conectividad que puedan surgir porque el servicio de afip no esta disponible
# se agrupan en un unico error con codigo 'conectividad' y en la regex se guardan fragmentos del texto
# de error que pueda venir de AFIP separados por ':' para poder parsearlos y saber si el mensaje recibido
# contiene alguno de estos fragmentos que indican que el error es de conectividad
def handler_error_conectividad_afip(str_error):
    error_custom_afip = ErrorCustomAfip()
    try:
        errores_conectividad = error_custom_afip.get_error(error_custom_afip.CONECTIVIDAD)
        if errores_conectividad and len(errores_conectividad):
            errores = errores_conectividad[0]['regex'].split(':')
            for error_regex in errores:
                if error_regex in str_error:
                    return errores_conectividad[0]['descripcion']
        else:
            logger.error("[ERROR_AFIP_NOT_FOUND] {} - {}".format(error_custom_afip.CONECTIVIDAD, str_error))
    except Exception as e:
        logger.error("[ERROR_AFIP_NOT_HANDLED] {}".format(str_error))
        logger.error(str(e))
    logger.error("[ERROR_AFIP_NOT_FOUND] {} - {}".format(error_custom_afip.CONECTIVIDAD, str_error))
    return str_error
