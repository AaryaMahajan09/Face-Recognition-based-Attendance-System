function selectRole(button, role){

   
    document.querySelectorAll(".role-btn")
    .forEach(btn => btn.classList.remove("active"));

    button.classList.add("active");

    
    document.getElementById("role").value = role;

}

function toggleSidebar(){
document.querySelector(".sidebar").classList.toggle("active");
}

