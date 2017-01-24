var tablelookup = {0: 'manuscript', 1: 'person', 2: 'place', 3: 'watermark', 4: 'org',
5: 'ex_doc', 6: 'subject', 7: 'publisher'};

var jsonEndpoint = '/sendjson'
/*
function getNewNodes (node) {
	//query = jsonEndpoint + tablelookup[node.getAttribute('group')] + '&id=' + node.getAttribute('dbkey');
	//console.log(query);
	$.get(jsonEndpoint, 
		{'entity': tablelookup[node.getAttribute('group')],
	 'id': node.getAttribute('dbkey')},
	 function(data) {
	 	console.log(data);
	 },
	 "json");
}
*/