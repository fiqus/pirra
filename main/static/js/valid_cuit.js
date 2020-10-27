/*
Use it with Jquery.Validation like this:

$.validator.addMethod("validCUIT", validCUIT, 'CUIT Inválido');

$("form").validate({
    rules: {
        CUIT_field: {
            validCUIT: true,
            required: true
        }
    }
});

*/

function validCUIT(cuit) {
    /* if (typeof (cuit) == 'undefined') {
        return true;
    }

    cuit = cuit.toString().replace(/[-_]/g, "");

    if (cuit == '')
        return true; //No estamos validando si el campo esta vacio, eso queda para el "required"

    if (cuit.length != 11) {
        return false;
    }
    else {
        var mult = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2];
        var total = 0;
        for (var i = 0; i < mult.length; i++) {
            total += parseInt(cuit[i]) * mult[i];
        }
        var mod = total % 11;
        var digit = mod == 0 ? 0 : mod == 1 ? 9 : 11 - mod;
    }
    return digit == parseInt(cuit[10]); */

    return true;
}