$(document).ready(function () {
    $.validator.addMethod("validCUIT", validCUIT, 'CUIT Inválido');
    $.validator.addMethod("validCUIL", validCUIT, 'CUIL Inválido');
    $.validator.addMethod("validDNI", function(value, element) {
      return value.trim().length === 8;
    }, "Ingrese un DNI válido de 8 cifras");

    var formatterInstance;

    //TODO pasar la comparación segun los id_afip del model
    function setValidations(el) {
        var value = $(el).find("option:selected").text().toLowerCase();
        var nroDoc = $("#id_nro_doc");
        nroDoc.rules('remove');
        formatterInstance = nroDoc.mask('9999999999999999999999');
        if(value === 'cuit') {
            nroDoc.rules( "add", {
                validCUIT: true,
                required: true,
            });
            formatterInstance.mask('99-99999999-9');
        }
        if(value === 'cuil') {
            nroDoc.rules("add", {
                validCUIL: true,
                required: true,
            });
            formatterInstance.mask('99-99999999-9');
        }
        if(value === 'dni') {
            nroDoc.rules("add", {
                required: true,
                validDNI: true,
            });
            formatterInstance.mask('99999999');
        }
        if(value === 'cdi' || value === 'otro') {
            formatterInstance.mask('999999999999999999');
        }
        if(value === 'otro') {
            nroDoc.rules( "add", {
                validCUIT: false,
                validDNI: false,
                required: false,
            });
            formatterInstance.mask('99999999');
        }
    }

    // aplico por js estilos porque cuando aparece label de validation hace subir al input
    $('.btn-search-cuit').parent().attr('style','vertical-align: top;');

    $('#id_activo, #id_fecha_baja, #id_usuario_baja').parent().hide();
    if(!$('#id_activo').attr('checked')){
        $('#id_activo').parent().show();
    }

    setValidations($('#id_tipo_doc'));
    $('.btn-search-cuit').attr('disabled','disabled');
    $('#id_tipo_doc').change(function(){
        setValidations(this);
        var value = $(this).find("option:selected").text().toLowerCase();
        if(value === 'cuit'){
            $('.btn-search-cuit').removeAttr('disabled');
        }else{
            $('.btn-search-cuit').attr('disabled','disabled');
        }
    });

    $("#id_agente_edi").hide();
    $("label[for='id_agente_edi']").hide();
});