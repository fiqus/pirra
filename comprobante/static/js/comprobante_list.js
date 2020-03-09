function preview(url) {
    var detail_template = Handlebars.compile($("#detail-modal-template").html());

    var modal = $(detail_template());
    modal.on('hidden.bs.modal', function () {
        modal.remove();
    });
    modal.modal();
    $.get(url).always(function (data) {
        modal.find(".modal-body").html(data);
        $('.carousel').carousel(
            {
                pause: true,
                interval: false
            });
    });
}

function print_pdf(url) {
   if( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ) {
       window.open(url, '_self');
   }else{
       window.open(url, '_blank');
   }
}

function show_inprogess_message(action) {
    $('#massive-result-header').hide();
    $('#massive-result').addClass('alert-info');
    $('#massive-result-body').html("Aguarde un instante por favor, estamos procesando sus comprobantes ... <br/>");
    if(action == 'autorizar') {
        $('#massive-result-body').append("Este proceso puede tomar unos minutos ya que dependemos de la velocidad de los servicios de la AFIP y de su conexión a internet");
    }
    $('#massive-result-footer').hide();
}

function show_result_message(alertClass, result, action) {
    $('#massive-result').removeClass('alert-danger');
    $('#massive-result').removeClass('alert-info');
    $('#massive-result').removeClass('alert-success');
    $('#massive-result').addClass(alertClass);
    $('#massive-result-header').show();
    $('#massive-result-body').html(result.result);
    $('#massive-result-footer').html("Se " + action + " <strong>" + result.cant + "</strong> comprobantes.").show();
}

function show_error_message(action) {
    $('#massive-result').removeClass('alert-success');
    $('#massive-result').removeClass('alert-info');
    $('#massive-result').addClass('alert-danger');
    $('#massive-result-header').show();
    $('#massive-result-body').html("<p class='error'><strong>Error durante el proceso. Por favor, intente nuevamente.<strong></p>");
    $('#massive-result-footer').html("Se " + action + " <strong>0</strong> comprobantes").show();
}

$.validator.addMethod("greaterThanStart", function(value, element) {
    var start = $(element).parents().find(".modal-dialog input[name$='_desde']").val();
    var startDate = new Date(start.split('/').reverse().join('/'));
    var endDate = new Date(value.split('/').reverse().join('/'));
    return startDate <= +endDate;
}, "Fecha desde debería ser mayor o igual a fecha hasta.");

function post_autorizacion_masiva(url){
    show_inprogess_message('autorizar');
    var $submitButton = $('#form_autorizar_masivo input:submit');
    $submitButton.attr('disabled', 'disabled');
    var closeButton = $('#form_autorizar_masivo button');
    closeButton.click(function(){
        $('body').spin({color: "#1AB394"});
        $('.overlay').css('display', 'block');
    });

    $.ajax({
        url: url, // the endpoint
        type: "POST", // http method
        data: $('#form_autorizar_masivo').serialize(), // data sent with the post request
        // handle a successful response
        success: function (result) {
            var alertClass = 'alert-' + result.result_type;
            show_result_message(alertClass, result, 'autorizaron');
            $submitButton.removeAttr('disabled');
        },
        // handle a non-successful response
        error: function (xhr, errmsg, err) {
            show_error_message('autorizaron');
            $submitButton.removeAttr('disabled');
        }
    });
}

function post_eliminacion_masiva(url){
    show_inprogess_message('eliminar');
    var $submitButton = $('#form_eliminar_masivo input:submit');
    $submitButton.attr('disabled', 'disabled');
    var closeButton = $('#form_eliminar_masivo button');
    closeButton.click(function(){
        $('body').spin({color: "#1AB394"});
        $('.overlay').css('display', 'block');
    });

    $.ajax({
        url: url,
        type: "POST",
        data: $('#form_eliminar_masivo').serialize(),
        success: function (result) {
            var alertClass = 'alert-' + result.result_type;
            show_result_message(alertClass, result, 'eliminaron');
            $submitButton.removeAttr('disabled');
        },
        error: function (xhr, errmsg, err) {
            show_error_message('eliminaron');
            $submitButton.removeAttr('disabled');
        }
    });
}

function autorizar_masivo(url) {
    var autorizar_template = Handlebars.compile($("#autorizar-masivo-modal-template").html());
    var modal = $(autorizar_template());

    modal.on('hidden.bs.modal', function () {
        modal.remove();
    });

    modal.modal();
    $.get(url).always(function (data) {
        modal.find(".modal-dynamic-content").html(data);
        modal.find("#id_autorizar_desde").datepicker({language: "es", format: "dd/mm/yyyy", autoclose: true});
        modal.find("#id_autorizar_hasta").datepicker({language: "es", format: "dd/mm/yyyy", autoclose: true});
        modal.find("#form_autorizar_masivo").validate({
            rules: {
                autorizar_desde: {
                    required: true
                },
                autorizar_hasta: {
                    required: true,
                    greaterThanStart: true
                }
            },
            submitHandler: function(form, e) {
                e.preventDefault();
                var closeButton = modal.find('#form_autorizar_masivo button, .modal-header button.close');
                closeButton.click(function(){
                    $('body').spin({color: "#1AB394"});
                    $('.overlay').css('display', 'block');
                    location.reload();
                });
                post_autorizacion_masiva(url);
            }
        });
    });
}

function imprimir_masivo(url) {
    var imprimir_template = Handlebars.compile($("#imprimir-masivo-modal-template").html());
    var modal = $(imprimir_template());

    modal.on('hidden.bs.modal', function () {
        modal.remove();
    });

    modal.modal();
    $.get(url).always(function (data) {
        modal.find(".modal-dynamic-content").html(data);
        modal.find("#id_imprimir_desde").datepicker({language: "es", format: "dd/mm/yyyy", autoclose: true});
        modal.find("#id_imprimir_hasta").datepicker({language: "es", format: "dd/mm/yyyy", autoclose: true});
        modal.find("#form_imprimir_masivo").validate({
            rules: {
                imprimir_desde: {
                    required: true
                },
                imprimir_hasta: {
                    required: true,
                    greaterThanStart: true
                }
            }
        });
    });
}

function eliminar_masivo(url) {
    var eliminar_template = Handlebars.compile($("#eliminar-masivo-modal-template").html());
    var modal = $(eliminar_template());

    modal.on('hidden.bs.modal', function () {
        modal.remove();
        location.reload();
    });

    modal.modal();
    $.get(url).always(function (data) {
        modal.find(".modal-dynamic-content").html(data);
        var closeButton = modal.find('#form_eliminar_masivo button');
        closeButton.click(function(){
            $('body').spin({color: "#1AB394"});
            $('.overlay').css('display', 'block');
        });

        modal.find("#id_eliminar_desde").datepicker({language: "es", format: "dd/mm/yyyy", autoclose: true});
        modal.find("#id_eliminar_hasta").datepicker({language: "es", format: "dd/mm/yyyy", autoclose: true});
        modal.find("#form_eliminar_masivo").validate({
            rules: {
                eliminar_desde: {
                    required: true
                },
                eliminar_hasta: {
                    required: true,
                    greaterThanStart: true
                }
            },
            submitHandler: function(form, e) {
                e.preventDefault();
                post_eliminacion_masiva(url);
            }
        });
    });
}

function imprimir_masivo_seleccion(url){
    var data = [];
    var comprobantesList = [];
    var compNumber;
    $('input[name="selection"]:checked').each(function(){
        data.push({value:this.value});
        //FIXME esto no debería ser posicional! Si se cambian de lugar o se agregan columnas se rompe el envío
        compNumber = $(this.parentNode.nextElementSibling.nextElementSibling).html().trim();
        if(compNumber.match(/\d+/g) != null){
            comprobantesList.push(compNumber);
        }
    });

    var imprimir_template = Handlebars.compile($("#imprimir-masivo-seleccion-modal-template").html());
    var modal = $(imprimir_template());

    modal.on('hidden.bs.modal', function () {
        modal.remove();
    });
    data = {pks: JSON.stringify(data), comprobantes: JSON.stringify(comprobantesList)};
    modal.modal();
    $.get(url, data).always(function (data) {
        modal.find(".modal-dynamic-content").html(data);
    });
}

function autorizar_masivo_seleccion(url){
    var data = [];
    var comprobantesList = [];
    var compNumber, compDesc;
    //FIXME Esto deberia ser una funcion, esta repetido muchas veces
    $('input[name="selection"]:checked').each(function(){
        data.push({value:this.value});
        //FIXME esto no debería ser posicional! Si se cambian de lugar o se agregan columnas se rompe el envío
        compNumber = $(this.parentNode.nextElementSibling).html().trim();
        if(compNumber.match(/\d+/g) == null){
            var tipoCompEl = this.parentNode.nextElementSibling.nextElementSibling;
            compDesc = $(tipoCompEl).html().trim() + ' - ' + $(tipoCompEl.nextElementSibling).html().trim();
            comprobantesList.push(compDesc);
        }
    });

    var autorizar_template = Handlebars.compile($("#autorizar-masivo-seleccion-modal-template").html());
    var modal = $(autorizar_template());

    modal.on('hidden.bs.modal', function () {
        modal.remove();
    });
    var pks = JSON.stringify(data);
    data = {pks: pks, comprobantes: JSON.stringify(comprobantesList)};

    modal.modal();

    $.get(url, data).always(function (data) {
        modal.find(".modal-dynamic-content").html(data);

        var $submitButton = modal.find('#form_autorizar_masivo_seleccion input:submit');
        $submitButton.on('click', function(){
            modal.on('hidden.bs.modal', function () {
                modal.remove();
                location.reload();
            });

            var closeButton = modal.find('#form_autorizar_masivo_seleccion button, .modal-header button.close');
            closeButton.click(function(){
                $('body').spin({color: "#1AB394"});
                $('.overlay').css('display', 'block');
            });

            $submitButton.attr('disabled', 'disabled');
            show_inprogess_message('autorizar');

            cbtes_id = $('input[name="nros_comp_autorizar"]').val()

            $.ajax({
                url: url,
                type: "POST",
                data: {nros_comp_autorizar: cbtes_id},
                success: function (result) {
                    var alertClass = 'alert-' + result.result_type;
                    show_result_message(alertClass, result, 'autorizaron');
                    $submitButton.removeAttr('disabled');
                },
                error: function (xhr, errmsg, err) {
                    show_error_message('autorizaron');
                    $submitButton.removeAttr('disabled');
                }
            });
            return false;
        });
    });
}

function duplicar_masivo_seleccion(url){
    var data = [];
    var comprobantesList = [];
    var compNumber, compDesc;
    //FIXME Esto deberia ser una funcion, esta repetido muchas veces
    $('input[name="selection"]:checked').each(function(){
        data.push({value:this.value});
        //FIXME esto no debería ser posicional! Si se cambian de lugar o se agregan columnas se rompe el envío
        compNumber = $(this.parentNode.nextElementSibling).html().trim();
        var tipoCompEl = this.parentNode.nextElementSibling.nextElementSibling;
        compDesc = $(tipoCompEl).html().trim() + ' - ' + $(tipoCompEl.nextElementSibling).html().trim();
        comprobantesList.push(compDesc);
    });

    var duplicar_template = Handlebars.compile($("#duplicar-masivo-seleccion-modal-template").html());
    var modal = $(duplicar_template());

    modal.on('hidden.bs.modal', function () {
        modal.remove();
        location.reload();
    });
    var pks = JSON.stringify(data);
    data = {pks: pks, comprobantes: JSON.stringify(comprobantesList)};

    modal.modal();
    $.get(url, data).always(function (data) {
        modal.find(".modal-dynamic-content").html(data);

        var closeButton = modal.find('#form_duplicar_masivo_seleccion button');
        closeButton.click(function(){
            $('body').spin({color: "#1AB394"});
            $('.overlay').css('display', 'block');
        });

        var $submitButton = modal.find('#form_duplicar_masivo_seleccion input:submit');
        $submitButton.on('click', function(){
            $submitButton.attr('disabled', 'disabled');
            show_inprogess_message('duplicar');

            cbtes_id = $('input[name="nros_comp_duplicar"]').val()

            $.ajax({
                url: url,
                type: "POST",
                dataType: "json",
                data: {nros_comp_duplicar: cbtes_id},
                success: function (result) {
                    var alertClass = 'alert-' + result.result_type;
                    show_result_message(alertClass, result, 'duplicaron');
                    $submitButton.removeAttr('disabled');
                },
                error: function (xhr, errmsg, err) {
                    show_error_message('duplicaron');
                    $submitButton.removeAttr('disabled');
                }
            });
            return false;
        });
    });
}

function eliminar_masivo_seleccion(url){
    var data = [];
    var comprobantesList = [];
    var compNumber, compDesc;
    //FIXME Esto deberia ser una funcion, esta repetido muchas veces
    $('input[name="selection"]:checked').each(function(){
        data.push({value:this.value});
        //FIXME esto no debería ser posicional! Si se cambian de lugar o se agregan columnas se rompe el envío
        compNumber = $(this.parentNode.nextElementSibling).html().trim();
        if(compNumber.match(/\d+/g) == null){
            var tipoCompEl = this.parentNode.nextElementSibling.nextElementSibling;
            compDesc = $(tipoCompEl).html().trim() + ' - ' + $(tipoCompEl.nextElementSibling).html().trim();
            comprobantesList.push(compDesc);
        }
    });

    var eliminar_template = Handlebars.compile($("#eliminar-masivo-seleccion-modal-template").html());
    var modal = $(eliminar_template());

    modal.on('hidden.bs.modal', function () {
        modal.remove();
        location.reload();
    });
    var pks = JSON.stringify(data);
    data = {pks: pks, comprobantes: JSON.stringify(comprobantesList)};

    modal.modal();
    $.get(url, data).always(function (data) {
        modal.find(".modal-dynamic-content").html(data);

        var closeButton = modal.find('#form_eliminar_masivo_seleccion button');
        closeButton.click(function(){
            $('body').spin({color: "#1AB394"});
            $('.overlay').css('display', 'block');
        });

        var $submitButton = modal.find('#form_eliminar_masivo_seleccion input:submit');
        $submitButton.on('click', function(){
            $submitButton.attr('disabled', 'disabled');
            show_inprogess_message('eliminar');

            cbtes_id = $('input[name="nros_comp_eliminar"]').val()

            $.ajax({
                url: url,
                type: "POST",
                dataType: "json",
                data: {nros_comp_eliminar: cbtes_id},
                success: function (result) {
                    var alertClass = 'alert-' + result.result_type;
                    show_result_message(alertClass, result, 'eliminaron');
                    $submitButton.removeAttr('disabled');
                },
                error: function (xhr, errmsg, err) {
                    show_error_message('eliminaron');
                    $submitButton.removeAttr('disabled');
                }
            });
            return false;
        });
    });
}

function enviar_masivo_seleccion(url){
    var data = [];
    var comprobantesList = [];
    var compNumber, compDesc;

    //FIXME Esto deberia ser una funcion, esta repetido muchas veces
    $('input[name="selection"]:checked').each(function(){
        data.push({value:this.value});
        //FIXME esto no debería ser posicional! Si se cambian de lugar o se agregan columnas se rompe el envío
        compNumber = $(this.parentNode.nextElementSibling.nextElementSibling).html().trim();
        if(compNumber.match(/\d+/g) != null){
            var tipoCompEl = this.parentNode.nextElementSibling.nextElementSibling;
            compDesc = $(tipoCompEl).html().trim() + ' - ' + $(tipoCompEl.nextElementSibling).html().trim();
            comprobantesList.push(compDesc);
        }
    });

    var enviar_template = Handlebars.compile($("#enviar-masivo-seleccion-modal-template").html());
    var modal = $(enviar_template());

    modal.on('hidden.bs.modal', function () {
        modal.remove();
    });

    var pks = JSON.stringify(data);
    data = {pks: pks, comprobantes: JSON.stringify(comprobantesList)};

    modal.modal();
    $.get(url, data).always(function (data) {
        modal.find(".modal-dynamic-content").html(data);

        var $submitButton = modal.find('#form_enviar_masivo_seleccion input:submit');
        var $cancelButton = modal.find('#form_enviar_masivo_seleccion div.modal-footer button, .modal-header button.close');
        var $spinner = modal.find('#form_enviar_masivo_seleccion div.modal-footer i.spinner');

        $submitButton.on('click', function(){
            $submitButton.hide();
            $cancelButton.attr('disabled', 'disabled');
            $spinner.show();
            show_inprogess_message('enviar');

            $cancelButton.click(function(){
                $('body').spin({color: "#1AB394"});
                $('.overlay').css('display', 'block');
            });

            modal.on('hidden.bs.modal', function () {
                modal.remove();
                location.reload();
            });

            var cbtes_id = $('input[name="nros_comp_enviar"]').val();

            $.ajax({
                url: url,
                type: "POST",
                dataType: "json",
                data: {nros_comp_enviar: cbtes_id},
                success: function (result) {
                    var alertClass = 'alert-' + result.result_type;

                    $('.comp_to_send_el, #eliminar_masivo').hide();

                    show_result_message(alertClass, result, 'enviaron');
                    var resultElem = $('#sent_comp_result');
                    var result_list = result.sent_comprobantes_list;
                    for (var i= 0, len = result_list.length; i < len; i++){
                        if(result_list[i].error){
                            resultElem.append('<li style="color: red;)">'+result_list[i].comp+' - '+result_list[i].status+'</li>')
                        }else {
                            resultElem.append('<li>'+result_list[i].comp+' - '+result_list[i].status+'</li>')
                        }
                    }
                    $submitButton.show();
                    $cancelButton.removeAttr('disabled');
                    $spinner.hide();
                },
                error: function (xhr, errmsg, err) {
                    show_error_message('enviaron');
                    $submitButton.show();
                    $cancelButton.removeAttr('disabled');
                    $spinner.hide();
                }
            });
            return false;
        });
    });
}

function autorizar(url) {
    var autorizar_template = Handlebars.compile($("#autorizar-modal-template").html());

    var modal = $(autorizar_template());
    modal.on('hidden.bs.modal', function () {
        modal.remove();
    });
    modal.modal();
    $.get(url).always(function (data) {
        modal.find(".modal-dynamic-content").html(data);
        modal.find("input:submit").click(function() {
            $(this).attr('disabled', true);
            $(this).siblings('button').attr('disabled', true);
            modal.find('button.close').attr('disabled', true);
            modal.find(".modal-title .spinner").show();
            modal.find('form').submit();
        });
    });
}

function toggleMassiveActionsButtons() {
    var total = $('input[name="selection"]:checked').length;
    if (total > 0) {
        $('.accion-masiva-deselected ').addClass("d-none");
        $('.accion-masiva-selected, #imprimir_masivo_seleccion').removeClass('d-none');
    }
    else {
        $('.accion-masiva-deselected ').removeClass("d-none");
        $('.accion-masiva-selected, #imprimir_masivo_seleccion').addClass('d-none');
    }
}

function exportar_citi_ventas() {
    $.get($("#exportar-citi-ventas").data("url")).always(function (data) {
        var dialog = bootbox.dialog({
            message: data,
            title: "Exportar Régimen de información de Ventas AFIP",
            buttons: {
                success: {
                    label: "Descargar",
                    className: "btn-success",
                    callback: function () {
                        $(this).find('form').submit();
                    }
                },
                close: {
                    label: "Cerrar",
                    className: "btn-default"
                }
            }
        });
        var mesActual = new Date().getMonth() + 1;
        $('#mes').val(mesActual);
    });
}

function exportar_masivo(url) {
    var exportar_template = Handlebars.compile($("#exportar-masivo-modal-template").html());
    var modal = $(exportar_template());

    modal.on('hidden.bs.modal', function () {
        modal.remove();
    });

    modal.modal();
    $.get(url).always(function (data) {
        modal.find(".modal-dynamic-content").html(data);
        modal.find("#id_exportar_desde").datepicker({language: "es", format: "dd/mm/yyyy", autoclose: true});
        modal.find("#id_exportar_hasta").datepicker({language: "es", format: "dd/mm/yyyy", autoclose: true});
        modal.find("#form_exportar_masivo").validate({
            rules: {
                exportar_desde: {
                    required: true
                },
                exportar_hasta: {
                    required: true,
                    greaterThanStart: true
                }
            }
        });
    });
}

function historial_enviados(url, cbte) {
    $.get(url).always(function (data) {
        var dialog = bootbox.dialog({
            message: data,
            title: "Historial de envíos: " + cbte,
            buttons: {
                close: {
                    label: "Cerrar",
                    className: "btn-default"
                }
            }
        });
    });
}

function enviar_comp_mail(url, cbte) {
    $.get(url).always(function (data) {
        var dialog = bootbox.dialog({
            message: data,
            title: "Enviar comprobante "+ cbte +" por email"
        });
        dialog.on('hidden.bs.modal', function () {
            dialog.remove();
            location.reload();
        });
    });
}

$(function () {

    toggleMassiveActionsButtons();

    $('[data-toggle="popover"]').popover();

    $('[data-toggle="tooltip"]').tooltip();

    $("#id_fecha_desde").datepicker({language: "es", format: "dd/mm/yyyy", orientation: "bottom"});
    $("#id_fecha_hasta").datepicker({language: "es", format: "dd/mm/yyyy", orientation: "bottom"});

    $(".detail-click").click(function(e){
        if(!$(e.target).is(':checkbox')){
            var url = $(e.target).data('url');
            if (!url) {
                url = this.getAttribute('data-url');
            }
            preview(url);
        } else {
           toggleMassiveActionsButtons();
        }
    });

    $('td input[type="checkbox"]').click(function(e){
        if(!$(e.target).is('input')){
            $(this).find('input').click();
        }
        toggleMassiveActionsButtons();
    });

    $("#cbte-search-form select[name='cliente']").selectize();

    $(document).click(function (e) {
        $('[data-toggle="popover"]').each(function () {
            if (!$(this).is(e.target) && $(this).has(e.target).length === 0 && $('.popover').has(e.target).length === 0) {
                //$(this).popover('hide');
                if ($(this).data('bs.popover').tip().hasClass('in')) {
                    $(this).popover('toggle');
                }
                return;
            }
        });
    });

    $(".link_imprimir").click(function(e){
        print_pdf($(this).attr("href"));
        return false;
    });


    $('#selectAll').click(function(event) {
        var isChecked = this.checked;
        $(':checkbox').each(function() {
            this.checked = isChecked;
        });
        toggleMassiveActionsButtons();
    });

    $("#exportar-citi-ventas").click(exportar_citi_ventas);

    $(".historial-enviados").click(function () {
        var $this = $(this);
        var url = $this.data("url");
        var cbte = $this.data("tipo-cbte") + " " + $this.data("numero");
        return historial_enviados(url, cbte);
    });

    $(".enviar-comp-mail").click(function () {
        var $this = $(this);
        var url = $this.data("url");
        var cbte = $this.data("tipo-cbte") + " " + $this.data("numero");
        return enviar_comp_mail(url, cbte);
    });

    $(".import").click(function () {
        var url = $(this).attr('href');
        var iframeSuccess = false;
        var import_dialog = bootbox.dialog({
            message: '<iframe id="import_iframe" src="' + url + '" frameborder="0"></iframe>',
            title: "Importar Comprobantes",
            size: "large",
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
        return false;
    });
});
