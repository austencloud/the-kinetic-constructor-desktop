# Browse Tab v2 Performance Stress Test Suite

A comprehensive automated stress test suite for systematically identifying and fixing performance bottlenecks in the Browse Tab v2 implementation.

## Overview

This test suite addresses the remaining performance optimization targets after successfully eliminating the critical scroll performance cascade:

- **Widget Creation Speed**: Target <50ms (currently 60-130ms)
- **Navigation Responsiveness**: Target <100ms (currently 118-119ms)  
- **Thumbnail Interaction Speed**: Target <200ms (currently 491ms)
- **Scroll Performance**: Maintain 0ms frame drops (achieved)

## Quick Start

### Run All Tests
```bash
python stress_test_suite.py --all
```

### Run Specific Test Categories
```bash
# Widget creation performance
python run_performance_tests.py widget-speed

# Navigation responsiveness
python run_performance_tests.py navigation-speed

# Thumbnail interaction speed
python run_performance_tests.py thumbnail-speed

# Scroll regression testing
python run_performance_tests.py scroll-stability

# Memory and resource testing
python run_performance_tests.py memory-check

# Quick validation check
python run_performance_tests.py quick-check
```

### Custom Test Execution
```bash
# Run specific combinations
python stress_test_suite.py --widget-creation --navigation --thumbnails

# Enable verbose logging
python stress_test_suite.py --all --verbose

# Custom output directory
python stress_test_suite.py --all --output-dir ./my_results

# Quick mode (reduced iterations)
python stress_test_suite.py --all --quick
```

## Test Categories

### 1. Widget Creation Performance Testing
**Target: <50ms per widget**

- **Simple Sequences**: 2-3 beats, baseline widget creation
- **Complex Sequences**: 8+ beats, stress test widget complexity
- **Cache Variations**: Cold vs warm cache performance comparison
- **Memory Pressure**: Widget creation under simulated low memory
- **Batch Creation**: Different batch sizes (1-10 widgets)
- **Progressive Creation**: Background widget creation simulation

### 2. Navigation Performance Testing
**Target: <100ms per navigation**

- **Basic Navigation**: Section button click response times
- **Rapid-Fire Navigation**: 10 clicks within 2 seconds stress test
- **Concurrent Navigation**: Navigation during background widget creation
- **Sequence Count Variations**: Performance with different section densities
- **Edge Cases**: Empty sections, navigation during scroll operations

### 3. Thumbnail Interaction Testing
**Target: <200ms per interaction**

- **Basic Clicks**: Thumbnail to sequence viewer display time
- **Complexity Variations**: Simple vs medium vs complex sequences
- **Cache State Testing**: Cold vs warm cache impact
- **Viewer State Variations**: Empty vs populated viewer performance
- **Sequence Viewer Performance**: Initialization and update timing

### 4. Scroll Regression Testing
**Target: Maintain 0ms frame drops**

- **Continuous Scroll**: 30+ second scroll simulation
- **Concurrent Scroll**: Scroll during widget creation and navigation
- **Viewport Updates**: Direct viewport update performance measurement
- **Frame Drop Detection**: Identify any scroll events >33ms (30fps minimum)

### 5. Memory and Resource Stress Testing

- **Low Memory Conditions**: Performance under memory pressure
- **Scale Testing**: 1000+ sequence datasets
- **Image Cache Stress**: Cache capacity and hit/miss performance
- **Memory Leak Detection**: Extended session memory growth monitoring
- **Resource Monitoring**: CPU and memory usage during operations

### 6. Multi-Action Stress Testing

- **Concurrent Actions**: Simultaneous scroll + navigation + thumbnail clicks
- **Session Endurance**: 30+ minute continuous usage simulation
- **Workflow Simulation**: Realistic usage pattern testing
- **Performance Baseline**: Establish and compare performance baselines

## Output and Reporting

### Generated Files

Each test run produces three output files:

1. **JSON Results** (`stress_test_results_YYYYMMDD_HHMMSS.json`)
   - Machine-readable detailed test data
   - Suitable for CI/CD integration and automated analysis

2. **Human-Readable Report** (`stress_test_report_YYYYMMDD_HHMMSS.txt`)
   - Comprehensive performance analysis
   - Category breakdowns and optimization recommendations

3. **CSV Data** (`stress_test_data_YYYYMMDD_HHMMSS.csv`)
   - Raw performance metrics for spreadsheet analysis
   - Timing data, memory usage, and test details

### Report Sections

- **Overall Results**: Pass/fail summary and success rates
- **Category Breakdown**: Performance statistics by test category
- **Target Analysis**: Success rates for specific performance targets
- **Optimization Recommendations**: Actionable improvement suggestions
- **Detailed Metrics**: Individual test timing and resource usage

## Performance Targets and Success Criteria

| Metric | Current Performance | Target | Success Criteria |
|--------|-------------------|---------|------------------|
| Widget Creation | 60-130ms | <50ms | 80% of tests pass |
| Navigation Response | 118-119ms | <100ms | 90% of tests pass |
| Thumbnail Interaction | 491ms | <200ms | 75% of tests pass |
| Scroll Frame Drops | 0ms (achieved) | 0ms | 100% of tests pass |
| Memory Growth | Variable | <100MB/session | No memory leaks detected |

## Integration with Existing Performance Monitoring

The stress test suite integrates with the existing performance monitoring infrastructure:

- Uses `QElapsedTimer` for precise timing measurements
- Monitors `psutil` for memory and CPU usage tracking
- Leverages existing performance logging patterns
- Maintains compatibility with current debugging tools

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure browse tab v2 modules are in Python path
2. **Qt Application Conflicts**: Only one QApplication instance allowed
3. **Memory Pressure**: Large memory tests may impact system performance
4. **Test Duration**: Full suite can take 30+ minutes to complete

### Performance Debugging

Use verbose mode for detailed performance analysis:
```bash
python stress_test_suite.py --all --verbose
```

Monitor real-time performance during test execution:
```bash
# In separate terminal
tail -f test_results/stress_test_*.log
```

## Configuration

Test parameters can be customized in `test_config.json`:

- Performance targets and thresholds
- Test iteration counts and durations
- Memory pressure simulation settings
- Output format preferences
- Integration module paths

## Contributing

When adding new performance tests:

1. Follow the existing test method naming convention (`_test_*`)
2. Use the `PerformanceMonitor` context manager for timing
3. Include appropriate target performance thresholds
4. Add comprehensive logging and error handling
5. Update the configuration file with new parameters

## CI/CD Integration

The test suite supports automated execution in CI/CD pipelines:

- Returns appropriate exit codes (0 = success, 1 = failures, 130 = interrupted)
- Generates machine-readable JSON output
- Supports quick mode for faster validation
- Provides clear pass/fail criteria for automated decision making

Example CI integration:
```bash
# Quick validation in PR checks
python stress_test_suite.py --quick --widget-creation --navigation

# Full performance regression testing in nightly builds
python stress_test_suite.py --all --output-dir ./ci_results
```
