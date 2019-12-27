$(function(){
    $('#contact').click(function(){
        var url = $(this).attr('href');
        jQuery.ajax({
            url: url,
            success: function(data) {
                var dialog = bootbox.dialog({
                    message: data,
                    title: "Contactanos",
                    buttons: {
                        success: {
                            label: "Enviar",
                            className: "btn-success",
                            callback: function(){
                                $form = $(this);
                                $form.find(".btn-success").attr("disabled", true);
                                $.post(url, $("#contact-form").serialize())
                                    .done(function(){
                                        dialog.modal('hide');
                                        toastr["success"]("Su mensaje fue enviado correctamente.");
                                    })
                                    .fail(function(data){
                                        $('.bootbox-body').html(data.responseText);
                                        $form.find(".btn-success").attr("disabled", false);
                                    });
                                return false;
                            }
                        },
                        close: {
                            label: "Cerrar",
                            className: "btn-default"
                        }
                    }
                });
            }
        });
        return false;
    });
});