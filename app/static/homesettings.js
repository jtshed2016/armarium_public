window.onload = function() {
	sendbutton = document.getElementById("postbutton");
	sendbutton.addEventListener("click", postdata);
}

function populateMenu(chartsShown, chartsNotShown) {
	showMenu = document.getElementById("chartsdisplayed");
	currChoices = showMenu.querySelectorAll(".chartchoice");
	if (currChoices.length > 0) {
		for (i of currChoices) {
			showMenu.removeChild(i);
		}
	}

	for (shownchart in chartsShown){

		iterChoice = document.createElement("DIV");
		iterChoice.id = "chart" + chartsShown[shownchart].id.toString();
		iterChoice.setAttribute("class", "chartchoice");

		chartname = document.createElement("P");
		chartname.innerHTML = chartsShown[shownchart].name;

		upButton = document.createElement("BUTTON");
		upButton.setAttribute("class", "up_button")
		upButton.addEventListener("click", (function(val) {
			return function() {
				chartUp(val);
			};
		}(chartsShown[shownchart].id)));
		
		upButton.innerHTML = "Up";

		downButton = document.createElement("BUTTON");
		downButton.setAttribute("class", "down_button");
		downButton.addEventListener("click", (function(val) {
			return function() {
				chartDown(val);
			};
		}(chartsShown[shownchart].id)));		
		downButton.innerHTML = "Down";

		delButton = document.createElement("BUTTON");
		delButton.setAttribute("class", "del_button");
		delButton.addEventListener("click", (function(val) {
			return function() {
				removeChart(val);
			};
		}(chartsShown[shownchart].id)));
		delButton.innerHTML = "Don't Show";

		iterChoice.appendChild(chartname);
		iterChoice.appendChild(upButton);
		iterChoice.appendChild(downButton);
		iterChoice.appendChild(delButton);

		showMenu.appendChild(iterChoice);
	}

	hideMenu = document.getElementById("chartsnotdisplayed");
	hideChoices = hideMenu.querySelectorAll(".chartchoice");
	if (hideChoices.length > 0) {
		for (i of hideChoices) {
			hideMenu.removeChild(i);
		}
	}

	for (hidechart in chartsNotShown) {
		iterChoice = document.createElement("DIV");
		iterChoice.id = "chart" + chartsNotShown[hidechart].id.toString();
		iterChoice.setAttribute("class", "chartchoice");

		chartname = document.createElement("P");
		chartname.innerHTML = chartsNotShown[hidechart].name;

		showButton = document.createElement("BUTTON");
		showButton.setAttribute("class", "show_button");
		showButton.addEventListener("click", (function(val) {
			return function() {
				addChart(val);
			};
		}(chartsNotShown[hidechart].id)));
		showButton.innerHTML = "Show";

		iterChoice.appendChild(chartname);
		iterChoice.appendChild(showButton);
		hideMenu.appendChild(iterChoice);

	}

}

function chartUp(chartID) {
	focus = showncharts.find(function(currChart, chartIndex) { return currChart.id === this.valueOf();}, chartID);
	focusIndex = showncharts.indexOf(focus);
	if (focusIndex === 0) {
		alert('Already at top!');
	} else {
		switchItem = showncharts[focusIndex - 1];
		showncharts.splice((focusIndex - 1), 2, focus, switchItem);
		populateMenu(showncharts, notshown_charts);
	};
}

function chartDown(chartID) {
	focus = showncharts.find(function(currChart, chartIndex) { return currChart.id === this.valueOf();}, chartID);
	focusIndex = showncharts.indexOf(focus);

	if (focusIndex + 1 === showncharts.length) {
		alert('Already at end!');
	} else {
		switchItem = showncharts[focusIndex + 1];
		showncharts.splice(focusIndex, 2, switchItem, focus);
		populateMenu(showncharts, notshown_charts);
	};	
}

function removeChart(chartID) {
	focus = showncharts.find(function(currChart, chartIndex) { return currChart.id === this.valueOf();}, chartID);
	focusIndex = showncharts.indexOf(focus);
	removed = showncharts.splice(focusIndex, 1)[0];
	notshown_charts.push(removed);
	populateMenu(showncharts, notshown_charts);
}

function addChart(chartID) {
	focus = notshown_charts.find(function(currChart, chartIndex) { return currChart.id === this.valueOf();}, chartID);
	focusIndex = notshown_charts.indexOf(focus);
	added = notshown_charts.splice(focusIndex, 1)[0];
	showncharts.push(added);
	populateMenu(showncharts, notshown_charts);
}

function postdata() {

  //console.log(showncharts, notshown_charts);
  var returnlist = [];
  for (i in showncharts) {
  	showncharts[i].display = 1;
  	returnlist.push(showncharts[i]);
  }

  for (i in notshown_charts) {
  	notshown_charts[i].display = 0;
  	returnlist.push(notshown_charts[i]);
  }
  console.log(returnlist);

  chartsupdate = new XMLHttpRequest();
  var url = '';
  chartsupdate.open("POST", url, true);
  chartsupdate.setRequestHeader("Content-type", "application/json");
  chartsupdate.send(JSON.stringify(returnlist));
  alert('Homepage settings updated.');
}

