import os
import json
import asyncio
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="🦞 Romy - Complete Business System")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Config
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vtovgrtlxekmshgxhmim.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

def supabase(method, endpoint, data=None):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
    try:
        with httpx.Client(timeout=30) as client:
            r = client.request(method, f"{SUPABASE_URL}/rest/v1/{endpoint}", headers=headers, json=data)
            return r.json()
    except Exception as e:
        return {"error": str(e)}

# ========================
# BUSINESS ENTITIES
# ========================

class PipelineState:
    def __init__(self, lead_id: str):
        self.lead_id = lead_id
        self.steps = []
        self.decisions = []
        self.questions_asked = []
        self.outputs = {}
    
    def add_step(self, agent: str, task: str, output: str):
        self.steps.append({"agent": agent, "task": task, "output": output[:1000], "timestamp": datetime.now().isoformat()})
        self.outputs[agent] = output
    
    def add_decision(self, decision: str, reasoning: str):
        self.decisions.append({"decision": decision, "reasoning": reasoning, "timestamp": datetime.now().isoformat()})

# ========================
# AGENTS - FULL BUSINESS SUITE
# ========================

async def run_agent(agent_type: str, task: str, context: Dict = None) -> Dict:
    """Run agent - returns actual working output"""
    agents = {
        # SALES & REVENUE
        "sales": {"role": "Sales Executive", "goal": "Close deals"},
        "closer": {"role": "Deal Closer", "goal": "Get signatures"},
        "account_manager": {"role": "Account Manager", "goal": "Retain clients"},
        "business_developer": {"role": "BD Manager", "goal": "Generate opportunities"},
        
        # MARKETING
        "marketer": {"role": "Marketing Strategist", "goal": "Create campaigns"},
        "social_media": {"role": "Social Media Manager", "goal": "Build presence"},
        "content_creator": {"role": "Content Creator", "goal": "Produce content"},
        "seo_specialist": {"role": "SEO Specialist", "goal": "Drive traffic"},
        "email_marketer": {"role": "Email Marketer", "goal": "Nurture leads"},
        "paid_ads": {"role": "PPC Specialist", "goal": "Optimize ads"},
        
        # DESIGN
        "graphic_designer": {"role": "Graphic Designer", "goal": "Create visuals"},
        "ui_designer": {"role": "UI/UX Designer", "goal": "Design interfaces"},
        "web_designer": {"role": "Web Designer", "goal": "Build websites"},
        "brand_designer": {"role": "Brand Designer", "goal": "Build brands"},
        
        # OPERATIONS
        "bookkeeper": {"role": "Bookkeeper", "goal": "Manage finances"},
        "hr_manager": {"role": "HR Manager", "goal": "Manage people"},
        "project_manager": {"role": "Project Manager", "goal": "Deliver projects"},
        "operations_manager": {"role": "Operations Manager", "goal": "Optimize processes"},
        
        # PRODUCT & TECH
        "product_manager": {"role": "Product Manager", "goal": "Define products"},
        "coder": {"role": "Developer", "goal": "Write code"},
        "architect": {"role": "Software Architect", "goal": "Design systems"},
        "devops": {"role": "DevOps Engineer", "goal": "Deploy infrastructure"},
        "data_analyst": {"role": "Data Analyst", "goal": "Analyze metrics"},
        
        # RESEARCH & QUALITY
        "researcher": {"role": "Research Analyst", "goal": "Gather insights"},
        "qualifier": {"role": "Sales Qualifier", "goal": "Score leads"},
        "proposal_writer": {"role": "Proposal Writer", "goal": "Win deals"},
        "tester": {"role": "QA Engineer", "goal": "Ensure quality"},
        
        # SUPPORT
        "customer_success": {"role": "CS Manager", "goal": "Delight customers"},
        "support_agent": {"role": "Support Agent", "goal": "Solve issues"},
        
        # DEFAULT
        "writer": {"role": "Technical Writer", "goal": "Create docs"},
    }
    
    agent = agents.get(agent_type, {"role": agent_type, "goal": "Complete task"})
    prompt = f"You are {agent['role']}. Goal: {agent['goal']}\n\nTASK: {task}\n\n"
    if context:
        prompt += f"CONTEXT: {json.dumps(context)}\n"
    prompt += "Provide thorough, actionable output. Make real decisions."

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 4000},
                timeout=60.0
            )
            result = response.json()
            if "error" in result:
                return {"success": False, "error": result.get("error", {}).get("message", "API error")}
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"success": True, "agent": agent_type, "output": content}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ========================
# COMPREHENSIVE PIPELINE
# ========================

async def run_full_pipeline(lead_id: str) -> Dict:
    """Complete business pipeline"""
    leads = supabase("GET", f"romy_leads?id=eq.{lead_id}")
    if not leads:
        return {"error": "Lead not found"}
    
    lead = leads[0]
    company = lead.get("company", "Unknown")
    email = lead.get("email", "")
    state = PipelineState(lead_id)
    
    # Step 1: Research
    r1 = await run_agent("researcher", f"Deep research on {company}. Include: company overview, team, tech stack, competitors, market position, recent news, pain points, decision makers.")
    state.add_step("researcher", company, r1.get("output", ""))
    
    # Step 2: Qualify
    r2 = await run_agent("qualifier", f"Qualify lead:\nCompany: {company}\nEmail: {email}\nResearch: {r1.get('output', '')[:1500]}\n\nScore 0-100, determine hot/warm/cold, budget indicator, timeline.")
    state.add_step("qualifier", "qualify", r2.get("output", ""))
    
    # Step 3: Create Proposal if hot
    score = 80 if "hot" in r2.get("output", "").lower() else 50
    if score >= 70:
        r3 = await run_agent("proposal_writer", f"Create detailed proposal for {company}\n\nResearch: {r1.get('output', '')[:1000]}\nQualification: {r2.get('output', '')[:1000]}\n\nInclude: Executive Summary, Solution, Timeline, Pricing, Terms, Next Steps")
        state.add_step("proposal_writer", "proposal", r3.get("output", ""))
        supabase("PATCH", f"romy_leads?id=eq.{lead_id}", {
            "status": "proposal",
            "proposal_data": {"proposal": r3.get("output", "")[:5000]},
            "score": score
        })
        supabase("POST", "romy_alerts", {
            "type": "proposal_ready", "title": f"Proposal ready for {company}",
            "message": f"Created proposal. Score: {score}", "lead_id": lead_id, "status": "pending", "priority": "high"
        })
    else:
        supabase("PATCH", f"romy_leads?id=eq.{lead_id}", {"status": "nurture", "score": score})
    
    return {"lead_id": lead_id, "company": company, "steps": state.steps, "decisions": state.decisions}

# ========================
# ALL API ENDPOINTS
# ========================

@app.get("/")
def root():
    return {"message": "🦞 Romy - Complete Business System", "version": "5.0", "status": "operational"}

@app.get("/health")
def health():
    return {"status": "healthy", "groq": "connected" if GROQ_API_KEY else "missing"}

# --- LEADS & DEALS ---

@app.get("/leads")
def list_leads(status: str = ""):
    query = "romy_leads?order=created_at.desc&limit=50"
    if status:
        query = f"romy_leads?status=eq.{status}&order=created_at.desc&limit=50"
    leads = supabase("GET", query)
    return {"leads": leads, "count": len(leads) if isinstance(leads, list) else 0}

@app.post("/leads")
def create_lead(lead: dict):
    result = supabase("POST", "romy_leads", lead)
    return {"lead": result[0] if isinstance(result, list) else result}

@app.get("/leads/{lead_id}")
def get_lead(lead_id: str):
    leads = supabase("GET", f"romy_leads?id=eq.{lead_id}")
    if not leads:
        raise HTTPException(status_code=404, detail="Lead not found")
    return leads[0]

@app.get("/leads/{lead_id}/proposal")
def get_proposal(lead_id: str):
    """Get full proposal for a lead"""
    leads = supabase("GET", f"romy_leads?id=eq.{lead_id}")
    if not leads:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead = leads[0]
    proposal = lead.get("proposal_data", {}).get("proposal", "No proposal generated yet")
    return {"lead_id": lead_id, "company": lead.get("company"), "proposal": proposal}

@app.get("/leads/{lead_id}/research")
def get_research(lead_id: str):
    """Get research data for a lead"""
    leads = supabase("GET", f"romy_leads?id=eq.{lead_id}")
    if not leads:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead = leads[0]
    research = lead.get("research_data", {}).get("research", "No research done yet")
    return {"lead_id": lead_id, "company": lead.get("company"), "research": research}

# --- PIPELINE & TRACKING ---

@app.get("/pipeline")
def get_pipeline():
    leads = supabase("GET", "romy_leads?order=created_at.desc&limit=50")
    alerts = supabase("GET", "romy_alerts?status=eq.pending&limit=10")
    pipeline_runs = supabase("GET", "romy_pipeline_runs?order=created_at.desc&limit=10")
    
    if isinstance(leads, list):
        return {
            "leads": {"total": len(leads), "by_status": {s: len([l for l in leads if l.get("status") == s]) for s in ["new", "researched", "qualified", "outreach_ready", "proposal", "nurture", "archived"]}},
            "alerts": len(alerts) if isinstance(alerts, list) else 0,
            "recent_runs": len(pipeline_runs) if isinstance(pipeline_runs, list) else 0
        }
    return {"leads": {"total": 0}, "alerts": 0}

@app.post("/pipeline/run/{lead_id}")
async def run_pipeline_endpoint(lead_id: str):
    """Run full pipeline on lead"""
    result = await run_full_pipeline(lead_id)
    return result

@app.get("/pipeline/tracking")
def track_all():
    """Track all deals and their status"""
    leads = supabase("GET", "romy_leads?order=created_at.desc&limit=50")
    tracking = []
    if isinstance(leads, list):
        for lead in leads:
            tracking.append({
                "id": lead.get("id"),
                "company": lead.get("company"),
                "contact": lead.get("name"),
                "email": lead.get("email"),
                "status": lead.get("status"),
                "score": lead.get("score", 0),
                "has_research": bool(lead.get("research_data", {}).get("research")),
                "has_proposal": bool(lead.get("proposal_data", {}).get("proposal")),
                "created": lead.get("created_at")
            })
    return {"tracking": tracking, "total": len(tracking)}

# --- AGENTS - ALL BUSINESS FUNCTIONS ---

@app.post("/execute")
async def execute_agent(agent_type: str, task: str):
    """Execute any business agent"""
    result = await run_agent(agent_type, task)
    return result

@app.get("/agents")
def list_agents():
    """List all available agents"""
    agents = [
        {"name": "sales", "category": "Sales", "description": "Close deals"},
        {"name": "closer", "category": "Sales", "description": "Get signatures"},
        {"name": "business_developer", "category": "Sales", "description": "Generate opportunities"},
        {"name": "marketer", "category": "Marketing", "description": "Create campaigns"},
        {"name": "social_media", "category": "Marketing", "description": "Build online presence"},
        {"name": "content_creator", "category": "Marketing", "description": "Produce content"},
        {"name": "seo_specialist", "category": "Marketing", "description": "Drive organic traffic"},
        {"name": "email_marketer", "category": "Marketing", "description": "Nurture leads"},
        {"name": "paid_ads", "category": "Marketing", "description": "Manage ads"},
        {"name": "graphic_designer", "category": "Design", "description": "Create visuals"},
        {"name": "ui_designer", "category": "Design", "description": "Design interfaces"},
        {"name": "web_designer", "category": "Design", "description": "Build websites"},
        {"name": "brand_designer", "category": "Design", "description": "Build brands"},
        {"name": "bookkeeper", "category": "Finance", "description": "Manage finances"},
        {"name": "hr_manager", "category": "Operations", "description": "Manage people"},
        {"name": "project_manager", "category": "Operations", "description": "Deliver projects"},
        {"name": "product_manager", "category": "Product", "description": "Define products"},
        {"name": "coder", "category": "Tech", "description": "Write code"},
        {"name": "architect", "category": "Tech", "description": "Design systems"},
        {"name": "devops", "category": "Tech", "description": "Deploy infrastructure"},
        {"name": "researcher", "category": "Research", "description": "Gather insights"},
        {"name": "qualifier", "category": "Sales", "description": "Score leads"},
        {"name": "proposal_writer", "category": "Sales", "description": "Win deals"},
        {"name": "customer_success", "category": "Support", "description": "Delight customers"},
    ]
    return {"agents": agents, "count": len(agents)}

# --- ALERTS & NOTIFICATIONS ---

@app.get("/alerts")
def list_alerts(status: str = "pending"):
    alerts = supabase("GET", f"romy_alerts?status=eq.{status}&order=created_at.desc&limit=20")
    return {"alerts": alerts, "count": len(alerts) if isinstance(alerts, list) else 0}

@app.post("/alerts/{alert_id}/acknowledge")
def ack_alert(alert_id: str):
    supabase("PATCH", f"romy_alerts?id=eq.{alert_id}", {"status": "acknowledged"})
    return {"alert_id": alert_id, "status": "acknowledged"}

# --- TASKS ---

@app.get("/tasks")
def list_tasks():
    tasks = supabase("GET", "romy_task_queue?order=created_at.desc&limit=50")
    return {"tasks": tasks}

# --- LOGS ---

@app.get("/logs")
def list_logs(limit: int = 50):
    logs = supabase("GET", f"romy_agent_logs?order=created_at.desc&limit={limit}")
    return {"logs": logs}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)