$(function () {
    $('#id_remito_nro').mask('9999-99999999');

    $('form#comprobante_add').submit(function () {
        var $el;
        $("select[id$=-producto]").each(function (n, el) {
            $el = $(el);
            if (parseInt($el.val(), 10) < 0) {
                $el.val("");
            }
        });
    });

    var selectifyproducto = function (sel, empty) {
        var $sel = $(sel);
        var i = 1;
        $sel.selectize({
            plugins: ['modify_textbox_value'],
            createOnBlur: true,
            selectOnTab: true,
            persist: false,
            create: function (input) {
                return {value: -1, text: input};
            },
            onChange: function (value) {
                var id = parseInt(value, 10);
                if (id) {
                    item = this.options[value];
                    var $tr = $($sel.parents("tr"));
                    if (id >= 0) {
                        $tr.find("input[id$=precio_unit]").val(productos[id].precio_unit);
                        $tr.find("select[id$=unidad]").val(productos[id].unidad);
                        $tr.find("select[id$=alicuota_iva]").val(productos[id].alicuota_iva);
                    }
                    // fix para que funcione selectize en IE
                    if (isNaN(item.text) || item.text == "") {
                        $sel.parent().siblings("input:hidden").val(this.getItem(value).text());
                    } else {
                        $sel.parent().siblings("input:hidden").val(item.text);
                    }
                    recalculate(true);
                }
            },
            render: {
                'option_create': function (data, escape) {
                    return '<div class="create">Utilizar <strong>' + escape(data.input) + '</strong>&hellip;</div>';
                }
            }
        });

        var detalle = $($sel.parent().siblings("input:hidden"));
        if (detalle.val() && !$sel.val()) {
            var selectize = $sel[0].selectize;
            selectize.addOption({value: "-1", text: detalle.val()});
            selectize.setValue("-1");
        }
    };

    // No permitir editar los opcionales desde el form. Solo se cambian desde la conf de empresa
    $('#opcional_table select').attr('disabled', 'disabled');

    $('#comprobante_add').validate({
        ignore: ":hidden:not(.desc_detalle)",
        errorPlacement: function (error, element) {
            $(element).parent().append(error); //fix to append after select 2
        },
        highlight: function (element, errorClass, validClass) {
            var elem = $(element);
            if (elem.hasClass("desc_detalle")) {//fix to add border color to select2
                $(element).parent().find('.selectize-control').addClass(errorClass);
            } else if (elem.parent().hasClass("selectize-input")) {
                $(element).parent().parent().addClass(errorClass);
            } else {
                elem.addClass(errorClass);
            }
        },
        unhighlight: function (element, errorClass, validClass) {
            var elem = $(element);
            if (elem.hasClass("desc_detalle")) { //fix to remove color to select2
                $(element).parent().find('.selectize-control').removeClass(errorClass);
            } else {
                elem.removeClass(errorClass);
            }
        }
    });

    $("#id_cliente").selectize({
        placeholder: "Seleccione un Cliente o cree uno nuevo",
        createOnBlur: true
    });

    $("#id_cbte_asoc").selectize({
        createOnBlur: true
    });

    $.validator.addMethod("noComma", function (value, element) {
        return !value.match(/[,]/g);
    }, "Utilizar puntos, no comas.");

    var add_detalle_validations = function (tr, detalle_id) {
        var idDetalles = "#id_detalles-" + (detalle_id - 1);
        $(idDetalles + "-cant").rules("add", {
            required: true,
            min: 1,
            messages: {
                min: "Debe ser positivo"
            }
        });
        $(idDetalles + "-precio_unit").rules("add", {
            noComma: true
        });
        $(idDetalles + "-detalle").rules("add", {
            required: true
        });
    };

    var add_tributo_validations = function (tr, tributo_id) {
        var idTributos = "#id_tributos-" + (tributo_id - 1);
        $(idTributos + "-alicuota").rules("add", {
            required: true,
            noComma: false,
            min: 0,
            messages: {
                min: "No valido"
            }
        });
        $(idTributos + "-base_imponible").rules("add", {
            required: true,
            noComma: false,
            min: 0,
            messages: {
                min: "No valido"
            }
        });
        $(idTributos + "-detalle").rules("add", {
            required: true
        });
    };

    $("#id_fecha_emision").datepicker({language: "es", format: "dd/mm/yyyy"});
    $("#id_fecha_venc_pago").datepicker({language: "es", format: "dd/mm/yyyy"});
    $("#id_fecha_pago").datepicker({language: "es", format: "dd/mm/yyyy"});

    $('#id_fecha_emision').datepicker().on('changeDate', function (e) {
        $('#id_fecha_emision').datepicker('hide');
    });
    $('#id_fecha_venc_pago').datepicker().on('changeDate', function (e) {
        $('#id_fecha_venc_pago').datepicker('hide');
    });

    $('#id_fecha_pago').datepicker().on('changeDate', function (e) {
        $('#id_fecha_pago').datepicker('hide');
    });

    var detail_template = Handlebars.compile($("#detail-template").html());
    var tributo_template = Handlebars.compile($("#tributo-template").html());
    var last_detalle_id = $("#detalle_table tbody").children().length;
    var last_tributo_id = $("#tributo_table tbody").children().length;

    var on_detalle_remove_click = function (evt) {
        var tr_to_remove = $(evt.target).parents("tr");
        var del = tr_to_remove.find('input[id$="DELETE"]');
        if (del.length) {
            tr_to_remove.css("display", "none");
            del.prop('checked', true);
        } else {
            tr_to_remove.remove();
            last_detalle_id--;
            $("#id_detalles-TOTAL_FORMS").val(last_detalle_id);
        }
        recalculate();
    };

    var on_tributo_remove_click = function (evt) {
        var tr_to_remove = $(evt.target).parents("tr");
        var del = tr_to_remove.find('input[id$="DELETE"]');
        if (del.length) {
            tr_to_remove.css("display", "none");
            del.prop('checked', true);
        } else {
            tr_to_remove.remove();
            last_tributo_id--;
            $("#id_tributos-TOTAL_FORMS").val(last_tributo_id);
        }
        recalculate();
    };

    $("#btn_add_detail").click(function () {
        var tr = $(detail_template({"n": last_detalle_id++}));
        tr.find("td.unidad select").append($("#unidades_ocultas").html());
        tr.find("select[id$='alicuota_iva']").append($("#alicuotas_iva_ocultas").html());
        var s = $(tr.find(".producto select"));
        s.append("<option value=''></option>");
        $.each(productos, function (id, data) {
            var o = $("<option value='" + id + "'>" + data.nombre + "</option>")
            s.append(o);
        });

        $("#id_detalles-TOTAL_FORMS").val(last_detalle_id);
        $("#detalle_table tbody").append(tr);
        add_detalle_validations(tr, last_detalle_id);
        var idCbte = parseInt($('#id_tipo_cbte').val());
        setupPrecios(idCbte);
        filtrarAlicuotasIva(idCbte);
        selectifyproducto(tr.find(".producto select"), true);
    });

    if (!$("#detalle_table tbody").children().length) {
        $("#btn_add_detail").click();
    }

    $('#detalle_table').on('click', ".remove_btn", on_detalle_remove_click);
    $('#detalle_table').on('change', 'input[id$="cant"]', recalculateCallBack);
    $('#detalle_table').on('change', 'input[id$="precio_unit"]', recalculateCallBack);
    $('#detalle_table').on('change', 'input[id$="precio_final"]', recalculateCallBack);
    $('#detalle_table').on('change', 'select[id$="alicuota_iva"]', recalculateCallBack);

    $("#btn_add_tributo").click(function () {
        var tr = $(tributo_template({"n": last_tributo_id++}));
        $(tr).find("select.tributos").append($("#tributos_ocultos").html());
        $("#id_tributos-TOTAL_FORMS").val(last_tributo_id);
        $("#tributo_table tbody").append(tr);
        add_tributo_validations(tr, last_tributo_id);
    });

    $('#tributo_table').on('click', ".remove_btn", on_tributo_remove_click);
    $('#tributo_table').on('change', 'input[id$="base_imponible"]', recalculateCallBack);
    $('#tributo_table').on('change', 'input[id$="alicuota"]', recalculateCallBack);
    $('#tributo_table').on('change', 'select[id$="tributo"]', recalculateCallBack);

    function recalculateCallBack() {
        recalculate();
    }

    function setTitle(title) {
        $('#titulo-cbte').html(title);
    }

    function filtrarAlicuotasIva(idCbte) {
        var visibles = 0, line, tipo_cbtes;
        var lines = $("#detalle_table tbody tr");
        for (var i = 0; i < lines.length; i++) {
            line = $(lines[i]);

            // muestra las que son comprendidas por el tipo de cbte (idCbte)
            line.find("select[id$='alicuota_iva'] option").each(function () {
                tipo_cbtes = $(this).data("tipo_cbte").split(",");
                if ($.inArray(idCbte.toString(), tipo_cbtes) > -1) {
                    $(this).removeAttr("disabled");
                    $(this).show();
                } else {
                    $(this).attr("disabled", "disabled");
                    $(this).hide();
                }
            });

            // si tras el filtro no quedan alicuotas o queda una y es vacia o 0%
            if (line.find("select[id$='alicuota_iva'] option:not(:disabled)").length === 0 ||
                (line.find("select[id$='alicuota_iva'] option:not(:disabled)").length === 1 &&
                    (line.find("select[id$='alicuota_iva']>option:selected").val() === "" ||
                        line.find("select[id$='alicuota_iva']>option:selected").val() === "1"))) {
                visibles++;
            }
        }
        if (visibles === last_detalle_id) {
            ocultarAlicuotasIva();
        }
        recalculate();
    }

    function ocultarAlicuotasIva() {
        $(".alicuotas-iva").hide();
        $("#totales_alicuotas").hide();

        var lines = $("#detalle_table tbody tr");
        var line, defaultItem;
        for (var i = 0; i < lines.length; i++) {
            line = $(lines[i]);
            defaultItem = line.find("select[id$='alicuota_iva'] option[data-porc='0.0000']:first");
            if (!defaultItem.val()) {
                defaultItem = line.find("select[id$='alicuota_iva'] option[data-porc='0,0000']:first");
            }
            $(defaultItem).removeAttr("disabled");
            $(defaultItem).prop('selected', true);
        }
        recalculate();
    }

    function mostrarAlicuotasIva() {
        $(".alicuotas-iva").show();
        $("#totales_alicuotas").show();
        recalculate();
    }

    function ocultarPrecioFinal() {
        $(".precio-unitario").show();
        $(".precio-final").hide();
        $(".imp_iva").show();
        $(".subtotales").show();
    }

    function preciosComprobantesE() {
        ocultarAlicuotasIva();
        $(".precio-unitario").show();
        $(".precio-final").hide();
        $(".imp_iva").hide();
        $(".subtotales").hide();
    }

    function mostrarPrecioFinal() {
        $(".precio-final").show();
        $(".precio-unitario").hide();
        $(".imp_iva").hide();
        $(".subtotales").hide();
    }

    function ocultarDescuentos() {
        $('#id_descuento').val(0);
        $('.descuentos').hide();
    }

    function setupPrecios(idCbte) {
        if (esComprobanteE(idCbte)) {
            preciosComprobantesE();
            ocultarDescuentos();
        } else {
            $('.descuentos').show();
            var hayDescuento = parseFloat($('#id_descuento').val());
            if (!esComprobanteC(idCbte)) {
                mostrarAlicuotasIva();
            }

            if (!isNaN(hayDescuento) && hayDescuento) {
                $('#descuento-total-container').show();
                if (esComprobanteB(idCbte)) {
                    $('.subtotales').show();
                }
                if (esComprobanteC(idCbte)) {
                    $("#label_subtotal, #subtotal").hide();
                }
            } else {
                $('#descuento-total-container').hide();
                if (esComprobanteB(idCbte)) {
                    $('.subtotales').hide();
                }
                if (esComprobanteC(idCbte)) {
                    $("#label_subtotal, #subtotal").show();
                }
            }

            if (esComprobanteB(idCbte)) {
                mostrarPrecioFinal();
                $(".subtotales").show();
                $("#totales_alicuotas").hide();
            } else {
                ocultarPrecioFinal();
            }
        }
    }

    $('#id_tipo_cbte').change(function () {
        setTitle($(this).find(":selected").text());
        var idCbte = parseInt($(this).val());

        if (esComprobanteE(idCbte)) {
            $("#panel_exportacion").show();
            $("#observaciones-text").show();
            $("#id_condicion_venta").val("");
            $("#div-condicion-venta").hide();
            $("#div-forma-pago").show();
            $("#panel_tributos").hide();
            $(".subtotales").hide();
            if (noEsFacturaE(idCbte)) {
                $("#cbte_asoc_container").show();
                $("#id_fecha_pago").val("");
                $("#fecha_pago_container").hide();
            } else {
                $("#id_cbte_asoc").val("");
                $("#cbte_asoc_container").hide();
                $("#fecha_pago_container").show();
            }
        } else {
            $("#panel_exportacion").hide();
            $("#observaciones-text").hide();
            $("#div-condicion-venta").show();
            $("#div-forma-pago").hide();
            $("#id_forma_pago").val("");
            $("#panel_tributos").show();
            $(".subtotales").show();
            $("#id_cbte_asoc").val("");
            $("#cbte_asoc_container").hide();
            $("#id_fecha_pago").val("");
            $("#fecha_pago_container").hide();
        }
        setupPrecios(idCbte);
        filtrarAlicuotasIva(idCbte);
    });

    $('#id_tipo_cbte').change();

    setTitle($('#id_tipo_cbte').find(":selected").text());

    $("#panel_exportacion label").each(function (i) {
        if ($(this).parent().parent().hasClass("required")) {
            $(this).text($(this).text() + "*");
        }
    });

    $('#id_detalles-0-precio_unit').rules("add", {
        noComma: true,
        required: true
    });

    $('#cliente_link').click(function () {
        $("#modal_dialog").empty();
        $("#modal_dialog").load($(this).attr('data-ref'));
    });

    $('#agregar-cliente').click(function () {
        $("#modal_dialog").empty();
        $("#modal_dialog").load($(this).attr('data-ref'), function () {
            $("#modal_dialog").modal('show');
        });
    });

    var descuento_has_changed = function () {
        var descuento = parseFloat($('#id_descuento').val());
        if (!isNaN(descuento) && descuento > 0) {
            $('#descuento-total-container').show();
        } else {
            $('#descuento-total-container').hide();
        }
        recalculate();
    };

    $('#id_descuento').on('change', function () {
        descuento_has_changed();
    }).change();

    recalculate();

    $(".producto select").each(function (i, sel) {
        selectifyproducto(sel, false);
    });

    /* escondo los detalles que habian sido borrados, pero al guardar dio error */
    $('#detalle_table').each(function (index, el) {
        var inputDelete = $(el).find('input[id$="DELETE"]');
        if (inputDelete.is(':checked')) {
            inputDelete.parents('tr').css("display", "none");
        }
    });

    $("#link-preview_oc").click(function (e) {
        var url = $(e.target).data('url');
        preview_oc(url);
    });


});

function esComprobanteA(idCbte) {
    return (idCbte == factura_a_id || idCbte == nc_a_id || idCbte == nd_a_id /*|| idCbte == recibo_a_id*/);
}

function esComprobanteB(idCbte) {
    return (idCbte == factura_b_id || idCbte == nc_b_id || idCbte == nd_b_id || idCbte == recibo_b_id);
}

function esComprobanteC(idCbte) {
    return (idCbte == factura_c_id || idCbte == nc_c_id || idCbte == nd_c_id || idCbte == recibo_c_id);
}

function esComprobanteE(idCbte) {
    return (idCbte == factura_e_id || idCbte == nd_e_id || idCbte == nc_e_id);
}

function noEsFacturaE(idCbte) {
    return idCbte != factura_e_id
}

function esComprobanteM(idCbte) {
    return (idCbte == factura_m_id || idCbte == nc_m_id || idCbte == nd_m_id /*|| idCbte == recibo_a_id*/);
}

function recalculateIva(unitario, cant, subtotal, line, porc, comboAlicuotaIva, neto_gravado, total_alicuotas, total, calculateFinal) {
    unitario = parseFloat(unitario.replace(",", "."));
    cant = cant ? parseFloat(cant.replace(",", ".")) : 0;

    var imp_neto = cant * unitario;
    subtotal += imp_neto;
    var imp_iva = 0;

    if (line.find('select[id$="alicuota_iva"]:visible').length > 0) { //impuesto esta en la factura
        imp_iva = imp_neto * porc / 100;
        line.find('span[id$="imp_iva"]').text(imp_iva.toFixed(2));
        var alicuotaSelected = comboAlicuotaIva.val();

        var total_to_use = imp_iva;
        if (alicuotaSelected == exento_id || alicuotaSelected == no_gravado_id) {
            total_to_use = imp_neto;
        } else {
            neto_gravado += imp_neto;
        }

        if (total_alicuotas[alicuotaSelected] && total_alicuotas[alicuotaSelected].total) {
            total_alicuotas[alicuotaSelected].total += total_to_use;
        } else {
            total_alicuotas[alicuotaSelected] = {total: total_to_use};
        }
    }

    var precio_tot = imp_neto + imp_iva;
    if (!isNaN(precio_tot)) {
        total += precio_tot;
        line.find('span[id$="precio_total"]').html(precio_tot.toFixed(2));
        if (calculateFinal && cant > 0) {
            var precio_final = precio_tot / cant;
            line.find('input[id$="precio_final"]').val(precio_final.toFixed(2));
        }
    }

    return {
        subtotal: subtotal,
        neto_gravado: neto_gravado,
        total: total,
        total_alicuotas: total_alicuotas
    };
}

function recalculate(productChanged) {
    var tipo_cbte = parseInt($('#id_tipo_cbte').val());

    // calculo subtotal, neto_gravado, total, total_alicuotas en base a las lineas del comprobante
    var totales = recalculate_lines_amounts(tipo_cbte, productChanged);
    var total_tributos = get_total_tributos();
    var subtotal = set_subtotal_cbte(totales, tipo_cbte, total_tributos);
    var importe_dto = set_importe_descuento(subtotal);
    var total = subtotal - importe_dto;

    if (totales.neto_gravado) {
        var neto_gravado_con_dto = aplicar_descuento(totales.neto_gravado, subtotal);
        $("#neto_gravado").html(neto_gravado_con_dto.toFixed(2)).parent().show();
    }

    // Muestro y sumo las alicuotas al total
    $("span[id^=total_alicuotaiva_]").html("0.00").parent().hide();
    $.each(totales.total_alicuotas, function (alicuota_id, value) {
        if (esComprobanteA(tipo_cbte) || esComprobanteM(tipo_cbte)) {
            var alicuota_final = aplicar_descuento(value.total, subtotal);
            $("#total_alicuotaiva_" + alicuota_id).html(alicuota_final.toFixed(2)).parent().show();
            if (alicuota_id !== no_gravado_id && alicuota_id !== exento_id) {
                total += alicuota_final;
            }
        }
    });

    // Muestro y sumo los tributos al total
    $("span[id^=total_tributo_]").html("0.00").parent().hide();
    $.each(total_tributos, function (tributo, value) {
        total += value.total;
        $("#total_tributo_" + tributo).html((value.total).toFixed(2)).parent().show();
    });

    // Muestro totales
    $("#total").text(total.toFixed(2));
    $("#id_importe_total").val(parseFloat(total).toFixed(2));

    function aplicar_descuento(value, tot) {
        var porcentaje_dto = get_porcentaje_descuento();
        return value - (value * porcentaje_dto / 100);
    }

    function recalculate_total_alicuotas(comboAlicuotaIva, imp_iva, imp_final, neto_gravado, unit, total_alicuotas) {
        var alicuotaSelected = comboAlicuotaIva.val();

        var total_to_use = imp_iva;
        if (alicuotaSelected == exento_id || alicuotaSelected == no_gravado_id) {
            total_to_use = imp_final;
        } else {
            neto_gravado += unit;
        }

        if (total_alicuotas[alicuotaSelected] && total_alicuotas[alicuotaSelected].total) {
            total_alicuotas[alicuotaSelected].total += total_to_use;
        } else {
            total_alicuotas[alicuotaSelected] = {total: total_to_use};
        }
        return {neto_gravado: neto_gravado, total_alicuotas: total_alicuotas};
    }

    function recalculate_lines_amounts(idCbte, productChanged) {

        function get_porc_alicuota_iva(comboAlicuotaIva) {
            var porc = comboAlicuotaIva.data("porc");
            if (!porc) {
                porc = "0";
            }
            return parseFloat(porc.replace(",", "."));
        }

        var calculos;
        var total_alicuotas = {};
        var total = 0;
        var subtotal = 0;
        var neto_gravado = 0;
        var lines = $("#detalle_table tbody tr:visible");
        productChanged = (typeof productChanged === 'undefined') ? false : productChanged;

        for (var i = 0; i < lines.length; i++) {
            var line = $(lines[i]);
            var cant = line.find('input[id$="cant"]').val();
            var comboAlicuotaIva = line.find('select[id$="alicuota_iva"]>option:selected');
            var $unit = line.find('input[id$="precio_unit"]');
            var unitario = $unit.val();
            var porc = get_porc_alicuota_iva(comboAlicuotaIva);

            if (esComprobanteB(idCbte)) {
                var final = line.find('input[id$="precio_final"]').val();
                if (!isNaN(parseInt(final)) && !productChanged) {  // Si cargó precio final y no cambió el producto
                    final = parseFloat(final.replace(",", "."));
                    cant = parseFloat(cant.replace(",", "."));

                    var imp_final = cant * final;
                    var imp_iva = 0;
                    if (line.find('select[id$="alicuota_iva"]:visible').length > 0) { //impuesto esta en la factura
                        var unit = final / (1 + (porc / 100));
                        subtotal += unit * cant;
                        if (porc > 0) {
                            imp_iva = imp_final - unit * cant;
                        }

                        $unit.val(unit.toFixed(4));
                        line.find('span[id$="imp_iva"]').text(imp_iva.toFixed(2));
                        var ret = recalculate_total_alicuotas(comboAlicuotaIva, imp_iva, imp_final, neto_gravado, unit, total_alicuotas);
                        neto_gravado = ret.neto_gravado;
                        total_alicuotas = ret.total_alicuotas;
                    }
                    var precio_tot = imp_final;
                    if (!isNaN(precio_tot)) {
                        total += precio_tot;
                        line.find('span[id$="precio_total"]').html(precio_tot.toFixed(2));
                    }
                } else if (!isNaN(parseInt(unitario))) {
                    calculos = recalculateIva(unitario, cant, subtotal, line, porc, comboAlicuotaIva, neto_gravado, total_alicuotas, total, true);
                    subtotal = calculos.subtotal;
                    neto_gravado = calculos.neto_gravado;
                    total = calculos.total;
                    total_alicuotas = calculos.total_alicuotas;
                }
            } else {
                if (!isNaN(parseInt(unitario))) {
                    calculos = recalculateIva(unitario, cant, subtotal, line, porc, comboAlicuotaIva, neto_gravado, total_alicuotas, total, false);
                    subtotal = calculos.subtotal;
                    neto_gravado = calculos.neto_gravado;
                    total = calculos.total;
                    total_alicuotas = calculos.total_alicuotas;
                }
            }
        }
        return {subtotal: subtotal, neto_gravado: neto_gravado, total: total, total_alicuotas: total_alicuotas};
    }

    function set_subtotal_cbte(totales, idCbte, total_tributos) {
        var porcentaje_dto = get_porcentaje_descuento();
        var subtotal = 0;

        if (!esComprobanteA(idCbte) && !esComprobanteM(idCbte)) {
            subtotal = totales.total;
        } else {
            subtotal = totales.neto_gravado;

            if (totales.total_alicuotas[exento_id]) {
                subtotal += totales.total_alicuotas[exento_id].total;
            }

            if (totales.total_alicuotas[no_gravado_id]) {
                subtotal += totales.total_alicuotas[no_gravado_id].total;
            }
        }

        if ((esComprobanteA(idCbte) || esComprobanteM(idCbte) || porcentaje_dto > 0 || !$.isEmptyObject(total_tributos)) && subtotal > 0) {
            $(".subtotales").show();
            $("#label_subtotal").text("Subtotal").show();
            $("#subtotal").text(subtotal.toFixed(2)).show();
        } else {
            $(".subtotales").hide();
        }

        return subtotal;
    }

    function get_porcentaje_descuento() {
        var desc_valor = parseFloat($('#id_descuento').val());
        var descuento = isNaN(desc_valor) ? 0 : desc_valor;
        return descuento;
    }

    function set_importe_descuento(subtotal) {
        var porcentaje_dto = get_porcentaje_descuento();
        var descuento = subtotal * porcentaje_dto / 100;
        $("#descuento").text("(" + descuento.toFixed(2) + ")");
        return descuento;
    }

    function get_total_tributos() {
        var total_tributos = {};
        var tributos = $("#tributo_table tbody tr:visible");
        var line, base_imponible, alicuota;
        var total_line = 0;
        for (var i = 0; i < tributos.length; i++) {
            line = $(tributos[i]);
            base_imponible = line.find('input[id$="base_imponible"]').val();
            alicuota = line.find('input[id$="alicuota"]').val();
            if (!isNaN(parseFloat(base_imponible))) {
                if (alicuota === "") {
                    alicuota = "0";
                }
                alicuota = parseFloat(parseFloat(alicuota.replace(",", ".")).toFixed(2));
                base_imponible = parseFloat(parseFloat(base_imponible.replace(",", ".")).toFixed(2));

                total_line = base_imponible * alicuota / 100;
                line.find('span[id$="total"]').text(total_line);

                var tributoSelected = line.find('select[id$="-tributo"]>option:selected').val();
                if (total_tributos[tributoSelected] && total_tributos[tributoSelected].total) {
                    total_tributos[tributoSelected].total += total_line;
                } else {
                    total_tributos[tributoSelected] = {total: total_line};
                }
            }
        }
        return total_tributos;
    }
}