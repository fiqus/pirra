$(document).ready(function () {
    var timeout = 10 * 60 * 1000;  // 10 minutos

    function checkServerStatus() {
        $("#server_status").html("<i class='fa fa-spinner fa-spin'></i>");
        $("#server_status").attr("data-content", "Actualizando...");
        Pace.ignore(function () {
            $.get("/comprobantes/comprobante/check_status/")
                .done(function (data) {
                    if (data.AppServerStatus === "ok" && data.DbServerStatus === "ok" && data.AuthServerStatus === "ok") {
                        $("#server_status").html("<i class='fa fa-circle text-navy'></i>");
                        $("#server_status").attr("data-content", "Online");
                    }
                    else {
                        $("#server_status").html("<i class='fa fa-circle text-danger'></i>");
                        $("#server_status").attr("data-content", "Offline");
                    }
                    window.setTimeout(function () {
                        checkServerStatus();
                    }, timeout);
                })
                .error(function (err) {
                    $("#server_status").html("<i class='fa fa-circle text-danger'></i>");
                    $("#server_status").attr("data-content", "Offline");
                    window.setTimeout(function () {
                        checkServerStatus();
                    }, timeout);
                });
        });
    }

    checkServerStatus();
});