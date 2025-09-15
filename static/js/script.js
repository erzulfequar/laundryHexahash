
$(function () {
    $(".jq-verification").on("click", function () {
        $(".otpInput").val("");
        $(".invalidMsg").text("")
        $(".textMsg")
            .text(
                "Sending verification code on your email!"
            )
            .css("color", "red");

        var evidenceid = $(this).data("evidenceid");
        var reqData = { evidenceid: evidenceid };
        console.log(evidenceid);
        $.ajax({
            method: "POST",
            url: "/generate_verification_code",
            data: reqData,
            headers: { "X-CSRFToken": getCookie("csrftoken") },
        })
            .done(function (response) {
                console.log(response);
                if (response.success) {
                    $(".textMsg")
                        .text(
                            "Please enter the verification code sent to your email to download the evidence!"
                        )
                        .css("color", "green");
                }
            })

            .fail(function (jqXHR, textStatus) {
                alert("Request failed: " + textStatus);
            });
    });
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

$(function () {
    $(".download").on("click", function () {
        var inputOtpText = $(".otpInput").val();
        console.log(inputOtpText);

        $.ajax({
            method: "POST",
            url: "/verificationOtp",
            data: { inputOtpText: inputOtpText },
            headers: { "X-CSRFToken": getCookie("csrftoken") },
        })
            .done(function (response) {
                console.log(response);
                if (response.success) {
                    window.open(response.downloadLink, "_blank");
                    $(".hideModal").modal("hide");
                } else {
                    $(".invalidMsg")
                        .text("Please enter the currect verification code!")
                        .css("color", "red");
                }
            })
            .fail(function (jqXHR, textStatus) {
                alert("Request failed: " + textStatus);
                $(".invalidMsg")
                    .text("Please enter the currect verification code!")
                    .css("color", "red");
            });
    });
});


function togglePassword(id, el) {
    const input = document.getElementById(id);
    const icon = el.querySelector("i");

    if (input.type === "password") {
        input.type = "text";
        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");
    } else {
        input.type = "password";
        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");
    }
}


