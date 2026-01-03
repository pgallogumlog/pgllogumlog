"""
Testing Context - Compass Test Runner Orchestrator.

This module handles the execution of Compass AI Readiness test cases.

Public API:
    - CompassTestOrchestrator: Main orchestrator for running Compass tests
    - CompassTestResult: Result from a single Compass test
    - CompassTestSuiteResult: Aggregate results from a test suite
    - CompassTestCase: Definition of a Compass test case
"""

from contexts.testing.compass_orchestrator import (
    CompassTestOrchestrator,
    CompassTestResult,
    CompassTestSuiteResult,
)
from contexts.testing.compass_test_cases import CompassTestCase, get_compass_test_cases

__all__ = [
    "CompassTestOrchestrator",
    "CompassTestResult",
    "CompassTestSuiteResult",
    "CompassTestCase",
    "get_compass_test_cases",
]
