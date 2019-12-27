$(document).ready(function () {
    $("#modificar-precios").click(modificar_precios);


    $("#importar").click(function () {
        var url = $(this).attr('href');
        var iframeSuccess = false;
        var import_dialog = bootbox.dialog({
            message: '<iframe id="import_iframe" style="opacity:0;" src="' + url + '" frameborder="0"></iframe>',
            title: "Importar Productos",
            size: "large",
            className: "importar-producto",
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

function modificar_precios() {
    $.get($("#modificar-precios").data("url")).always(function (data) {
        var dialog = bootbox.dialog({
            message: data,
            title: "Actualizar Precios en Forma Masiva",
            buttons: {
                success: {
                    label: "Modificar",
                    className: "btn-success",
                    callback: function () {
                        $(this).find('.btn-success').attr('disabled', 'disabled');
                        $(this).find('form').submit();
                    }
                },
                close: {
                    label: "Cerrar",
                    className: "btn-default"
                }
            }
        });
        dialog.find("#modificar-precios-form").validate({
            rules: {
                porcentaje: {
                    required: true
                }
            }
        });
        dialog.find("#modificar-precios-form").on('submit', function(){
            $(this).closest('.modal-dialog').find('.btn-success').attr('disabled', 'disabled');
        });

        // tunneo la pantallita por js
        var porcentajeContainerEl = $('#id_porcentaje').closest('div');
        porcentajeContainerEl.find('label').remove();
        porcentajeContainerEl.addClass('input-group col-xs-6 col-md-6 pull-left id_porcentaje_container');
        porcentajeContainerEl.append('<div class="input-group-append"><span class="input-group-text">%</span></div>');
        // $('#id_incrementar .radio').removeClass('radio').addClass('radio-inline');
    });
}