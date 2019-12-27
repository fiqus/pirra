$(document).ready(function () {
    $("#importar-ptos-vta-afip").click(importar_ptos_vta_afip);
});

function importar_ptos_vta_afip() {
    $.get($("#importar-ptos-vta-afip").data("url")).always(function (data) {
        var dialog = bootbox.dialog({
            message: data,
            title: "Importar Puntos de Venta desde el servicio web de la AFIP",
            buttons: {
                success: {
                    label: "Importar",
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
        dialog.find("#importar-ptos-vta-afip-form").on('submit', function(){
            $(this).closest('.modal-dialog').find('.btn-success').attr('disabled', 'disabled');
        });
    });
}