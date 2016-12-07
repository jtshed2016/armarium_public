window.onload = function () {
	document.getElementById("item_to_edit").addEventListener("change", updateContents);
	//console.log(document.getElementById("item_to_edit").value)
}

function updateContents() {
	msid = document.getElementById("item_to_edit").value
	$.get(
		"/sendcontentsjson",
		{'msid' : msid},
		function (data) {
			;
			contentsMenu = document.getElementById("content_item");
			contentsMenu.options.length = 0;
			var counter = 0
			for (item in data) {
				contentsMenu.options[counter] = new Option(data[item], item);
				counter ++;
			}
		}
		)
}