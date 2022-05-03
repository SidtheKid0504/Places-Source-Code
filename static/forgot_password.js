const submitButton = document.getElementById("input-submit");
const forgotPasswordForm = document.getElementById("email-form");

submitButton.onclick = () => {
  forgotPasswordForm.submit();
}