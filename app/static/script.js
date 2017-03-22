graphViewPaths = ['/ms', '/person', '/place', '/org', '/watermark', '/exwork', '/exdoc']

window.onload = function() {
  /*
  console.log(window.location.pathname);
  console.log((window.location.pathname).replace(/[0-9]*$/, ''));

  console.log(graphViewPaths.indexOf((window.location.pathname).replace(/[0-9]*$/, '')));
  */
  if (graphViewPaths.indexOf((window.location.pathname).replace(/[0-9]*$/, '')) !== -1) {

	 document.getElementById("labeltoggle").addEventListener("change", toggleLabels);
  }
}

function renderHomeChart(visDiv, toolTipDiv, x_axis_id, x_axis_label, y_axis_label, data, urlpath) {
  //take data from an entity or attribute, draw bar chart of frequencies on front page
    var svg = d3.select(visDiv),
    margin = {top: 20, right: 20, bottom: 75, left: 40},
    width = svg.attr("width") - margin.left - margin.right,
    height = svg.attr('height') - margin.top - margin.bottom;


  svg.append("rect")
    .attr("width", "100%")
    .attr("height", "100%")
    .attr("fill", "#fefae9");

  var x = d3.scaleBand().rangeRound([0, width]).padding(0.1),
  y = d3.scaleLinear().rangeRound([height, 0]);

  var g = svg.append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


    x.domain(data.map(function(d) {
      //return up to 10 characters of language name, plus ellipsis if longer; needs to match .bar entry below
      if (d.name.length >15) {
        return d.name.slice(0,15) + '...'
      } else {
        return d.name;
      };      
    }));
    y.domain([0, d3.max(data, function(d) { return d.frequency; })]);

    g.append("g")
      .attr("class", "axis axis--x")
      .attr("id", x_axis_id)
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(x))
      .selectAll("text")
      .style("text-anchor", "start")
      .attr("transform", "rotate(25)");

    //add x-axis label
    d3.select('#' + x_axis_id)
      .append("text")
      .text(x_axis_label)
      .attr("transform", "translate("+ (width/2).toString() + "," + (margin.bottom* (3/4)).toString() + ")")
      .attr("class", "axislabel");

    g.append("g")
      .attr("class", "axis axis--y")
      .call(d3.axisLeft(y).ticks(10))
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -30)
      .attr("dy", ".071em")
      .style("text-anchor", "end")
      .attr("class", "axislabel")
      .text(y_axis_label);

    g.selectAll(".bar")
      .data(data)
      .enter()
        .append("a")
        .attr("xlink:href", function(d) {return urlpath + d.id})
        .append("rect")
        .attr("class", "bar")
        .attr("x", function(d) {
          //return up to 10 characters of language name; must match x domain mapping above
          if (d.name.length > 15) {
            return x(d.name.slice(0,15) + "...");
          } else {
            return x(d.name);
          }
        })
        .attr("y", function(d) {return y(d.frequency); })
        .attr("width", x.bandwidth())
        .attr("height", function(d) {return height - y(d.frequency); })
        .attr("name", function(d) {return d.name;})
        .on("mouseover", function(d) {
          if (d.frequency === 1) {
            tooltext = " manuscript";
          } else {
            tooltext = " manuscripts";
          }
          d3.select(toolTipDiv)
          .style("visibility", "visible")
          .style("top", function() { return(d3.event.pageY - 50) + "px"; })
          .style("left", function() {return(d3.event.pageX - 100) + "px"; })
          .html(d.name + ": " + d.frequency + tooltext)
        })
        .on("mouseout", function() {d3.select(toolTipDiv).style("visibility", "hidden")});

}

function toggleLabels() {
	//turn labels on or off in graph vis
	labelstatus = document.getElementById("labeltoggle")['labeltoggle'].value
	
	var labels = document.getElementsByClassName('labels');

	if (labelstatus === 'off') {
		for (var i = 0; i< labels.length; i++) {
			labels[i].style.display = 'none';
		};
	} else {
			for (var i = 0; i< labels.length; i++) {
				labels[i].style.display = 'inline';
			};
	};
};

function populateGraphTip(inputNode) {
  //inputNode: circle element from vis
  //focusNode: Javascript object representing graph node
  focusNode = graph.nodes.find(function(currNode) {return currNode.id === this.id} ,inputNode);
  holderDiv = document.getElementById("nodeinfo");
  holderTable = holderDiv.getElementsByTagName('table')[0];
  holderDiv.removeChild(holderTable);
  
  /*
  console.log(focusNode);
  */

  newTable = document.createElement("TABLE");
  
  switch( focusNode.group) {
    case 0:
    //manuscript
      titleRow = document.createElement("TR");
      titleHead = document.createElement("TH");
      titleHead.innerHTML = "Title";
      titleRow.appendChild(titleHead);
      titleText = document.createElement("TD");
      titleText.innerHTML = focusNode.title;
      titleRow.appendChild(titleText);

      yearRow = document.createElement("TR");
      yearHead = document.createElement("TH");
      yearHead.innerHTML = "Date";
      yearRow.appendChild(yearHead);
      yearText = document.createElement("TD");
      yearText.innerHTML = focusNode.date;
      yearRow.appendChild(yearText);


      authorRow = document.createElement("TR");
      authorHead = document.createElement("TH");
      authorHead.innerHTML = "Author";
      authorRow.appendChild(authorHead);
      authorText = document.createElement("TD");
      authorText.innerHTML = focusNode.author;
      authorRow.appendChild(authorText);

      urlRow = document.createElement("TR");
      urlCell = document.createElement("TD");
      urlCell.colSpan = "2";
      urlCell.id = "pagelink";
      urlLink = document.createElement("A");
      urlLink.href = focusNode.url;
      urlLink.text = "Link to Page";
      urlCell.appendChild(urlLink);
      urlRow.appendChild(urlCell);

      newTable.appendChild(titleRow);
      newTable.appendChild(authorRow);
      newTable.appendChild(yearRow);
      newTable.appendChild(urlRow);

      break;
    case 1:
    //person
      nameRow = document.createElement("TR");
      nameHead = document.createElement("TH");
      nameHead.innerHTML = "Name";
      nameRow.appendChild(nameHead);
      nameText = document.createElement("TD");
      nameText.innerHTML = focusNode.name;
      nameRow.appendChild(nameText);

      yearRow = document.createElement("TR");
      yearHead = document.createElement("TH");
      yearHead.innerHTML = "Dates";
      yearRow.appendChild(yearHead);
      yearText = document.createElement("TD");
      yearText.innerHTML = focusNode.date;
      yearRow.appendChild(yearText);

      urlRow = document.createElement("TR");
      urlCell = document.createElement("TD");
      urlCell.colSpan = "2";
      urlCell.id = "pagelink";
      urlLink = document.createElement("A");
      urlLink.href = focusNode.url;
      urlLink.text = "Link to Page";
      urlCell.appendChild(urlLink);
      urlRow.appendChild(urlCell);

      newTable.appendChild(nameRow);
      newTable.appendChild(yearRow);
      newTable.appendChild(urlRow);
      break;

    case 2:
    //place
      nameRow = document.createElement("TR");
      nameHead = document.createElement("TH");
      nameHead.innerHTML = "Name";
      nameRow.appendChild(nameHead);
      nameText = document.createElement("TD");
      nameText.innerHTML = focusNode.name;
      nameRow.appendChild(nameText);

      urlRow = document.createElement("TR");
      urlCell = document.createElement("TD");
      urlCell.colSpan = "2";
      urlCell.id = "pagelink";
      urlLink = document.createElement("A");
      urlLink.href = focusNode.url;
      urlLink.text = "Link to Page";
      urlCell.appendChild(urlLink);
      urlRow.appendChild(urlCell);

      newTable.appendChild(nameRow);
      newTable.appendChild(urlRow);
      break;
    case 3:
    //watermark
      nameRow = document.createElement("TR");
      nameHead = document.createElement("TH");
      nameHead.innerHTML = "Name";
      nameRow.appendChild(nameHead);
      nameText = document.createElement("TD");
      nameText.innerHTML = focusNode.name;
      nameRow.appendChild(nameText);

      urlRow = document.createElement("TR");
      urlCell = document.createElement("TD");
      urlCell.colSpan = "2";
      urlCell.id = "pagelink";
      urlLink = document.createElement("A");
      urlLink.href = focusNode.url;
      urlLink.text = "Link to Page";
      urlCell.appendChild(urlLink);
      urlRow.appendChild(urlCell);

      briqUrlRow = document.createElement("TR");
      briqUrlText = document.createElement("TD");
      briqUrlText.colSpan = "2";
      briqUrlText.id = "pagelink";
      briqUrlLink = document.createElement("A");
      briqUrlLink.href = focusNode.briq_url;
      briqUrlLink.text = "View Watermark (Briquet Online)";
      briqUrlLink.target = '_blank'
      briqUrlLink.rel = 'noopener noreferrer'
      briqUrlText.appendChild(briqUrlLink);
      briqUrlRow.appendChild(briqUrlText);

      newTable.appendChild(nameRow);
      newTable.appendChild(urlRow);
      newTable.appendChild(briqUrlRow);

      break;
    case 4:
    //organization
      nameRow = document.createElement("TR");
      nameHead = document.createElement("TH");
      nameHead.innerHTML = "Name";
      nameRow.appendChild(nameHead);
      nameText = document.createElement("TD");
      nameText.innerHTML = focusNode.name;
      nameRow.appendChild(nameText);

      urlRow = document.createElement("TR");
      urlCell = document.createElement("TD");
      urlCell.colSpan = "2";
      urlCell.id = "pagelink";
      urlLink = document.createElement("A");
      urlLink.href = focusNode.url;
      urlLink.text = "Link to Page";
      urlCell.appendChild(urlLink);
      urlRow.appendChild(urlCell);

      newTable.appendChild(nameRow);
      newTable.appendChild(urlRow);
      break;
    case 5:
    //external doc
      nameRow = document.createElement("TR");
      nameHead = document.createElement("TH");
      nameHead.innerHTML = "Title";
      nameRow.appendChild(nameHead);
      nameText = document.createElement("TD");
      nameText.innerHTML = focusNode.name;
      nameRow.appendChild(nameText);

      authorRow = document.createElement("TR");
      authorHead = document.createElement("TH");
      authorHead.innerHTML = "Author";
      authorRow.appendChild(authorHead);
      authorText = document.createElement("TD");
      authorText.innerHTML = focusNode.author;
      authorRow.appendChild(authorText);

      dateRow = document.createElement("TR");
      dateHead = document.createElement("TH");
      dateHead.innerHTML = "Date";
      dateRow.appendChild(dateHead);
      dateText = document.createElement("TD");
      dateText.innerHTML = focusNode.dates;
      dateRow.appendChild(dateText);

      urlRow = document.createElement("TR");
      urlCell = document.createElement("TD");
      urlCell.colSpan = "2";
      urlCell.id = "pagelink";
      urlLink = document.createElement("A");
      urlLink.href = focusNode.url;
      urlLink.text = "Link to Page";
      urlCell.appendChild(urlLink);
      urlRow.appendChild(urlCell);

      newTable.appendChild(nameRow);
      newTable.appendChild(authorRow);
      newTable.appendChild(dateRow);
      newTable.appendChild(urlRow);

      break;
    case 6:
    //external work
      nameRow = document.createElement("TR");
      nameHead = document.createElement("TH");
      nameHead.innerHTML = "Title";
      nameRow.appendChild(nameHead);
      nameText = document.createElement("TD");
      nameText.innerHTML = focusNode.name;
      nameRow.appendChild(nameText);

      pubRow = document.createElement("TR");
      pubHead = document.createElement("TH");
      pubHead.innerHTML = "Publisher";
      pubRow.appendChild(pubHead);
      pubText = document.createElement("TD");
      pubText.innerHTML = focusNode.publisher + ', (' + focusNode.location + ')';
      pubRow.appendChild(pubText);

      urlRow = document.createElement("TR");
      urlCell = document.createElement("TD");
      urlCell.colSpan = "2";
      urlCell.id = "pagelink";
      urlLink = document.createElement("A");
      urlLink.href = focusNode.url;
      urlLink.text = "Link to Page";
      urlCell.appendChild(urlLink);
      urlRow.appendChild(urlCell);

      newTable.appendChild(nameRow);
      newTable.appendChild(pubRow);
      newTable.appendChild(urlRow);
      
      break;    
  }

  holderDiv.appendChild(newTable);
}

//lookup object of colors -- used to send arguments to controller when retrieving from DB to populate graph
//corresponds to 'valuemap' in get_info_from_db function in views.py
var tablelookup = {0: 'manuscript', 1: 'person', 2: 'place', 3: 'watermark', 4: 'org', 5: 'exdoc', 6: 'exwork'};

//assign colors from d3 range so they can be applied consistently across graphs
color = {0: "#1f77b4", 1: "#aec7e8", 2: "#ff7f0e", 3: "#ffbb78", 4: "#2ca02c", 5: "#98df8a", 6: "#d62728"}

//variables for forces in graph:
//forceStrength -- level of attraction (or repulsion, if negative)
var forceStrength = -80
//maximum distance between two nodes
var maximumDistance = 150
//minimum distance between two nodes
var minimumDistance = 40

var endpointPath = '/sendjson'


function ticked() {
    link
      .attr("x1", function(d) { return d.source.x; })
      .attr("y1", function(d) { return d.source.y; })
      .attr("x2", function(d) { return d.target.x; })
      .attr("y2", function(d) { return d.target.y; })

    node
      .attr("cx", function(d) { return d.x; })
      .attr("cy", function(d) { return d.y; });

    labels
      .attr("transform", function(d) { return "translate(" + (d.x + 5).toString() + "," + (d.y).toString() + ")";});
  }

 function dragstarted(d) {
  if (!d3.event.active) simulation.alphaTarget(0.3).restart();
  d.fx = d.x;
  d.fy = d.y;
 }

function dragged(d) {
  d.fx = d3.event.x;
  d.fy = d3.event.y;
}

function dragended(d) {
  if (!d3.event.active) simulation.alphaTarget(0);
  d.fx = null;
  d.fy = null;
}


function nodeExists(currNode) {
  //for use with array.find -- returns "true" if node already exists in graph array
  return currNode.id === this.id;
}

function linkExists(currLink) {
  //for use with array.find -- returns "true" if link or inverse already exists in graph array
  //console.log('current source: ', currLink.source);
  //console.log('current link ID (under iteration): ', currLink.source.id);

  return ((currLink.source.id === this.source) && (currLink.target.id === this.target)
    ||
    (currLink.source.id === this.target) && (currLink.target.id === this.source))
}


function getNewNodes(currNode) {
  idArgs = currNode.id.split('_')
  entity = tablelookup[idArgs[0]]
  dbID = idArgs[1]
//sends REQUEST to JSON endpoint to get new subgraph associated with node, calls update function
//destURL -- change to send entity name and ID when integrated
destURL = endpointPath + '?entity=' + entity + '&id=' + dbID
d3.json(destURL, function (newGraph) {
  update(newGraph);
})
}

function update(newData) {
  //takes new data, checks to see if nodes/links already exist, adds if necessary, re-renders graph
  for (x in newData.nodes) {
    //check for existing nodes
    if (graph.nodes.find(nodeExists, newData.nodes[x]) === undefined) {
      graph.nodes.push(newData.nodes[x])
      //if a node isn't in the graph, "undefined" is returned and the new node is pushed to array
    }
    

  }
  for (y in newData.links) {
    //check for existing links
    if (graph.links.find(linkExists, newData.links[y]) === undefined) {
      //if a link isn't in the graph, "undefined" is returned and the new link is pushed to array
      newLinkSource = graph.nodes.find( function(oldNode) { return oldNode.id === this.source}, newData.links[y]);
      newLinkTarget = graph.nodes.find( function(oldNode) { return oldNode.id === this.target}, newData.links[y]);
      graph.links.push({'source': newLinkSource, 'target': newLinkTarget, 'value': 10})
    }
  }

  //update nodes, links, and labels with new data and merge
  node = node.data(graph.nodes, function(d) { return d.id;});
  node.exit().remove();
  node = node.enter()
  .append("circle")
  .attr("class", "nodes")
  .attr("r", 5)
  .attr("fill", function(d) { return color[d.group]})
  .attr("id", function(d) {return d.id; })
  .attr("onmouseover", "populateGraphTip(this)")
  .attr("onclick", "getNewNodes(this)")
  .call(d3.drag()
  .on("start", dragstarted)
  .on("drag", dragged)
  .on("end", dragended))
  .merge(node);

  link = link.data(graph.links, function(d) { return d.source.id + "-" + d.target.id; });
  link.exit().remove();
  link = link.enter().append("line").merge(link).style("stroke-width", function(d) { return Math.sqrt(d.value)});

  labels = labels.data(graph.nodes);
  labels.exit().remove()
  labels = labels.enter()
  .append("text")
    .attr("dx", -10)
    .attr("dy", ".35em")
    .attr("class", "labels")
    .attr("fill", "black")
    .text(function(d) {return d.name})
    .merge(labels);

//restart simulation with new data
  simulation
    .nodes(graph.nodes)
  .force("link").links(graph.links);
  simulation
    .force("charge", d3.forceManyBody().strength(forceStrength).distanceMax(maximumDistance).distanceMin(minimumDistance))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .alpha(1).restart();

}