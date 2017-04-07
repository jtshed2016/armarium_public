window.onload = function() {
	previewbutton = document.getElementById('previewbutton');
	previewbutton.addEventListener("click", (chartReRender(chartName, '#' + targetDiv, '#' + targetTip, x_id, x_label, y_label, chart_data, charturl, max_values)));	
}

function chartReRender(val0, val1, val2, val3, val4, val5, val6, val7, val8) {
		return function() {
			mainsvg = document.getElementById(val1.slice(1));
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
			val8 = document.getElementById('chart_max_values').value;

			renderHomeChart(val0, val1, val2, val3, val4, val5, val6, val7, val8);

			contextDiv = document.querySelectorAll('.viscontext')[0];
			
			headlineTarget = contextDiv.querySelectorAll('h3')[0];
			headlineTarget.innerHTML = document.getElementById('chart_title').value;

			contextTarget = contextDiv.querySelectorAll('p')[0];
			contextTarget.innerHTML = document.getElementById('chart_text').value;


			if (chartName === 'people') {
				selectForm = document.getElementById('relselect');

				if (selectForm === null) {
					selectForm = document.createElement('FORM');
					selectForm.setAttribute('id', 'relselect')

					formtitle = document.createElement('EM');
					formtitle.innerHTML = 'Display:';
					selectForm.appendChild(formtitle);

					document.getElementById(val0 + 'visholder').appendChild(selectForm);
				} else {
					currentRoleChecks = selectForm.querySelectorAll('.roleselect');
					if (currentRoleChecks.length > 0) {
						for (i of currentRoleChecks) {
							selectForm.removeChild(i);
						}
					}

					currentRoleLabels = selectForm.querySelectorAll('label');
					if (currentRoleLabels.length > 0) {
						for (i of currentRoleLabels) {
							selectForm.removeChild(i);
						}
					}
				}

				

				for (activerole in includeRels) {
					newCheck = document.createElement('input');
					newCheck.setAttribute('type', 'checkbox');
					newCheck.setAttribute('class', 'roleselect');
					newCheck.setAttribute('name', activerole);
					newCheck.setAttribute('value', activerole);
					if (includeRels[activerole] === true) {
						newCheck.setAttribute('checked', 'checked');
					}
					newCheck.addEventListener('change', reselectRels);
					newCheck.addEventListener('change', (chartReRender(chartName, '#' + targetDiv, '#' + targetTip, x_id, x_label, y_label, chart_data, charturl, max_values)));

					newLabel = document.createElement('LABEL');
					newLabel.setAttribute('for', activerole);
					newLabel.innerHTML = activerole;

					selectForm.appendChild(newCheck);
					selectForm.appendChild(newLabel);
				}

			}

		};
	}


function reselectRels() {
	includeRels[this.name] = this.checked;
}