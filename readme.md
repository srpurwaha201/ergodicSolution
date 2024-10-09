**Q. How would you deal with this problem if there wasn’t a 1-1 correspondence between the entities mentioned in the text and the name of the entities in the graph?**
I would approach this problem using:
- Fuzzy Matching to find the close matches between text mentions and entity names in the graph
- Normalising the text before matching
- Using machine learning approach

# Improvements
Below are few improvements I would've done if I had more time:
- Using networkx for graph representation:
	- The current approach includes storing nodes and edges separately, and traversing all of them for each query
	- A better way would be to store the graph using a native graph data structure (for instance, using networkx python library)
	- That would enable in much faster performance. For instance, finding neighbours of a node will be much quicker and easier, in comparison to traversing all the edges in the current approach
- Handling the possibility of multiple relationships between a pair of nodes
	- Currently the **/relationship** api assumes there can only be a single edge between 2 nodes
- Handling indirect impact of a natural disaster on a city 
	- Currently the **/impact-analysis** api returns direct connections to a city (hence direct impact). Ideally it should return indirect impacts as well (i.e. connected components in the graph)