window.onload = function() {
	if (window.location.pathname === '/addexdoc') {
		document.getElementById("ex_main_title").disabled = true;
		document.getElementById("ex_publisher").disabled = false;
		document.getElementById("ex_pub_loc").disabled = false;

	} else if (window.location.pathname === '/editexdoc') {
		document.getElementById("ex_main_title_new").disabled = true;
		document.getElementById("ex_publisher").disabled = true;
		document.getElementById("ex_pub_loc").disabled = true;
		document.getElementById("oldinput").checked = true;
	}
	document.getElementById("newinput").addEventListener("click", selectNew);
	document.getElementById("newinput").addEventListener("click", function () {document.getElementById('docsubmit').disabled = true;})
	document.getElementById("oldinput").addEventListener("click", selectOld);
	document.getElementById("ex_main_title_new").addEventListener("keyup", blockSubmitNew);
	document.getElementById("ex_main_title").addEventListener("change", blockSubmitOld);
	document.getElementById("docsubmit").addEventListener("mouseover", function () {console.log(document.getElementById("ex_main_title").value)})
	document.getElementById("ex_ref_ms").size="5";
}
function selectOld() {
	document.getElementById("ex_main_title_new").disabled = true;
	document.getElementById("ex_main_title_new").value = '';
	document.getElementById("ex_main_title").disabled = false;
	document.getElementById("ex_publisher").disabled = true;
	document.getElementById("ex_publisher").value = '';
	document.getElementById("ex_pub_loc").disabled = true;
	document.getElementById("ex_pub_loc").value = '';
	//console.log('Selecting old');
}

function selectNew() {
	document.getElementById("ex_main_title_new").disabled = false;
	document.getElementById("ex_main_title").value = '';
	document.getElementById("ex_main_title").disabled = true;
	document.getElementById("ex_publisher").disabled = false;
	document.getElementById("ex_pub_loc").disabled = false;

	//console.log('Selecting new');
}

function blockSubmitNew() {
	subButton = document.getElementById('docsubmit');
	
	if (document.getElementById("ex_main_title_new").disabled === false) {
		if (document.getElementById("ex_main_title_new").value === '') {
			subButton.disabled = true;
		} else {
			subButton.disabled = false;
		}
	} 
}

function blockSubmitOld() {
	subButton = document.getElementById('docsubmit');

	if (document.getElementById("ex_main_title").disabled === false) {
		if ((document.getElementById("ex_main_title").value === "0") || (document.getElementById("ex_main_title").value === undefined))  {
			subButton.disabled = true;
		} else {
			subButton.disabled = false;
		}
		
	}
}