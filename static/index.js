//Login Code 
//Get All HTML Form Components
const modal = document.getElementById('loginModal');
const submitButton  = document.getElementById('submitLogin');
const loginForm = document.getElementById("login-form");

//Prevent The Usage Of The Enter Button When Typing So People Cant Spam Empty Space
$(document).ready(function() {
  $(window).keydown(function(event){
    if(event.keyCode == 13) {
      event.preventDefault();
      return false;
    }
  });
});

//Function to Check If User Has Logged In And Remove Modal Accordingly
function displayOrUndisplayModal(user_defined) {
  if (user_defined === undefined || user_defined === "") {
    modal.style.display="block";
  } else {
    modal.style.display="none";
    populate(250);
  }
}

//Submit Login Form When User Information Is Submitted
submitButton.addEventListener("click", () => {
  loginForm.submit(e => {
    e.preventDefault();
  });
});

//Canvas Components
const container = document.querySelector('.container');
const color = document.querySelector('.color');
const resetBtn = document.querySelector('.btn');

//Variables To Check Time The Last Time A User Placed A Pixel And If They Can Draw
let timePixelPlaced;
let draw;

//Function To Get And Display All Placed Pixels
function populate(size) {
  //Add A Pixel To The Container Depending The Area Of The Container
  container.style.setProperty('--size', size);
  let i=0, len=size*size;
  while(i<len) {
    const div = document.createElement('div');
    div.classList.add('pixel');
    div.setAttribute("id", `pixel${i}`);
    container.appendChild(div);
    i++;
  }

  //Send Pixel Data And Tell Server That A User Placed A Pixel When A Pixel Is Clicked
  document.querySelectorAll('.pixel').forEach(item => {
    item.addEventListener('click', () => {
      if (draw) {
        item.style.backgroundColor = color.value;
        $.post(window.location.href, {
          pixel_id: item.id,
          color: color.value,
          last_time_pixel_placed: new Date()
        });
        //Change The Time The User Placed Te Pixel And Set Their Ability To Draw As False
        timePixelPlaced = new Date();
        draw = false;
      } 
    });
  });
}

//Get The Pixels That Have Been Placed And Change Their Color
function getPixels(pixel_id, color) {
  changedElement = document.getElementById(pixel_id);
  changedElement.style.backgroundColor = color;
}

//Timer Code
//Get The HTML Timer On The Site
const timerText = document.getElementById("timer");

// Function To Set Timer With A Parameter Of Time
function timer(time) {
  let lastPixelTime;
  //Check If Timer Is Already Initalized Else Make The Last Time Pixel Placed The Inputted Time
  if (timePixelPlaced) {
    lastPixelTime = timePixelPlaced;
  } else {
    lastPixelTime = new Date(time);
  }
  // Get The Next Time Period Before User Can Place Another Pixel
  let minutesToAdd = 5;
  let nextPixelTime = new Date(lastPixelTime.getTime() + minutesToAdd*60000);

  //Get The Current Time
  currentTime = new Date();

  //Check If The Current Time Is Less Than The Next Time A Pixel Can Be Placed
  if (currentTime.getTime() < nextPixelTime.getTime()) {
    //Set If The User Can Draw To False
    draw = false;

    //Get The Difference Of Time Between The Two Time Periods And Display It On The Timer
    let timeDiff = nextPixelTime.getTime() - currentTime.getTime();
    let minRemaining = Math.floor((timeDiff%(1000 * 60 * 60)) / (1000 * 60)).toString();
    let secRemaining = Math.floor((timeDiff%(1000 * 60)) / 1000);
    if (secRemaining < 10) {
      secRemaining = `0${secRemaining}`
    }
    timerText.innerHTML=`Time Until You Can Place Your Next Pixel- ${minRemaining}:${secRemaining}`;

  } else {
    /*
      If The Current Time Is Equal Or Greater Than The Time The Next Pixel Can Be Placed
      Allow The User To Draw
    */
    draw = true;
    timerText.innerHTML=`Time Until You Can Place Your Next Pixel- 0:00`;
  }
}

//Chat Box Code
//Get All Elements Of The Chat Box
const messageButton = document.getElementById("message-submit");
const userMessage  = document.getElementById("user-message");
const allMessages = document.getElementById("all-messages");

//Send Chat Data To Server
messageButton.addEventListener("click", () => {
  $.post(window.location.href, {
    message: userMessage.value
  });
});

//Connect To Socketio(The Thing Used To Send Stuff To Other Users)
const socket = io(window.location.href, {
  withCredentials: true,
  extraHeaders: {
    "custom-header": "places0504" //Can Make This Custom Header Anything
  }
});

//Change The Pixel That Was Clicked On For All Users Online
socket.on("send_pixel", pixel => {
  changedElement = document.getElementById(pixel.pixel_id);
  changedElement.style.backgroundColor = pixel.color;
});

//Send The Message To All Users Online
socket.on("send_message", message => {
  let newMessage = document.createElement("li");
  newMessage.setAttribute("class", "message");
  newMessage.innerHTML = `${message.current_username}: ${message.message}`;
  allMessages.appendChild(newMessage);
  userMessage.value = "";
});