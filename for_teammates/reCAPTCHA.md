# This is a document for the reCAPTCHA verification.
I made the python backend part, and yall lowk gotta lock in to do this one.

## Prerequisites
1. **Sign Up for reCAPTCHA**: Register your website in the reCAPTCHA Admin Console to obtain a site key (public) and a secret key (private). Choose either reCAPTCHA v2 ("I'm not a robot" checkbox) or v3 (score-based, no user interaction).
   1. **Tip**: CHOOSE V3, the images are acc rly annoying 
2. **Add Domain**: Ensure your authorized domains (e.g., localhost for local testing) are added to your reCAPTCHA settings.

**(From Google Gemini)**

## Coding
It takes some html and js, but I also figured that out, so this is what it should look like:

```html
<script src="https://www.google.com/recaptcha/api.js?render=YOUR_SITE_KEY"></script>
<script>
    function onSubmit(event) {
        event.preventDefault();
        grecaptcha.ready(function() {
            grecaptcha.execute('YOUR_SITE_KEY', {action: 'submit'}).then(function(token) {
                // Add the token to a hidden input field
                document.getElementById("token_input").value = token;
                // Submit the form to your backend
                document.getElementById("demo-form").submit();
            });
        });
    }
</script>
<form id="demo-form" action="/submit-form" method="POST">
    <!-- form fields here -->
    <input type="hidden" id="token_input" name="g-recaptcha-response">
    <button type="submit" onclick="onSubmit(event)">Submit</button>
</form>
```

**Replace YOUR_SITE_KEY** with `6Lfcb0QsAAAAAIqvHgijjsGJm5QFX1AO4jtAZ4Su`

Basically, this means that whenever you want to create a form, such as the login page (which is the only place this CAPTCHA should be), all you have to do is wrap it in this:

```html
<form id='whatever-you-want' action='/submit-form' method=POST>
    <input type='text' name='username' placeholder='Username'>
    <!-- Whatever other inputs or textareas you want -->

     <!-- The reCAPTCHA hidden field -->
      <input type='hidden' id='token_input' name='g-recaptcha-response'>
      <button type='submit' onclick='onSubmit(event)'>Submit</button>
</form>
```

**So yeah!**