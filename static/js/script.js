$(document).ready(function () {
    $('.btn-redirect').click(function () {
        window.location.href=$( this ).attr( "data-redirect-url" );
    });

    $(".btn-ajax-toggle").click(function (e) {
        const url = $( this ).attr( "data-request-url" );
        const actionType = $( this ).attr( "data-action-type" );
        $.getJSON( url , ( data ) => {
            if (data.success) {
                if (actionType === "mark-favorite") {
                    let star_span = $(this).children('span');
                    if (!star_span.hasClass('checked')) {
                        star_span.toggleClass('checked');
                    }
                }
                else if (actionType === "mark-unread") {
                    $( this ).remove();
                }
            }
            else {
                if (actionType === "mark-favorite") {
                    let star_span = $(this).children('span');
                    if (star_span.hasClass('checked')) {
                        star_span.toggleClass('checked');
                    }
                }
            }
        });
    });
});
