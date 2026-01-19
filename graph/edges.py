"""Conditional edges for LangGraph workflow."""
from typing import Literal
from graph.state import ResumeState
from config.settings import MAX_ITERATIONS, GROQ_MOCK_MODE
from utils.logger import logger

def should_continue_iteration(state: ResumeState) -> Literal["continue", "finalize"]:
    """
    Determine if we should iterate again or finalize.
    
    FIX-1: Increment iteration FIRST, then enforce MAX_ITERATIONS = 2
    FIX-6: Never loop on feedback failure
    FIX-7: Always end in deterministic state
    """
    
    # FIX-1: Increment iteration counter FIRST
    state.iteration += 1
    logger.info(f"Incremented to iteration {state.iteration}")
    
    # FIX-1: Check hard iteration cap IMMEDIATELY after increment
    if state.iteration >= state.max_iterations:
        logger.warning(f"HARD ITERATION CAP REACHED: {state.iteration} >= {state.max_iterations}")
        # FIX-4: Enter read-only feedback mode
        state.feedback_mode = "read_only"
        # FIX-7: Mark for deterministic exit
        state.should_finalize = True
        if not state.finalization_state:
            state.finalization_state = "FINALIZED_FAIL_WITH_WARNINGS"
        return "finalize"
    
    # Check for blocking errors
    if state.content_generation_error or state.latex_generation_error:
        logger.warning("Error encountered - finalizing")
        state.should_finalize = True
        state.finalization_state = "FINALIZED_FAIL_WITH_WARNINGS"
        return "finalize"

    # In mock mode, avoid long-running iteration loops
    if GROQ_MOCK_MODE and state.iteration >= 1:
        logger.info("Mock mode: finalizing after one iteration")
        state.should_finalize = True
        if not state.finalization_state:
            state.finalization_state = "FINALIZED_FAIL_WITH_WARNINGS"
        return "finalize"
    
    # FIX-5: Check BLOCKING standards only (not warnings)
    if state.blocking_standards_met:
        logger.info("[OK] ALL BLOCKING STANDARDS MET - FINALIZING")
        state.finalization_state = "FINALIZED_PASS"
        state.should_finalize = True
        return "finalize"
    
    # FIX-6: Feedback failures don't cause loops - just continue to next iteration
    logger.info(f"Standards not met - continuing to iteration {state.iteration}")
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
