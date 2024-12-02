from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from api.models.auth import get_current_user
from agents.research import research_graph_builder
from api.services.save_report import save_report  
from api.models.get_database_collection import get_collections
from api.models.auth import oauth2_scheme
import uuid  

router = APIRouter()

report_collection = get_collections().get("report")

# A simple in-memory store (in practice, consider using Redis or a database)
sessions = {}

@router.get("/generate-report")
async def generate_report(
    topic: str,
    max_analysts: int,
    token: str = Depends(oauth2_scheme)
):
    # Get current user and check if the user is active
    current_user = await get_current_user(token, oauth2_scheme)
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Prepare the thread to collect the graph
    thread = {"configurable": {"thread_id": str(uuid.uuid4())}}  

    # Generate the initial graph (without feedback)
    graph = research_graph_builder()
    analysts_info = []

    # Collect the analyst information
    for event in graph.stream({"topic": topic, "max_analysts": max_analysts}, thread, stream_mode="values"):
        analysts = event.get('analysts', [])
        for analyst in analysts:
            analysts_info.append({
                "name": analyst.name,
                "affiliation": analyst.affiliation,
                "role": analyst.role,
                "description": analyst.description
            })

    # Save the session (analysts_info + graph) in memory or database
    sessions[thread["configurable"]["thread_id"]] = {
        "analysts_info": analysts_info,
        "topic": topic,
        "max_analysts": max_analysts,
        "graph": graph,  # Save the graph object here
        "created_at": datetime.utcnow()
    }

    # Return the thread ID for the next step (feedback)
    return {
        "thread_id": thread["configurable"]["thread_id"],
        "analysts": analysts_info,
        "message": "Please provide feedback to proceed with the final report generation."
    }

@router.post("/submit-feedback")
async def submit_feedback(
    thread_id: str,  
    feedback: str,
    token: str = Depends(oauth2_scheme)
):
    # Get current user and check if the user is active
    current_user = await get_current_user(token, oauth2_scheme)
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Retrieve the session (analysts' information + graph) based on thread_id
    session = sessions.get(thread_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    analysts_info = session["analysts_info"]
    topic = session["topic"]
    max_analysts = session["max_analysts"]
    graph = session["graph"]  # Retrieve the graph object

    thread = {"configurable": {"thread_id": thread_id}}
    
    # Add the feedback to the graph
    graph.update_state(thread, {"human_analyst_feedback": feedback}, as_node="human_feedback")
    
    # Generate the final report with the feedback applied
    final_analysts_info = []
    for event in graph.stream({"topic": topic, "max_analysts": max_analysts}, thread, stream_mode="values"):
        analysts = event.get('analysts', [])
        for analyst in analysts:
            final_analysts_info.append({
                "name": analyst.name,
                "affiliation": analyst.affiliation,
                "role": analyst.role,
                "description": analyst.description
            })

    # After updating the feedback, clear it to ensure no persistent feedback remains
    graph.update_state(thread, {"human_analyst_feedback": None}, as_node="human_feedback")
    
    # Stream updates and get the final report state
    for event in graph.stream(None, thread, stream_mode="updates"):
        next(iter(event.keys()))  

    final_state = graph.get_state(thread)
    report = final_state.values.get('final_report')

    # Prepare the final report data
    report_data = {
        "topic": topic,
        "analysts": final_analysts_info,
        "report": report,
        "created_at": datetime.utcnow()  
    }

    # Save the generated report to the database
    save_report(report_collection, report_data)

    # Remove the session after the report is generated (optional)
    del sessions[thread_id]

    return {
        "analysts": final_analysts_info,
        "report": report
    }

@router.get("/get-reports")
async def get_reports(token: str = Depends(oauth2_scheme)):
    current_user = await get_current_user(token, oauth2_scheme)
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")

    reports = list(report_collection.find({}))

    formatted_reports = []
    for report in reports:
        report['_id'] = str(report['_id'])
        formatted_reports.append(report)

    return {
        "reports": formatted_reports
    }
