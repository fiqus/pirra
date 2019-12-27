$(document).ready(function () {
    var $precio_final = $("#id_precio_final");
    var $precio_unit = $("#id_precio_unit");
    var $ingresa_final = $("#id_ingresa_precio_final");
    var unit = parseFloat($precio_unit.val().replace(",", "."));
    var $lbl_precio_final = $("label[for='id_precio_final']");
    var $lbl_precio_unit = $("label[for='id_precio_unit']");

    function calculate_precio_unitario() {
        var precio_final = parseFloat($precio_final.val().replace(",", "."));

        if($ingresa_final.prop('checked') && precio_final > 0) {
            var porc = $("#id_alicuota_iva option:selected").data('porc');
            if (porc === "") {
                porc = "0";
            }
            porc = parseFloat(porc.replace(",", "."));
            var unit = precio_final / (1 + (porc / 100));
            $precio_unit.val(unit.toFixed(4));
        }
    }

    function calculate_precio_final(unit) {
        var porc = $("#id_alicuota_iva option:selected").data('porc');
        if (porc === "") {
            porc = "0";
        }
        porc = parseFloat(porc.replace(",", "."));
        var final = unit * (1 + (porc / 100));
        $precio_final.val(final.toFixed(4));
    }

    function showPrecioFinal () {
        $precio_final.toggle();
        $lbl_precio_final.toggle();
        $precio_unit.toggle();
        $lbl_precio_unit.toggle();
    }

    $precio_final.hide();
    $lbl_precio_final.hide();

    if(unit > 0) {
        calculate_precio_final(unit);

        if ($ingresa_final.prop('checked')) {
            showPrecioFinal();
        }
    }

    $ingresa_final.change(function(){
        showPrecioFinal();
        calculate_precio_unitario();
    });

    $precio_final.change(function(){
        calculate_precio_unitario();
    });

    $precio_unit.change(function(){
        calculate_precio_final($(this).val());
    });

    $("#id_alicuota_iva").change(function(){
        var unit = parseFloat($precio_unit.val().replace(",", "."));

        if($ingresa_final.prop('checked')) {
            calculate_precio_unitario();
        } else {
            if(unit > 0) {
                calculate_precio_final(unit);
            }
        }
    });
});