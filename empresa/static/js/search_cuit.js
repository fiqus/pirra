$(function(){
    $(".btn-search-cuit").click(function(){
        var text = $("#id_nro_doc").val();
        text = text.replace(/-/g, '');

        $.getJSON('/afip/cuit_details/' + text, function(data){
            $("#id_nombre").val(data["denominacion"]);
            $("#id_condicion_iva").val(data["condicion_iva"]);
            toastr['success']('Se encontro el nro de documento. Se cargaron los datos pertenecientes a ' +
                data["denominacion"] +
                "<br>Si lo desea puede modificar la razon social.");
        }).fail(function(){
            $("#id_nombre").val("");
            $("#id_condicion_iva").val("");
            toastr['error']('No se encontro el nro de documento ' +
                text +
                '<br>Si esta seguro que el nro de documento es valido puede utilizarlo igualmente.');
        });
    })
});