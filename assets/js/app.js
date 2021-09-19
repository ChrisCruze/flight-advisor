

function slack_message(text){
    var payload = {"text":text}
    payload = JSON.stringify(payload);
    $.ajax({type: "POST",
        url: "https://cors-anywhere.herokuapp.com/https://hooks.slack.com/services/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",
        dataType: 'json',
        headers: {
        "Content-Type": "application/json"},
        async: false,
        data: payload
        })
}

function slack_sign_up_email_notify(email){
    var text = `New Sign Up: ${email}`
    slack_message(text)
}