"""Conditional edges for LangGraph workflow."""
from typing import Literal
from graph.state import ResumeState
from config.settings import MAX_ITERATIONS, GROQ_MOCK_MODE
from utils.logger import logger

def should_continue_iteration(state: ResumeState) -> Literal["continue", "finalize"]:
    """
    Determine if we should iterate again or finalize.
    
    Conditions for PASS (finalize):
    1. All quality standards met
    
    Conditions for CONTINUE (iterate):
    1. Status is FAIL
    2. Iteration count < MAX_ITERATIONS
    3. No errors occurred
    
    Conditions for FINALIZE (regardless of status):
    1. Hit maximum iterations
    2. Unrecoverable error occurred
    """
    
    # Check for errors
    if state.content_generation_error or state.latex_generation_error:
        logger.warning("Error encountered - finalizing")
        return "finalize"

    # In mock mode, avoid long-running iteration loops by finalizing after
    # the first iteration to keep offline testing bounded and deterministic.
    if GROQ_MOCK_MODE and state.iteration >= 1:
        logger.info("Mock mode: finalizing after one iteration to avoid loop")
        return "finalize"
    
    # Check status
    if state.overall_status == "pass":
        logger.info("[OK] ALL STANDARDS MET - FINALIZING")
        return "finalize"
    
    # Check iteration limit BEFORE incrementing
    if state.iteration >= state.max_iterations - 1:
        logger.warning(f"Max iterations ({state.max_iterations}) reached - finalizing")
        return "finalize"
    
    # Increment iteration counter for next iteration
    state.iteration += 1
    logger.info(f"Standards not met - continuing to iteration {state.iteration + 1}")
    return "continue"

def route_to_next_iteration(state: ResumeState) -> Literal["generate_content", "__end__"]:
    """
    Route back to content generation for next iteration or end.
    This is called when should_continue_iteration returns "continue".
    """
    
    # Increment iteration counter
    state.iteration += 1
    
    logger.info(f"\n{'='*60}")
    logger.info(f"STARTING ITERATION {state.iteration + 1}")
    logger.info(f"{'='*60}\n")
    
    return "generate_content"

__all__ = [
    "should_continue_iteration",
    "route_to_next_iteration",
]
