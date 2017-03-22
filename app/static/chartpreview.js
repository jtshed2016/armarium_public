window.onload = function() {
	previewbutton = document.getElementById('previewbutton');
	previewbutton.addEventListener("click", (function(val1, val2, val3, val4, val5, val6, val7, val8) {
		return function() {
			mainsvg = document.getElementById(targetDiv);
			svgGraphics = mainsvg.querySelectorAll('g');
			svgRects = mainsvg.querySelectorAll('rect');
			
			if (svgGraphics.length > 0) {
				mainsvg.removeChild(svgGraphics[0]);
				}

			if (svgRects.length > 0) {
				mainsvg.removeChild(svgRects[0]);
			}
	
			val4 = document.getElementById('chart_x_label').value;
			val5 = document.getElementById('chart_y_label').value;

			//not used yet---need to add to main renderHomeChart method
			val8 = document.getElementById('chart_max_values').value;

			renderHomeChart(val1, val2, val3, val4, val5, val6, val7, val8);

			contextDiv = document.querySelectorAll('.viscontext')[0];
			
			headlineTarget = contextDiv.querySelectorAll('h3')[0];
			headlineTarget.innerHTML = document.getElementById('chart_title').value;

			contextTarget = contextDiv.querySelectorAll('p')[0];
			contextTarget.innerHTML = document.getElementById('chart_text').value;


		};
	}('#' + targetDiv, '#' + targetTip, x_id, x_label, y_label, chart_data, charturl, max_values)));	
}

//need to update chart context and headline, too