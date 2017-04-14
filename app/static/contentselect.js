window.onload = function () {
	document.getElementById("item_to_edit").addEventListener("change", updateContents);
}

function updateContents() {
	msid = document.getElementById("item_to_edit").value
	contents_req = new XMLHttpRequest();
	url = "/sendcontentsjson?msid=" + msid.toString();
	contents_req.onreadystatechange = function() {
		if (contents_req.readyState == XMLHttpRequest.DONE) {
			data = JSON.parse(contents_req.responseText);
			contentsMenu = document.getElementById("content_item");
			contentsMenu.options.length = 0;
			var counter = 0
			for (item in data) {
				contentsMenu.options[counter] = new Option(data[item], item);
				counter ++;
			}	
		}
	}
	contents_req.open("GET", url, true);
	contents_req.send();
}