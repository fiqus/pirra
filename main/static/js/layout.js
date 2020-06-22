$(document).ready(function () {
    var timeout = 10 * 60 * 1000;  // 10 minutos

    function checkServerStatus() {
        $("#server_status").html("<i class='fa fa-spinner fa-spin'></i>");
        $("#server_status").attr("data-content", "Actualizando...");
        $("#server_status").html("<i class='fa fa-circle text-success'></i>");
        $("#server_status").attr("data-content", "Online");
    }

    checkServerStatus();
});