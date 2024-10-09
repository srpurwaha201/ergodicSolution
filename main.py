from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import json
import time
from typing import List, Dict, Optional
import uuid

app = FastAPI()

# In-memory storage for task statuses
task_statuses = {}

graphDataPath: str = "data/kg.json"

# Load the knowledge graph data
with open(graphDataPath) as f:
    kg_data = json.load(f)

# Create a graph model
class GraphModel:
    def __init__(self, nodes, edges):
        self.nodes = {node["id"]: node for node in nodes}
        self.edges = edges

#class for text input for ml task api
class TextInput(BaseModel):
    text: str


graph = GraphModel(kg_data["nodes"], kg_data["edges"])

# Helper functions
def get_products_by_supplier(supplier_id):
    products = []
    for edge in graph.edges:
        if edge["source"] == supplier_id and edge["relationship"] == "supplies":
            manufacturer_id = edge["target"]
            for prod_edge in graph.edges:
                if prod_edge["source"] == manufacturer_id and prod_edge["relationship"] == "produces":
                    products.append(graph.nodes[prod_edge["target"]])
    return products

def get_manufacturing_locations(product_id):
    locations = set()
    for edge in graph.edges:
        if edge["target"] == product_id and edge["relationship"] == "produces":
            manufacturer_id = edge["source"]
            manufacturer = graph.nodes[manufacturer_id]
            locations.add(manufacturer["attributes"]["location"])
    return list(locations)

#handles both directed and undirected graphs
def find_path(start_node, end_node):
    def dfs(current, target, path, visited):
        if current == target:
            return path

        visited.add(current)
        for edge in graph.edges:
            if edge["source"] == current and edge["target"] not in visited:
                new_path = dfs(edge["target"], target, path + [edge], visited)
                if new_path:
                    return new_path
            elif edge["target"] == current and edge["source"] not in visited:
                new_path = dfs(edge["source"], target, path + [edge], visited)
                if new_path:
                    return new_path
        visited.remove(current)
        return None

    return dfs(start_node, end_node, [], set())

# API endpoint for getting products by supplier id
@app.get("/products-by-supplier/{supplier_id}")
async def get_supplier_products(supplier_id: str):
    if supplier_id not in graph.nodes:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return get_products_by_supplier(supplier_id)

# API endpoint for manufacturing locations by product id
@app.get("/manufacturing-locations/{product_id}")
async def get_product_manufacturing_locations(product_id: str):
    if product_id not in graph.nodes:
        raise HTTPException(status_code=404, detail="Product not found")
    return get_manufacturing_locations(product_id)

# Api end point for returning all the entities where location is city 
# (returns the directly impacted entities for now. ideally should return indirect entities as well)
@app.get("/impact-analysis/{city}")
async def analyze_natural_disaster_impact(city: str):
    affected_entities = []
    for node_id, node in graph.nodes.items():
        if node["attributes"].get("location") == city:
            affected_entities.append(node)
    return affected_entities

# Api end point for returning relationship between two nodes. 
# Assumes there is only a single relationship possible between two nodes
@app.get("/relationship/{node1_id}/{node2_id}")
async def get_relationship(node1_id: str, node2_id: str):
    if node1_id not in graph.nodes or node2_id not in graph.nodes:
        raise HTTPException(status_code=404, detail="One or both nodes not found")
    path = find_path(node1_id, node2_id)
    if path:
        return {"path": path}
    else:
        return {"message": "No relationship found between the nodes"}

async def process_ml_task(question: str):
    time.sleep(1000)  # Simulating a long-running task
    return "finished"

#APi end point for submitting ml task. ads the task in the background and returns the task id
@app.post("/ml-task")
async def create_ml_task(question: str, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    task_statuses[task_id] = {"status": "processing"}
    background_tasks.add_task(process_ml_task, task_id, question)
    return {"task_id": task_id, "status": "processing"}

#Api end point to check the status of the task with task id
@app.get("/ml-task/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in task_statuses:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_statuses[task_id]

# Entity extraction from text
def extract_entities(text: str) -> List[str]:
    entities = set()
    text_lower = text.lower()
    
    # Check for node names
    for node in graph.nodes.values():
        if node["name"].lower() in text_lower:
            entities.add(node["name"])
    
    # Check for attribute values
    for node in graph.nodes.values():
        for attr, value in node["attributes"].items():
            if isinstance(value, str) and value.lower() in text_lower:
                entities.add(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item.lower() in text_lower:
                        entities.add(item)
    
    # Check for edge attribute values
    for edge in graph.edges:
        for attr, value in edge["attributes"].items():
            if isinstance(value, str) and value.lower() in text_lower:
                entities.add(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item.lower() in text_lower:
                        entities.add(item)
    
    return list(entities)

@app.post("/extract-entities")
async def extract_entities_from_text(text_input: TextInput):
    return {"entities": extract_entities(text_input.text)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)