# Phase 52 Deferred Items

## Pre-existing test failures (not caused by Phase 52 changes)

These failures existed before Phase 52 execution and are out of scope for this plan:

- test_code_checker.py: TestDisallowedImports::test_disallowed_plotly_express
- test_code_checker.py: TestDisallowedImports::test_disallowed_plotly_graph_objects
- test_graph_visualization.py: TestVizResponseNode::test_viz_response_success
- test_graph_visualization.py: TestVizResponseNode::test_viz_response_failure
- test_llm_providers.py: TestHealthEndpoint::test_health_llm_endpoint_exists
- test_pulse_agent.py: Multiple failures (pipeline partial, generate signals, end-to-end)
- test_pulse_service.py: TestCreditPrecheck, TestCreditDeduction, TestActiveRunConflict, TestPipelineRefund, TestPipelinePersists, TestPipelineStatus
- test_routing.py: TestRoutingConfig::test_manager_uses_specified_model
- test_user_classes_workspace.py: test_max_active_collections_correct_values

All confirmed pre-existing by running test suite before any Phase 52 code changes.
