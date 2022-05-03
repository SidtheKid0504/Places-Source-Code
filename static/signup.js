//Get HTML Form Elements From Form
const submitButton = document.getElementById("input-submit");
const signupForm = document.getElementById("signup-form");

//Submit HTML Form To Server
submitButton.addEventListener("click", () => { 
  signupForm.submit();
})