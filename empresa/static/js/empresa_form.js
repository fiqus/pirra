$(document).ready(function () {
    //TODO pasar la comparación segun las pks del model
    function setValidations($el) {
        var value = $el.find("option:selected").text().toLowerCase();
        var $nro_iibb = $('#id_nro_iibb');
        if(value === "exento") {
            $nro_iibb.rules( "add", {
                required: false
            });
        } else {
            $nro_iibb.rules("add", {
                required: true
            });
        }
    }

    $('.mandarCopiaOrigenInput').closest('.form-group').prepend('<label class="control-label" id="configuracionFacturas">Configuración de Envíos</label>');
    $('.imprimirDuplicadoYTriplicadoInput').closest('.form-group').prepend('<label class="control-label" id="configuracionImpresionFacturas">Configuración de Impresión</label>');

    $('#id_utiliza_edi').closest('.form-group').prepend('<label class="control-label" id="utiliza_edi">EDI (Intercambio Electrónico de Datos)</label>');

    $('#id_email').rules("add", {
        required: true,
        messages: {
          required: "El mail de la empresa es necesario."
        }
    });
    $('#id_condicion_iva').rules("add", { required: true });
    var $cond_iibb = $('#id_condicion_iibb');
    setValidations($cond_iibb);
    $cond_iibb.change(function(){
        setValidations($(this));
    });

    $('input[name="fecha_serv_desde"], input[name="fecha_serv_hasta"]').datepicker({language: "es", format: "dd/mm/yyyy"});
});