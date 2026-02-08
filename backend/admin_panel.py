"""
Admin Panel for Formula Management
Simple web interface for managing formulas
"""

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from backend.app import Formula, get_db, FormulaCreate, FormulaResponse
from backend.formula_engine import FormulaEngine
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="backend/templates")


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = get_db()):
    """Admin dashboard"""
    formulas = db.query(Formula).all()
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "formulas": formulas
    })


@app.get("/admin/formulas", response_class=HTMLResponse)
async def list_formulas(request: Request, db: Session = get_db()):
    """List all formulas"""
    formulas = db.query(Formula).order_by(Formula.created_at.desc()).all()
    return templates.TemplateResponse("formulas_list.html", {
        "request": request,
        "formulas": formulas
    })


@app.get("/admin/formulas/new", response_class=HTMLResponse)
async def new_formula_form(request: Request):
    """New formula form"""
    return templates.TemplateResponse("formula_form.html", {
        "request": request,
        "formula": None,
        "formula_types": ["rpm", "revenue", "custom", "irpm"]
    })


@app.get("/admin/formulas/{formula_id}/edit", response_class=HTMLResponse)
async def edit_formula_form(request: Request, formula_id: int, db: Session = get_db()):
    """Edit formula form"""
    formula = db.query(Formula).filter(Formula.id == formula_id).first()
    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    return templates.TemplateResponse("formula_form.html", {
        "request": request,
        "formula": formula,
        "formula_types": ["rpm", "revenue", "custom", "irpm"]
    })


@app.post("/admin/formulas")
async def create_formula(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    formula_expression: str = Form(...),
    formula_type: str = Form(...),
    is_active: bool = Form(True),
    db: Session = get_db()
):
    """Create new formula"""
    formula = Formula(
        name=name,
        description=description,
        formula_expression=formula_expression,
        formula_type=formula_type,
        is_active=is_active
    )
    db.add(formula)
    db.commit()
    db.refresh(formula)
    
    return RedirectResponse(url="/admin/formulas", status_code=303)


@app.post("/admin/formulas/{formula_id}")
async def update_formula(
    request: Request,
    formula_id: int,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    formula_expression: str = Form(...),
    formula_type: str = Form(...),
    is_active: bool = Form(True),
    db: Session = get_db()
):
    """Update existing formula"""
    formula = db.query(Formula).filter(Formula.id == formula_id).first()
    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    formula.name = name
    formula.description = description
    formula.formula_expression = formula_expression
    formula.formula_type = formula_type
    formula.is_active = is_active
    formula.updated_at = datetime.utcnow()
    
    db.commit()
    
    return RedirectResponse(url="/admin/formulas", status_code=303)


@app.post("/admin/formulas/{formula_id}/compute")
async def compute_formula_endpoint(
    request: Request,
    formula_id: int,
    db: Session = get_db()
):
    """Trigger computation for a formula"""
    engine = FormulaEngine(db)
    result = engine.compute_formula(formula_id)
    
    return RedirectResponse(
        url=f"/admin/formulas?computed={formula_id}",
        status_code=303
    )


@app.post("/admin/formulas/{formula_id}/delete")
async def delete_formula_endpoint(
    request: Request,
    formula_id: int,
    db: Session = get_db()
):
    """Delete (deactivate) formula"""
    formula = db.query(Formula).filter(Formula.id == formula_id).first()
    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    formula.is_active = False
    db.commit()
    
    return RedirectResponse(url="/admin/formulas", status_code=303)
