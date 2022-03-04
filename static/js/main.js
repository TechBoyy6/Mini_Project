const inputs = document.querySelectorAll(".input");


function addcl(){
	let parent = this.parentNode.parentNode;
	parent.classList.add("focus");
}

function remcl(){
	let parent = this.parentNode.parentNode;
	if(this.value == ""){
		parent.classList.remove("focus");
	}
}


inputs.forEach(input => {
	input.addEventListener("focus", addcl);
	input.addEventListener("blur", remcl);
});


function fetchDetails(){
	alert("Use the window to the right to fetch details.");
	document.getElementById('ownerDetailsDiv').style.display = 'grid';
	document.getElementById('external_site').style.display = 'grid';
	vehicle_data = document.getElementById('searchTools');
	console.log(vehicle_data);
	// values = document.getElementsByClassName('col-6 d-flex justify-content-start align-items-center');
	console.log("Main Values");
	console.log(vehicle_data.value);
	

	
	
}