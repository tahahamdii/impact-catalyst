# api/routes/relation_graph.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
from api.models.auth import oauth2_scheme, get_current_user
from api.models.graph_database import get_graph
from pydantic import BaseModel

class RelationOption(BaseModel):
    option: str

router = APIRouter()

@router.get("/get-graph")
async def get_relation_graph(relation_option: str, token: str = Depends(oauth2_scheme)):
    current_user = await get_current_user(token, oauth2_scheme)
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Fetch the relationship graph based on the provided option
    graph = get_graph(relation_option)
    if graph is None:
        raise HTTPException(status_code=404, detail="Relation not found or no data available.")
    
    # Return the graph data: nodes and edges
    return {
        "nodes": list(graph.nodes),  # Assuming graph.nodes gives the nodes in the graph
        "edges": [{"source": u, "target": v, "type": d['type']} for u, v, d in graph.edges(data=True)]  # Get edge data
    }
