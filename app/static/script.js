window.onload = function() {
	document.getElementById("labeltoggle").addEventListener("change", toggleLabels);
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

var tablelookup = {0: 'manuscript', 1: 'person', 2: 'place', 3: 'watermark', 4: 'org',
5: 'exdoc', 6: 'subject', 7: 'publisher'};

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
destURL = endpointPath + '?entity=' + entity + '&id=' + dbID + '&state=add'
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
  .attr("r", 5)
  .attr("fill", function(d) { return color(d.group)})
  .attr("id", function(d) {return d.id; })
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