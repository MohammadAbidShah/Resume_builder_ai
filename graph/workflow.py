"""LangGraph workflow definition for Resume Builder."""
from langgraph.graph import StateGraph, END
from graph.state import ResumeState
from graph.nodes import (
    node_generate_content,
  node_validate_content,
    node_generate_latex,
    node_validate_ats,
    node_validate_pdf,
    node_evaluate_and_decide,
    node_selective_regeneration,
    node_save_iteration,
    node_finalize,
)
from graph.edges import should_continue_iteration, route_to_next_iteration
from config.settings import GROQ_MOCK_MODE
from utils.logger import logger

def build_workflow():
    """
    Build the LangGraph workflow for resume generation.
    
    Graph Structure:
    
    START
      ↓
    [generate_content] ← ┐
      ↓                    │
    [validate_content]    │
      ↓                    │
    [generate_latex]      │ continue
      ↓                    │
    [validate_ats] ───┐   │
      ↓               ├→[evaluate] → should_continue_iteration
    [validate_pdf] ──┘   │
      ↓ (parallel)       │
    [save_iteration] ────┴─→ finalize
      ↓                        │
    [finalize] ───────────────┴──→ END
    """
    
    # Create workflow
    workflow = StateGraph(ResumeState)
    
    # Add nodes
    workflow.add_node("generate_content", node_generate_content)
    workflow.add_node("validate_content", node_validate_content)
    workflow.add_node("generate_latex", node_generate_latex)
    workflow.add_node("validate_ats", node_validate_ats)
    workflow.add_node("validate_pdf", node_validate_pdf)
    workflow.add_node("evaluate", node_evaluate_and_decide)
    workflow.add_node("selective_regeneration", node_selective_regeneration)
    workflow.add_node("save_iteration", node_save_iteration)
    workflow.add_node("finalize", node_finalize)
    
    # Set entry point
    workflow.set_entry_point("generate_content")
    
    # Add edges - Main workflow sequence
    workflow.add_edge("generate_content", "validate_content")
    workflow.add_edge("validate_content", "generate_latex")
    
    # Parallel validation nodes (both run after LaTeX generation)
    workflow.add_edge("generate_latex", "validate_ats")
    workflow.add_edge("generate_latex", "validate_pdf")
    
    # Both validations converge to evaluation
    workflow.add_edge("validate_ats", "evaluate")
    workflow.add_edge("validate_pdf", "evaluate")
    
    # Decision point - should we continue or finalize?
    workflow.add_edge("evaluate", "save_iteration")

    # FIX-2: Router enforcement - feedback failure ONLY routes to selective regeneration
    # In mock mode we route straight to finalize to avoid long-running loops
    # during offline deterministic testing. In live mode, use conditional iteration logic.
    if GROQ_MOCK_MODE:
      workflow.add_edge("save_iteration", "finalize")
    else:
      # Conditional edge from save_iteration with FIX-2 enforcement
      workflow.add_conditional_edges(
        "save_iteration",
        should_continue_iteration,
        {
          "continue": "selective_regeneration",  # FIX-2: ONLY selective regeneration on failure
          "finalize": "finalize",                 # Move to finalize on pass
        }
      )
    
    # FIX-3: Selective regeneration routes to LaTeX generation (skip content generation)
    workflow.add_edge("selective_regeneration", "generate_latex")
    
    # Final edge
    workflow.add_edge("finalize", END)
    
    logger.info("LangGraph workflow built successfully")
    return workflow.compile()

# Create the compiled graph
app = build_workflow()

__all__ = ["app", "build_workflow"]
