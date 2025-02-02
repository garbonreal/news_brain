// Implement some common effects

$(function () {
    // Sidebar to follow
    const topPadding = 15;
    const sidebar = $("#sidebar");
    const offset = sidebar.offset();
    const documentHeight = $(document).height();

    if (sidebar.length > 0) {
        $(window).scroll(function () {
            const sideBarHeight = sidebar.height();
            if ($(window).scrollTop() > offset.top) {
                let newPosition = ($(window).scrollTop() - offset.top) + topPadding;
                const maxPosition = documentHeight - (sideBarHeight + 368);
                if (newPosition > maxPosition) {
                    newPosition = maxPosition;
                }
                sidebar.stop().animate({
                    marginTop: newPosition
                });
            } else {
                sidebar.stop().animate({
                    marginTop: 15
                });
            }
        });
    }

    // User Center drop-down menu
    $('#loginCenter').hover(
        function () {
            $('.menu .userControl').css('display', 'block');
        }, function () {
            $('.menu .userControl').css('display', 'none');
        }
    );
});

// Back to top of page
function scrollToTop() {
    document.body.scrollTop = document.documentElement.scrollTop = 0;
}

function scrollToBottom() {
    document.body.scrollTop = document.documentElement.scrollTop = document.body.scrollHeight;
}
