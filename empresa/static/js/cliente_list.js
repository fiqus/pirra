$(document).ready(function () {
    $('[data-toggle="tooltip"]').tooltip();

    var detalles = $('tbody tr');
    var boton;
    for (var i=0; i < detalles.length; i++){
        console.log(detalles[i]);
        var el = $(detalles[i]);
        boton = el.find('.btn-danger');
        if(el.find('.true').length){
            boton.text('Desactivar').addClass('activar-desactivar-button');
        }else{
            boton.removeClass('btn-danger').addClass('btn-success').text('Activar').addClass('activar-desactivar-button');
        }
    }

    $("#importar").click(function () {
        var url = $(this).attr('href');
        var iframeSuccess = false;
        var import_dialog = bootbox.dialog({
            message: '<iframe id="import_iframe" style="opacity:0;" src="' + url + '" frameborder="0"></iframe>',
            title: "Importar Clientes",
            size: "large",
            className: "importar-cliente",
            buttons: {
                success: {
                    label: "Importar",
                    className: "btn-success",
                    callback: function () {
                        var iframe = document.getElementById("import_iframe");
                        var iframedoc = (iframe.contentWindow || iframe.contentDocument);
                        var _this = this;
                        if (iframedoc.document) {
                            iframedoc = iframedoc.document;
                            iframedoc.getElementsByTagName("form")[0].submit();
                            $(this).find(".btn").prop('disabled', true);

                            iframe.onload = function () {
                                if ($(this.contentDocument).find("form").length) {
                                    $(_this).find(".btn").prop('disabled', false);
                                } else {
                                    $(_this).find(".btn").prop('disabled', false);
                                    $(_this).find(".btn-success").hide();
                                    iframeSuccess = true;
                                }
                            };
                        }
                        return false;
                    }
                },
                close: {
                    label: "Cerrar",
                    className: "btn-default",
                    callback: function () {
                        if (iframeSuccess) {
                            location.reload();
                            return false;
                        }
                    }
                }
            }
        });
        // bloqueo pantalla hasta que esté todo cargado
        $('#import_iframe').ready(function(){
            $('#import_iframe').css('opacity',1);
        });
        return false;
    });
});